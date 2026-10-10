import time
import re

from ai.chat import ask_chat
from ai.memory_manager import learn

from core.context import add_message
from core.diagnostics import debug_print
from hud.integration import HUDIntegration

from voice.manager import (
    start_speech_session,
)

from voice.tts_pipeline import (
    TTSPipeline,
)

from voice.speech_text import (
    clean_for_speech_stateful,
)


# * =========================================================
# * Voice Text Cleaner
# * =========================================================

def clean_for_speech(text):
    """Clean one complete text fragment for TTS only."""

    cleaned, _ = clean_for_speech_stateful(text)
    return cleaned


# * =========================================================
# * Run Chat
# * =========================================================

def run_chat(
    question,
    stop_event
):

    print(
        "[AI WORKER] Thinking..."
    )

    # * =====================================================
    # * Memory
    # * =====================================================

    memory_result = learn(
        question
    )

    if memory_result["saved"]:

        debug_print(
            "[MEMORY] Saved -> "
            f"{memory_result['key']} = "
            f"{memory_result['value']}"
        )

    elif memory_result.get(
        "already_known"
    ):

        debug_print(
            "[MEMORY] Already known."
        )

    # * =====================================================
    # * Start AI Request
    # * =====================================================

    t0 = time.perf_counter()

    session = ask_chat(
        question,
        stop_event
    )

    stream = session.stream

    is_developer = (
        session.is_developer
    )

    debug_print(
        "Request sent:",
        time.perf_counter() - t0
    )

    debug_print("[AI] Streaming response...")

    # * =====================================================
    # * Response State
    # * =====================================================

    answer = ""

    sentence_buffer = ""

    # * Fenced code can span several streamed sentence chunks. Carry the state
    # * so code stays visible in the UI/history but is silent by default.
    speech_in_code_block = False

    # * =====================================================
    # * TTS Pipeline
    # * =====================================================

    voice_session = None

    tts_pipeline = None

    if not is_developer:

        # * -------------------------------------------------
        # * Create a NEW voice session for this response.
        # * -------------------------------------------------

        voice_session = (
            start_speech_session()
        )

        # * -------------------------------------------------
        # * Create PRO TTS pipeline.
        #
        # * Sentence generation and playback are now
        # * separated so the next sentence can be prepared
        # * while the current sentence is playing.
        # * -------------------------------------------------

        tts_pipeline = TTSPipeline(

            stop_event=stop_event,

            session=voice_session,

        )

        tts_pipeline.start()

    # * =====================================================
    # * Developer Response Buffer
    # * =====================================================

    developer_answer = ""

    # * =====================================================
    # * Stream AI Response
    # * =====================================================

    try:

        first = True

        for data in stream:

            # * -------------------------------------------------
            # * Task interruption
            # * -------------------------------------------------

            if stop_event.is_set():

                if first:

                    debug_print(
                        "First token:",
                        time.perf_counter()
                        - t0
                    )

                    first = False

                print(
                    "\n[AI WORKER] Interrupted"
                )

                return

            # * -------------------------------------------------
            # * Extract token
            # * -------------------------------------------------

            token = data.get(
                "response",
                ""
            )

            if not token:

                continue

            # * -------------------------------------------------
            # * Terminal output
            # * -------------------------------------------------

            debug_print(
                token,
                end="",
                flush=True
            )

            # * -------------------------------------------------
            # * Store complete answer
            # * -------------------------------------------------

            answer += token

            # * =================================================
            # * Developer Mode
            # * =================================================

            if is_developer:

                developer_answer += token

                continue

            # * =================================================
            # * Normal Chat
            # * =================================================

            sentence_buffer += token

            # * -------------------------------------------------
            # * Extract complete sentences
            #
            # * Decimal-safe:
            #
            # * 1084.80
            # * 2.44%
            #
            # * will not be incorrectly split.
            # * -------------------------------------------------

            while True:

                match = re.search(

                    r"""
                    (?<!\d)
                    [^.!?]+
                    [.!?]+
                    (?=\s|$)
                    """,

                    sentence_buffer,

                    re.VERBOSE

                )

                if not match:

                    break

                # * -------------------------------------------------
                # * Extract sentence
                # * -------------------------------------------------

                sentence = (
                    match.group(0)
                    .strip()
                )

                # * -------------------------------------------------
                # * Remove extracted sentence
                # * -------------------------------------------------

                sentence_buffer = (
                    sentence_buffer[
                        match.end():
                    ]
                )

                # * -------------------------------------------------
                # * Send to TTS pipeline
                # * -------------------------------------------------

                if sentence:

                    cleaned, speech_in_code_block = (
                        clean_for_speech_stateful(
                            sentence,
                            speech_in_code_block,
                        )
                    )

                    if cleaned:

                        tts_pipeline.put(
                            cleaned
                        )

    finally:

        print()

    # * =====================================================
    # * Check Cancellation
    # * =====================================================

    if stop_event.is_set():

        print(
            "[CHAT] Cancelled before TTS"
        )

        return

    if (
        voice_session
        and voice_session.cancel_event.is_set()
    ):

        print(
            "[CHAT] Voice session cancelled"
        )

        return

    if answer.strip():
        # * Publish the untouched completed response as soon as generation
        # * finishes. TTS can continue preparing/playing progressively without
        # * delaying the single coherent HUD/activity entry.
        HUDIntegration.response(answer)
        debug_print("[AI] Response completed.")

    # * =====================================================
    # * Remaining Text
    # * =====================================================

    remaining = (
        sentence_buffer.strip()
    )

    if (
        remaining
        and not is_developer
    ):

        cleaned, speech_in_code_block = (
            clean_for_speech_stateful(
                remaining,
                speech_in_code_block,
            )
        )

        if cleaned:

            tts_pipeline.put(
                cleaned
            )

    # * =====================================================
    # * Finish TTS Pipeline
    # * =====================================================

    if not is_developer:

        # * -------------------------------------------------
        # * Tell pipeline no more sentences are coming.
        # * -------------------------------------------------

        tts_pipeline.finish()

        # * -------------------------------------------------
        # * Wait until:
        #
        # * - remaining TTS is generated
        # * - queued audio is played
        # * - files are cleaned
        #
        # * OR cancellation occurs.
        # * -------------------------------------------------

        tts_pipeline.wait()

    # * =====================================================
    # * Save Conversation
    # * =====================================================

    if not answer.strip():

        return

    add_message(
        "assistant",
        answer
    )
