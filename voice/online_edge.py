import asyncio
import threading
import edge_tts

from pathlib import Path
from uuid import uuid4
from time import time

from voice.player import play
from core.diagnostics import debug_print

from voice.state import (
    is_cancelled,
    is_current,
)

CACHE = Path(__file__).parent / "cache"

CACHE.mkdir(
    exist_ok=True
)

VOICE = "en-GB-RyanNeural"
KANNADA_VOICE = "kn-IN-GaganNeural"
HINDI_VOICE = "hi-IN-MadhurNeural"

ENGLISH_VOICES = {
    "Ryan": "en-GB-RyanNeural",
    "Thomas": "en-GB-ThomasNeural",
    "Connor": "en-IE-ConnorNeural",
    "William": "en-AU-WilliamNeural",
    "Guy": "en-US-GuyNeural",
    "Aria": "en-US-AriaNeural",
    "Jenny": "en-US-JennyNeural",
    "Prabhat": "en-IN-PrabhatNeural",
    "Neerja": "en-IN-NeerjaNeural",
}

CACHE_MAX_AGE = 24 * 60 * 60


# * =========================================================
# * Select Voice
# * =========================================================

def _get_voice(text):

    if not text:
        return VOICE

    # * Kannada Unicode block: U+0C80 - U+0CFF
    if any(
        "\u0C80" <= character <= "\u0CFF"
        for character in text
    ):
        return KANNADA_VOICE

    # * Hindi / Devanagari Unicode block: U+0900 - U+097F
    if any(
        "\u0900" <= character <= "\u097F"
        for character in text
    ):
        return HINDI_VOICE

    return VOICE

# * =========================================================
# * English Voice Selection
# * =========================================================

def set_english_voice(voice_name):
    global VOICE

    voice_name = str(
        voice_name or ""
    ).strip()

    voice_id = ENGLISH_VOICES.get(
        voice_name
    )

    if not voice_id:
        return False

    VOICE = voice_id

    debug_print(
        "[EDGE TTS] English voice:",
        voice_name
    )

    return True


def get_english_voice():
    for name, voice_id in ENGLISH_VOICES.items():

        if voice_id == VOICE:
            return name

    return "Ryan"

# * =========================================================
# * Cache Cleanup
# * =========================================================

def _cleanup_cache():

    now = time()
    removed = 0

    try:

        for file in CACHE.glob("*.mp3"):

            try:

                age = (
                    now
                    - file.stat().st_mtime
                )

                if age > CACHE_MAX_AGE:

                    file.unlink()

                    removed += 1

            except FileNotFoundError:

                pass

            except Exception as e:

                print(
                    "[EDGE TTS ERROR] Could not remove stale speech cache:"
                    f" {e}"
                )

        if removed:

            debug_print(
                "[EDGE TTS CACHE] "
                f"Removed {removed} "
                "stale audio file(s)"
            )

    except Exception as e:

        print(
            "[EDGE TTS CACHE] "
            f"Cleanup error: {e}"
        )


_cleanup_cache()


# * =========================================================
# * Delete Audio File
# * =========================================================

def _delete_file(file):

    try:

        path = Path(file)

        if path.exists():

            path.unlink()

            debug_print(
                "[EDGE TTS CACHE] Deleted:",
                path.name
            )

    except FileNotFoundError:

        pass

    except Exception as e:

        print(
            "[EDGE TTS ERROR] Could not delete generated speech:"
            f" {e}"
        )


# * =========================================================
# * Generate Speech
# * =========================================================

async def _generate(
    text,
    outfile,
):

    voice = _get_voice(text)

    communicate = edge_tts.Communicate(

        text=text,

        voice=voice,

    )

    await communicate.save(
        outfile
    )


# * =========================================================
# * Generate Audio File
#
# ! IMPORTANT:
#
# * This function ONLY generates.
# * It does NOT play.
#
# * This allows the next sentence to be prepared
# * while the previous sentence is playing.
# * =========================================================
# * =========================================================
# * Generate Audio Only
#
# * Does NOT play the audio.
# * =========================================================

def generate_audio(
    text,
    session,
):

    if not text:

        return None

    if (
        is_cancelled(session)
        or not is_current(session)
    ):

        return None

    outfile = (
        CACHE
        / f"{uuid4().hex}.mp3"
    )

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    try:

        debug_print(
            "[EDGE TTS] Preparing:",
            outfile.name
        )

        loop.run_until_complete(

            _generate(
                text,
                str(outfile),
            )

        )

        # * -------------------------------------------------
        # * Check session again.
        # * -------------------------------------------------

        if (
            is_cancelled(session)
            or not is_current(session)
        ):

            debug_print(
                "[EDGE TTS] "
                "Prepared audio discarded"
            )

            _delete_file(
                outfile
            )

            return None

        return outfile

    except Exception as e:

        print(
            "[EDGE TTS ERROR]",
            e
        )

        _delete_file(
            outfile
        )

        return None

    finally:

        try:

            loop.close()

        except Exception:

            pass


# * =========================================================
# * Play Prepared Audio
# * =========================================================

def play_audio(
    outfile,
    session,
):

    if not outfile:

        return False

    try:

        if (
            is_cancelled(session)
            or not is_current(session)
        ):

            return False

        debug_print(
            "[EDGE TTS] Playing:",
            Path(outfile).name
        )

        return play(
            str(outfile),
            cancel_event=session.cancel_event,
        )

    finally:

        # * -------------------------------------------------
        # * play() has returned.
        #
        # * pygame has unloaded the file.
        #
        # * Safe to delete.
        # * -------------------------------------------------

        _delete_file(
            outfile
        )

def _worker(
    text,
    session,
):

    if (
        is_cancelled(session)
        or not is_current(session)
    ):

        return False

    outfile = generate_audio(
        text,
        session
    )

    if not outfile:

        return False

    return play_audio(
        outfile,
        session
    )


# * =========================================================
# * Public API
# * =========================================================

def speak_online(
    text,
    wait=False,
    session=None,
):

    if not text:

        return False

    if session is None:

        return False

    if (
        is_cancelled(session)
        or not is_current(session)
    ):

        return False

    if wait:

        return _worker(
            text,
            session
        )

    thread = threading.Thread(

        target=_worker,

        args=(
            text,
            session,
        ),

        daemon=True,

        name="EdgeTTS",

    )

    thread.start()

    return True
