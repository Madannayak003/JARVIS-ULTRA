import threading
import queue
from pathlib import Path

from voice.manager import (
    speak,
    prepare_speech,
    play_prepared_speech,
)

from core.diagnostics import debug_print

from voice.state import (
    is_current,
    is_cancelled,
)

from hud.integration import HUDIntegration


# * =========================================================
# * PRO TTS PIPELINE
#
# AI Stream
# * ↓
# * Sentence Queue
# * ↓
# * Parallel TTS Generation Workers
# * ↓
# * Ordered Audio Buffer
# * ↓
# * Playback Worker
#
# * Example:
#
# * Sentence 1 ──┐
# * Sentence 2 ──┼── generate in parallel
# * Sentence 3 ──┘
# * ↓
# * ordered audio buffer
# * ↓
# * Sentence 1 → play
# * Sentence 2 → play
# * Sentence 3 → play
#
# ! IMPORTANT:
#
# * Generation may happen in parallel.
# * Playback ALWAYS remains sequential.
#
# * =========================================================


# * =========================================================
# * Configuration
# * =========================================================

TTS_WORKERS = 2

SENTENCE_QUEUE_SIZE = 4

AUDIO_QUEUE_SIZE = 3


class TTSPipeline:

    def __init__(
        self,
        stop_event,
        session,
    ):

        self.stop_event = stop_event

        self.session = session

        # * -------------------------------------------------
        # * Incoming sentences
        # * -------------------------------------------------

        self.sentence_queue = queue.Queue(
            maxsize=SENTENCE_QUEUE_SIZE
        )

        # * -------------------------------------------------
        # * Generated audio
        #
        # ! IMPORTANT:
        #
        # * This queue contains ordered items.
        #
        # * Each item:
        #
        # * (
        # * sentence_index,
        # * audio_file,
        # * sentence
        # * )
        #
        # * -------------------------------------------------

        self.audio_queue = queue.Queue(
            maxsize=AUDIO_QUEUE_SIZE
        )

        # * -------------------------------------------------
        # * Generated results waiting for ordered playback
        #
        # * Example:
        #
        # * {
        # * 2: (file2, sentence2),
        # * 0: (file0, sentence0),
        # * 1: (file1, sentence1),
        # * }
        #
        # ! Playback waits for the next required index.
        # * -------------------------------------------------

        self.pending_audio = {}

        self.pending_lock = threading.Lock()

        self.pending_condition = threading.Condition(
            self.pending_lock
        )

        # * -------------------------------------------------
        # * Workers
        # * -------------------------------------------------

        self.prefetch_threads = []

        self.playback_thread = None

        # * -------------------------------------------------
        # * State
        # * -------------------------------------------------

        self.started = False

        self.finished = False
        
        self.hud_speaking = False

        self.worker_done_count = 0

        self.worker_done_lock = threading.Lock()

        # * -------------------------------------------------
        # * Sentence ordering
        # * -------------------------------------------------

        self.next_sentence_index = 0

        self.next_play_index = 0

        self.index_lock = threading.Lock()

        # * -------------------------------------------------
        # * Number of sentences submitted
        # * -------------------------------------------------

        self.total_sentences = 0

        self.total_lock = threading.Lock()

    # * =====================================================
    # * Cancellation
    # * =====================================================

    def cancelled(self):

        return (
            self.stop_event.is_set()
            or self.session.cancel_event.is_set()
            or not is_current(self.session)
            or is_cancelled(self.session)
        )

    # * =====================================================
    # * Start
    # * =====================================================

    def start(self):

        if self.started:

            return

        self.started = True

        debug_print(
            "[TTS PIPELINE] Starting"
        )

        # * -------------------------------------------------
        # * Start parallel TTS generation workers
        # * -------------------------------------------------

        for worker_number in range(
            TTS_WORKERS
        ):

            thread = threading.Thread(

                target=self._prefetch_worker,

                args=(worker_number,),

                daemon=True,

                name=(
                    f"JARVIS-TTS-Prefetch-"
                    f"{worker_number + 1}"
                ),

            )

            self.prefetch_threads.append(
                thread
            )

            thread.start()

        # * -------------------------------------------------
        # * Start ONE playback worker
        #
        # * Only one thread is allowed to control audio
        # * playback.
        # * -------------------------------------------------

        self.playback_thread = threading.Thread(

            target=self._playback_worker,

            daemon=True,

            name="JARVIS-TTS-Playback",

        )

        self.playback_thread.start()

        debug_print(
            "[TTS PIPELINE] Started "
            f"with {TTS_WORKERS} TTS workers"
        )

    # * =====================================================
    # * Add Sentence
    # * =====================================================

    def put(self, sentence):

        if not sentence:

            return False

        if self.cancelled():

            return False

        sentence = sentence.strip()

        if not sentence:

            return False
        
        # * -------------------------------------------------
        # * Assign an ordering index.
        #
        # * This happens BEFORE placing the sentence into
        # * the queue.
        # * -------------------------------------------------

        with self.index_lock:

            sentence_index = (
                self.next_sentence_index
            )

            self.next_sentence_index += 1

        # * -------------------------------------------------
        # * Store indexed sentence.
        # * -------------------------------------------------

        item = (
            sentence_index,
            sentence,
        )

        # * -------------------------------------------------
        # * Back-pressure
        # * -------------------------------------------------

        while not self.cancelled():

            try:

                self.sentence_queue.put(
                    item,
                    timeout=0.05
                )

                with self.total_lock:

                    self.total_sentences += 1

                return True

            except queue.Full:

                continue

        return False

    # * =====================================================
    # * Finish Input
    # * =====================================================

    def finish(self):

        if self.finished:

            return

        self.finished = True

        # * -------------------------------------------------
        # * One sentinel per generation worker.
        #
        # ! Every worker must receive its own sentinel.
        # * -------------------------------------------------

        for _ in range(
            TTS_WORKERS
        ):

            while not self.cancelled():

                try:

                    self.sentence_queue.put(
                        None,
                        timeout=0.05
                    )

                    break

                except queue.Full:

                    continue

    # * =====================================================
    # * Prefetch Worker
    #
    # * Multiple workers generate audio simultaneously.
    # * =====================================================

    def _prefetch_worker(
        self,
        worker_number,
    ):

        worker_name = (
            f"TTS-{worker_number + 1}"
        )

        debug_print(
            f"[TTS PIPELINE] "
            f"{worker_name} started"
        )

        while True:

            if self.cancelled():

                return

            try:

                item = self.sentence_queue.get(
                    timeout=0.05
                )

            except queue.Empty:

                continue

            # * -------------------------------------------------
            # * Worker shutdown
            # * -------------------------------------------------

            if item is None:

                self.sentence_queue.task_done()

                with self.worker_done_lock:

                    self.worker_done_count += 1

                debug_print(
                    f"[TTS PIPELINE] "
                    f"{worker_name} finished"
                )

                return

            sentence_index, sentence = item

            try:

                if self.cancelled():

                    return

                # * -------------------------------------------------
                # * Clean sentence
                # * -------------------------------------------------

                sentence = sentence.strip()

                if not sentence:

                    continue

                debug_print(
                    "[TTS PIPELINE] "
                    f"{worker_name} preparing "
                    f"sentence {sentence_index}"
                )

                # * -------------------------------------------------
                # * Generate audio.
                #
                # ! IMPORTANT:
                #
                # * This only generates.
                #
                # * It does NOT play.
                # * -------------------------------------------------

                audio_file = prepare_speech(

                    sentence,

                    self.session,

                )

                # * -------------------------------------------------
                # * Offline / fallback
                # * -------------------------------------------------

                if audio_file is None:

                    if not self.cancelled():

                        self._store_fallback(
                            sentence_index,
                            sentence,
                        )

                    continue

                # * -------------------------------------------------
                # * Check cancellation after generation.
                # * -------------------------------------------------

                if self.cancelled():

                    self._delete_audio(
                        audio_file
                    )

                    return

                # * -------------------------------------------------
                # * Store generated audio using its index.
                #
                # * It doesn't matter which worker finishes first.
                # * Playback will wait for the correct index.
                # * -------------------------------------------------

                with self.pending_condition:

                    self.pending_audio[
                        sentence_index
                    ] = (
                        audio_file,
                        sentence,
                    )

                    self.pending_condition.notify_all()

            except Exception as e:

                print(
                    "[VOICE ERROR] Speech preparation failed:"
                    f" {e}"
                )

            finally:

                self.sentence_queue.task_done()

    # * =====================================================
    # * Store Fallback
    #
    # * If Edge TTS isn't available, keep the sentence
    # * in the ordered playback system.
    # * =====================================================

    def _store_fallback(
        self,
        sentence_index,
        sentence,
    ):

        with self.pending_condition:

            self.pending_audio[
                sentence_index
            ] = (
                None,
                sentence,
            )

            self.pending_condition.notify_all()

    # * =====================================================
    # * Playback Worker
    #
    # * ONLY this worker controls playback.
    #
    # * Playback order:
    #
    # * 0 → 1 → 2 → 3 ...
    #
    # ! Never based on generation completion order.
    # * =====================================================

    def _playback_worker(self):

        debug_print(
            "[TTS PIPELINE] "
            "Playback worker started"
        )

        try:

            while True:

                if self.cancelled():

                    self._cleanup_pending_audio()

                    return

                # * -------------------------------------------------
                # * Wait for the next sentence's audio.
                # * -------------------------------------------------

                with self.pending_condition:

                    while (

                        self.next_play_index
                        not in self.pending_audio

                        and not self.cancelled()

                    ):

                        if self._generation_finished():

                            self._cleanup_pending_audio()

                            return

                        self.pending_condition.wait(
                            timeout=0.05
                        )

                    if self.cancelled():

                        self._cleanup_pending_audio()

                        return

                    if (
                        self.next_play_index
                        not in self.pending_audio
                    ):

                        continue

                    audio_file, sentence = (
                        self.pending_audio.pop(
                            self.next_play_index
                        )
                    )

                    current_index = (
                        self.next_play_index
                    )

                    self.next_play_index += 1

                # * -------------------------------------------------
                # * HUD — JARVIS has started speaking.
                #
                # * This is intentionally triggered when the
                # * first sentence is actually ready for playback,
                # * not merely when the TTS pipeline starts.
                # * -------------------------------------------------

                if not self.hud_speaking:

                    try:

                        HUDIntegration.speaking()

                        self.hud_speaking = True

                        debug_print("[VOICE] Speaking response.")

                    except Exception as e:

                        print(
                            "[HUD] Speaking event failed:",
                            e
                        )

                # * -------------------------------------------------
                # * Play prepared audio.
                # * -------------------------------------------------

                try:

                    if self.cancelled():

                        if audio_file:

                            self._delete_audio(
                                audio_file
                            )

                        return

                    debug_print(
                        "[TTS PIPELINE] "
                        f"Playing sentence "
                        f"{current_index}"
                    )

                    # * -------------------------------------------------
                    # * Edge TTS prepared audio
                    # * -------------------------------------------------

                    if audio_file:

                        play_prepared_speech(

                            audio_file,

                            self.session,

                        )

                    # * -------------------------------------------------
                    # * Offline / fallback
                    # * -------------------------------------------------

                    else:

                        self._play_fallback(
                            sentence
                        )

                except Exception as e:

                    print(
                        "[TTS PLAYBACK ERROR]",
                        e
                    )

                    if audio_file:

                        self._delete_audio(
                            audio_file
                        )

        finally:

            # * -------------------------------------------------
            # * Entire TTS playback is finished.
            #
            # * This executes even when:
            #
            # * - playback completes normally
            # * - user interrupts
            # * - session is cancelled
            # ! - an error occurs
            # * -------------------------------------------------

            if self.hud_speaking:

                try:

                    HUDIntegration.idle()

                except Exception as e:

                    print(
                        "[HUD] Idle event failed:",
                        e
                    )

                self.hud_speaking = False

    # * =====================================================
    # * Generation Finished
    # * =====================================================

    def _generation_finished(self):

        with self.worker_done_lock:

            workers_finished = (
                self.worker_done_count
                >= TTS_WORKERS
            )

        with self.total_lock:

            total = self.total_sentences

        return (
            workers_finished
            and self.next_play_index
            >= total
        )

    # * =====================================================
    # * Offline / Fallback
    # * =====================================================

    def _play_fallback(
        self,
        sentence,
    ):

        if self.cancelled():

            return

        try:

            debug_print(
                "[TTS PIPELINE] "
                "Using fallback speech"
            )

            speak(

                sentence,

                wait=True,

                session=self.session,

                notify_remote=False,

                record_conversation=False,

            )

        except Exception as e:

            print(
                "[TTS FALLBACK ERROR]",
                e
            )

    # * =====================================================
    # * Wait
    # * =====================================================

    def wait(self):

        # * -------------------------------------------------
        # * Wait for generation workers.
        # * -------------------------------------------------

        for thread in self.prefetch_threads:

            if thread:

                thread.join()

        # * -------------------------------------------------
        # * Wake playback worker after generation is done.
        # * -------------------------------------------------

        with self.pending_condition:

            self.pending_condition.notify_all()

        # * -------------------------------------------------
        # * Wait for playback.
        # * -------------------------------------------------

        if self.playback_thread:

            self.playback_thread.join()

        # * -------------------------------------------------
        # * Final cleanup.
        # * -------------------------------------------------

        self._cleanup_pending_audio()

        # * -------------------------------------------------
        # * HUD — complete speech state.
        #
        # * This happens only after ALL generated sentences
        # * have finished playing.
        # * -------------------------------------------------

        try:

            HUDIntegration.idle()

        except Exception as e:

            print(
                "[TTS PIPELINE] "
                f"HUD idle update failed: {e}"
            )

        debug_print(
            "[TTS PIPELINE] Finished"
        )
        
    # * =====================================================
    # * Delete Audio
    # * =====================================================

    def _delete_audio(
        self,
        audio_file,
    ):

        if not audio_file:

            return

        try:

            path = Path(
                audio_file
            )

            if path.exists():

                path.unlink()

                debug_print(
                    "[TTS PIPELINE] "
                    f"Deleted: {path.name}"
                )

        except FileNotFoundError:

            pass

        except Exception as e:

            print(
                "[VOICE ERROR] Could not clean up generated speech:"
                f" {e}"
            )

    # * =====================================================
    # * Cleanup Pending Audio
    #
    # * Called when:
    #
    # * - user interrupts
    # * - session becomes invalid
    # * - pipeline finishes
    # * =====================================================

    def _cleanup_pending_audio(self):

        with self.pending_condition:

            items = list(
                self.pending_audio.values()
            )

            self.pending_audio.clear()

            self.pending_condition.notify_all()

        for audio_file, _ in items:

            if audio_file:

                self._delete_audio(
                    audio_file
                )
