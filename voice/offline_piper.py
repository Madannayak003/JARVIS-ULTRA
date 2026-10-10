"""
JARVIS PRO
Offline Piper TTS

Offline-only speech engine.

Architecture:

    prepare_audio()
          ↓
       WAV cache
          ↓
    play_audio()
          ↓
       delete

This mirrors the Edge TTS architecture so the TTS pipeline
can prepare multiple sentences in parallel.
"""

import subprocess
import tempfile
import sys
from pathlib import Path
from uuid import uuid4

from voice.player import play

from voice.state import (
    is_cancelled,
    is_current,
)


# * =========================================================
# * Configuration
# * =========================================================

CACHE = (
    Path(__file__).parent
    / "cache"
    / "piper"
)

CACHE.mkdir(
    parents=True,
    exist_ok=True
)


PIPER_MODEL = (
    Path(__file__).parent
    / "models"
    / "en_US-lessac-medium.onnx"
)


# * =========================================================
# * Piper Availability
# * =========================================================

_PIPER_READY = None


def _piper_available():

    global _PIPER_READY

    if _PIPER_READY is not None:
        return _PIPER_READY

    try:

        result = subprocess.run(

            [
                sys.executable,
                "-m",
                "piper",
                "--help",
            ],

            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,

            timeout=10,
        )

        _PIPER_READY = (
            result.returncode == 0
        )

    except Exception:

        _PIPER_READY = False

    return _PIPER_READY


# * =========================================================
# * Model Check
# * =========================================================

def _model_available():

    return (
        PIPER_MODEL.exists()
        and PIPER_MODEL.is_file()
    )


# * =========================================================
# * Delete Audio
# * =========================================================

def _delete_file(file):

    if not file:
        return

    try:

        path = Path(file)

        if path.exists():

            path.unlink()

            print(
                "[PIPER OFFLINE] "
                "Deleted:",
                path.name
            )

    except FileNotFoundError:

        pass

    except Exception as e:

        print(
            "[PIPER OFFLINE] "
            "Delete failed:",
            e
        )


# * =========================================================
# * Generate Piper Audio
# * =========================================================

def generate_audio(
    text,
    session,
):

    if not text:
        return None

    if (
        session is None
        or is_cancelled(session)
        or not is_current(session)
    ):

        return None


    # * -----------------------------------------------------
    # * Piper
    # * -----------------------------------------------------

    if not _piper_available():

        print(
            "[PIPER OFFLINE] "
            "Piper is unavailable."
        )

        return None


    # * -----------------------------------------------------
    # * Model
    # * -----------------------------------------------------

    if not _model_available():

        print(
            "[PIPER OFFLINE] "
            "Model not found:",
            PIPER_MODEL
        )

        return None


    # * -----------------------------------------------------
    # * Output file
    # * -----------------------------------------------------

    outfile = (
        CACHE
        / f"{uuid4().hex}.wav"
    )


    try:

        print(
            "[PIPER OFFLINE] Preparing:",
            outfile.name
        )


        # * -------------------------------------------------
        # * Run Piper
        # * -------------------------------------------------

        process = subprocess.run(

            [
                sys.executable,

                "-m",
                "piper",

                "--model",
                str(PIPER_MODEL),

                "--output_file",
                str(outfile),

            ],

            input=str(text),

            text=True,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.PIPE,

            timeout=60,
        )


        # * -------------------------------------------------
        # ! Piper error
        # * -------------------------------------------------

        if process.returncode != 0:

            print(
                "[PIPER OFFLINE] "
                "Generation failed."
            )

            if process.stderr:

                print(
                    "[PIPER OFFLINE]",
                    process.stderr.strip()
                )

            _delete_file(outfile)

            return None


        # * -------------------------------------------------
        # * Session check AFTER generation
        # * -------------------------------------------------

        if (
            is_cancelled(session)
            or not is_current(session)
        ):

            print(
                "[PIPER OFFLINE] "
                "Prepared audio discarded."
            )

            _delete_file(outfile)

            return None


        # * -------------------------------------------------
        # * Validate output
        # * -------------------------------------------------

        if not outfile.exists():

            print(
                "[PIPER OFFLINE] "
                "No WAV generated."
            )

            return None


        if outfile.stat().st_size == 0:

            print(
                "[PIPER OFFLINE] "
                "Empty WAV generated."
            )

            _delete_file(outfile)

            return None


        return outfile


    except subprocess.TimeoutExpired:

        print(
            "[PIPER OFFLINE] "
            "Generation timeout."
        )

        _delete_file(outfile)

        return None


    except Exception as e:

        print(
            "[PIPER OFFLINE ERROR]",
            e
        )

        _delete_file(outfile)

        return None


# * =========================================================
# * Play Prepared Audio
# * =========================================================

def play_audio(
    audio_file,
    session,
):

    if not audio_file:
        return False


    try:

        if (
            session is None
            or is_cancelled(session)
            or not is_current(session)
        ):

            return False


        print(
            "[PIPER OFFLINE] Playing:",
            Path(audio_file).name
        )


        return play(
            str(audio_file),
            cancel_event=session.cancel_event,
        )


    except Exception as e:

        print(
            "[PIPER OFFLINE] "
            "Playback failed:",
            e
        )

        return False


    finally:

        # * -------------------------------------------------
        # * pygame has finished with the WAV.
        # * -------------------------------------------------

        _delete_file(
            audio_file
        )


# * =========================================================
# * Synchronous Convenience API
# * =========================================================

def speak_offline(
    text,
    session=None,
):

    if not text:
        return False


    # * -----------------------------------------------------
    # * A synchronous call still needs a session.
    # * -----------------------------------------------------

    if session is None:

        return False


    audio_file = generate_audio(
        text,
        session,
    )

    if not audio_file:

        return False


    return play_audio(
        audio_file,
        session,
    )