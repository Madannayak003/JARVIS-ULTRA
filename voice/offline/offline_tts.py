"""
JARVIS PRO
Offline Piper TTS

Completely isolated offline TTS engine.

DO NOT import:
voice.manager
voice.online_edge
voice.player
voice.speech_state
voice.tts_pipeline

This module belongs only to the offline voice system.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from voice.offline.offline_player import play


# * =========================================================
# * Configuration
# * =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PIPER_MODEL = (
    BASE_DIR
    / "models"
    / "en_US-lessac-medium.onnx"
)

# * Number of Piper generation workers.
PIPER_WORKERS = 2

# * Number of sentences to prepare ahead of playback.
# * 2 gives us:
#
# * sentence currently playing
# * +
# * next sentence already preparing
#
PREFETCH = 2


# * =========================================================
# * Piper Check
# * =========================================================

def piper_available():

    try:

        result = subprocess.run(
            [
                "python",
                "-m",
                "piper",
                "--help",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )

        return result.returncode == 0

    except Exception:

        return False


# * =========================================================
# * Model Check
# * =========================================================

def model_available():

    return (
        PIPER_MODEL.exists()
        and PIPER_MODEL.is_file()
    )


# * =========================================================
# * Prepare One Sentence
# * =========================================================

def generate(text):

    if not text:
        return None

    text = str(text).strip()

    if not text:
        return None

    if not model_available():

        print(
            "[OFFLINE TTS] Model not found:",
            PIPER_MODEL
        )

        return None

    try:

        temp = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        temp.close()

        wav_file = Path(temp.name)

        print(
            "[OFFLINE TTS] Preparing:",
            wav_file.name
        )

        process = subprocess.run(

            [
                "python",
                "-m",
                "piper",

                "--model",
                str(PIPER_MODEL),

                "--output_file",
                str(wav_file),
            ],

            input=text,

            text=True,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.PIPE,

            timeout=60,
        )

        if process.returncode != 0:

            print(
                "[OFFLINE TTS] Piper failed."
            )

            if process.stderr:

                print(
                    process.stderr.strip()
                )

            wav_file.unlink(
                missing_ok=True
            )

            return None

        if not wav_file.exists():

            return None

        if wav_file.stat().st_size == 0:

            wav_file.unlink(
                missing_ok=True
            )

            return None

        return wav_file

    except Exception as e:

        print(
            "[OFFLINE TTS ERROR]",
            e
        )

        return None


# * =========================================================
# * Split Text
# * =========================================================

def split_sentences(text):

    if not text:
        return []

    text = str(text).strip()

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


# * =========================================================
# * Prepare Multiple Sentences
#
# * Kept for compatibility.
#
# * This function still prepares all sentences and returns
# * them in the original order.
#
# * The main speak() function below uses the new streaming
# * pipeline instead.
# * =========================================================

def prepare(text):

    sentences = split_sentences(text)

    if not sentences:

        return []

    prepared = [None] * len(sentences)

    print(
        f"[OFFLINE TTS] Preparing "
        f"{len(sentences)} sentences..."
    )

    with ThreadPoolExecutor(
        max_workers=PIPER_WORKERS
    ) as executor:

        futures = {

            executor.submit(
                generate,
                sentence
            ): index

            for index, sentence
            in enumerate(sentences)

        }

        for future in futures:

            index = futures[future]

            try:

                prepared[index] = future.result()

            except Exception as e:

                print(
                    "[OFFLINE TTS] "
                    f"Preparation error {index}:",
                    e
                )

    return prepared


# * =========================================================
# * Play Prepared Sentences
# * =========================================================

def play_prepared(prepared):

    if not prepared:

        return False

    success = True

    for index, wav_file in enumerate(prepared):

        if not wav_file:

            success = False

            continue

        try:

            print(
                f"[OFFLINE TTS] "
                f"Playing sentence {index}"
            )

            result = play(
                wav_file
            )

            if not result:

                success = False

        except Exception as e:

            print(
                "[OFFLINE TTS] "
                f"Playback error {index}:",
                e
            )

            success = False

        finally:

            try:

                wav_file.unlink(
                    missing_ok=True
                )

                print(
                    "[OFFLINE TTS] Deleted:",
                    wav_file.name
                )

            except Exception as e:

                print(
                    "[OFFLINE TTS] "
                    "Cleanup error:",
                    e
                )

    return success


# * =========================================================
# * STREAMING OFFLINE TTS
#
# ! IMPORTANT:
#
# * This is the main improvement.
#
# * Piper prepares only a small number of sentences ahead.
# * Playback starts as soon as the first sentence is ready.
#
# ! We DO NOT wait for the entire response.
# * =========================================================

def speak(text):

    sentences = split_sentences(text)

    if not sentences:

        return False

    print(
        f"[OFFLINE TTS] "
        f"Streaming {len(sentences)} sentences..."
    )

    success = True

    # * -----------------------------------------------------
    # * Executor remains alive for the entire response.
    # * -----------------------------------------------------

    executor = ThreadPoolExecutor(
        max_workers=PIPER_WORKERS
    )

    futures = {}

    try:

        # * -------------------------------------------------
        # * Initial prefetch
        #
        # * Generate only the first 2 sentences.
        # * -------------------------------------------------

        initial_count = min(
            PREFETCH,
            len(sentences)
        )

        for index in range(initial_count):

            futures[index] = executor.submit(
                generate,
                sentences[index]
            )

        # * -------------------------------------------------
        # * Playback in original order
        # * -------------------------------------------------

        for index in range(len(sentences)):

            # * ---------------------------------------------
            # * Make sure this sentence has been submitted.
            #
            # * After the initial prefetch, submit one new
            # * sentence as we move forward.
            # * ---------------------------------------------

            if index not in futures:

                futures[index] = executor.submit(
                    generate,
                    sentences[index]
                )

            future = futures[index]

            # * ---------------------------------------------
            # * Wait ONLY for the current sentence.
            #
            # * NOT for the entire response.
            # * ---------------------------------------------

            try:

                wav_file = future.result()

            except Exception as e:

                print(
                    "[OFFLINE TTS] "
                    f"Generation error {index}:",
                    e
                )

                wav_file = None

            # * ---------------------------------------------
            # * Immediately submit another sentence ahead.
            # * ---------------------------------------------

            next_index = index + PREFETCH

            if next_index < len(sentences):

                if next_index not in futures:

                    futures[next_index] = (
                        executor.submit(
                            generate,
                            sentences[next_index]
                        )
                    )

            # * ---------------------------------------------
            # * Play current sentence
            # * ---------------------------------------------

            if not wav_file:

                success = False

                continue

            try:

                print(
                    f"[OFFLINE TTS] "
                    f"Playing sentence {index}"
                )

                result = play(
                    wav_file
                )

                if not result:

                    success = False

            except Exception as e:

                print(
                    "[OFFLINE TTS] "
                    f"Playback error {index}:",
                    e
                )

                success = False

            finally:

                # * -----------------------------------------
                # * Delete after playback.
                # * -----------------------------------------

                try:

                    wav_file.unlink(
                        missing_ok=True
                    )

                    print(
                        "[OFFLINE TTS] Deleted:",
                        wav_file.name
                    )

                except Exception as e:

                    print(
                        "[OFFLINE TTS] "
                        "Cleanup error:",
                        e
                    )

            # * ---------------------------------------------
            # * Remove completed future.
            # * ---------------------------------------------

            futures.pop(
                index,
                None
            )

    finally:

        # * -------------------------------------------------
        # * Cancel anything that hasn't started.
        # * -------------------------------------------------

        for future in futures.values():

            if not future.done():

                future.cancel()

        executor.shutdown(
            wait=True
        )

    return success


# * =========================================================
# * End
# * =========================================================