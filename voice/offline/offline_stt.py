"""
JARVIS PRO
Offline Speech-to-Text

Completely isolated offline STT.

Uses:
SpeechRecognition -> microphone capture only
Faster-Whisper    -> local transcription

IMPORTANT:
This file NEVER uses:
recognize_google()
online speech APIs
voice.manager
voice.speech_state
core.listener
"""

import time

import numpy as np
import speech_recognition as sr


# * =========================================================
# * Configuration
# * =========================================================

WHISPER_MODEL_NAME = "small"

WHISPER_DEVICE = "cpu"

WHISPER_COMPUTE_TYPE = "int8"

LANGUAGE = "en"

# * ---------------------------------------------------------
# * Audio filtering
# * ---------------------------------------------------------

# * Minimum RMS level considered real microphone speech.
#
# * This prevents silence / very quiet background noise
# * from being sent to Whisper.
MIN_RMS = 0.008

# * Ignore extremely short recordings.
MIN_AUDIO_SECONDS = 0.25

# * ---------------------------------------------------------
# * Whisper quality settings
# * ---------------------------------------------------------

BEAM_SIZE = 5

NO_SPEECH_THRESHOLD = 0.65

LOG_PROB_THRESHOLD = -1.0

COMPRESSION_RATIO_THRESHOLD = 2.4


# * =========================================================
# * Load Faster-Whisper once
# * =========================================================

WHISPER_MODEL = None
_WHISPER_INITIALIZED = False
_WHISPER_ERROR = ""


def initialize():
    """Load Faster-Whisper once and report a clear local error on failure."""

    global WHISPER_MODEL, _WHISPER_INITIALIZED, _WHISPER_ERROR

    if _WHISPER_INITIALIZED:
        return WHISPER_MODEL is not None

    _WHISPER_INITIALIZED = True
    print("[OFFLINE STT] Loading Faster-Whisper...")

    try:
        from faster_whisper import WhisperModel

        WHISPER_MODEL = WhisperModel(
            WHISPER_MODEL_NAME,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )
        print("[OFFLINE STT] Faster-Whisper ready.")
        return True

    except Exception as error:
        _WHISPER_ERROR = str(error)
        print(f"[OFFLINE STT ERROR] Faster-Whisper unavailable: {_WHISPER_ERROR}")
        return False


# * =========================================================
# * Microphone
# * =========================================================

recognizer = sr.Recognizer()

# * Starting threshold.
recognizer.energy_threshold = 300

# * Let SpeechRecognition adapt to room noise.
recognizer.dynamic_energy_threshold = True

# * Shorter than your old 1.5 seconds.
#
# * This makes JARVIS respond more naturally after
# * you finish speaking.
recognizer.pause_threshold = 0.9

# * Detect speech sooner.
recognizer.phrase_threshold = 0.25

# * Keep a short amount of silence around speech.
recognizer.non_speaking_duration = 0.5


# * =========================================================
# * AudioData -> NumPy
# * =========================================================

def _audio_to_array(audio):

    pcm_data = audio.get_raw_data(
        convert_rate=16000,
        convert_width=2,
    )

    audio_array = np.frombuffer(
        pcm_data,
        dtype=np.int16,
    ).astype(
        np.float32
    ) / 32768.0

    return audio_array


# * =========================================================
# * Audio Quality Check
# * =========================================================

def _audio_quality(audio_array):

    if audio_array is None:

        return False

    if len(audio_array) == 0:

        return False

    # * -----------------------------------------------------
    # * Duration
    # * -----------------------------------------------------

    duration = (
        len(audio_array) / 16000.0
    )

    if duration < MIN_AUDIO_SECONDS:

        print(
            "[OFFLINE STT] Audio too short."
        )

        return False

    # * -----------------------------------------------------
    # * RMS volume
    # * -----------------------------------------------------

    rms = float(
        np.sqrt(
            np.mean(
                np.square(
                    audio_array
                )
            )
        )
    )

    print(
        f"[OFFLINE STT] Audio level: "
        f"{rms:.4f}"
    )

    if rms < MIN_RMS:

        print(
            "[OFFLINE STT] "
            "Audio too quiet. Ignoring."
        )

        return False

    return True


# * =========================================================
# * Transcribe Audio
# * =========================================================

def transcribe_audio(audio):

    if audio is None:

        return None

    try:

        if not initialize():
            return None

        # * -------------------------------------------------
        # * Convert microphone audio
        # * -------------------------------------------------

        audio_array = _audio_to_array(
            audio
        )

        # * -------------------------------------------------
        # * Reject silence / extremely short audio
        # * -------------------------------------------------

        if not _audio_quality(
            audio_array
        ):

            return None

        print(
            "[OFFLINE STT] Transcribing..."
        )

        # * -------------------------------------------------
        # * Faster-Whisper
        # * -------------------------------------------------

        transcription_started = time.perf_counter()

        segments, info = (
            WHISPER_MODEL.transcribe(

                audio_array,

                language=LANGUAGE,

                beam_size=BEAM_SIZE,

                vad_filter=True,

                vad_parameters={
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 200,
                },

                # ! Important:
                # ! Don't let previous transcription
                # * influence the next command.
                condition_on_previous_text=False,

                # * Reject likely hallucinations.
                no_speech_threshold=(
                    NO_SPEECH_THRESHOLD
                ),

                log_prob_threshold=(
                    LOG_PROB_THRESHOLD
                ),

                compression_ratio_threshold=(
                    COMPRESSION_RATIO_THRESHOLD
                ),
            )
        )

        # * -------------------------------------------------
        # * Collect segments
        # * -------------------------------------------------

        collected = []

        probabilities = []

        for segment in segments:

            text = segment.text.strip()

            if not text:
                continue

            collected.append(text)

            probabilities.append(
                getattr(
                    segment,
                    "avg_logprob",
                    None
                )
            )

        print(
            "[OFFLINE STT] Transcription latency: "
            f"{time.perf_counter() - transcription_started:.2f}s"
        )

        # * -------------------------------------------------
        # * Nothing recognized
        # * -------------------------------------------------

        if not collected:

            print(
                "[OFFLINE STT] "
                "No speech recognized."
            )

            return None

        text = " ".join(
            collected
        ).strip()

        if not text:

            return None

        # * -------------------------------------------------
        # * Basic hallucination protection
        # * -------------------------------------------------

        if len(text) < 2:

            print(
                "[OFFLINE STT] "
                "Recognition too short."
            )

            return None

        # * -------------------------------------------------
        # * Confidence information
        # * -------------------------------------------------

        valid_probs = [
            p
            for p in probabilities
            if p is not None
        ]

        if valid_probs:

            avg_logprob = (
                sum(valid_probs)
                / len(valid_probs)
            )

            print(
                "[OFFLINE STT] "
                f"Average log probability: "
                f"{avg_logprob:.3f}"
            )

            # * Extremely low-confidence result.
            if avg_logprob < -1.5:

                print(
                    "[OFFLINE STT] "
                    "Low-confidence result. "
                    "Ignoring."
                )

                return None

        # * -------------------------------------------------
        # * Final result
        # * -------------------------------------------------

        print(
            "[OFFLINE STT] Recognized:",
            text
        )

        return text

    except Exception as e:

        print(
            "[OFFLINE STT ERROR]",
            e
        )

        return None


# * =========================================================
# * Calibrate Microphone
# * =========================================================

def calibrate():

    mic = sr.Microphone()

    print(
        "[OFFLINE STT] "
        "Calibrating microphone..."
    )

    with mic as source:

        recognizer.adjust_for_ambient_noise(
            source,
            duration=1.5
        )

    print(
        "[OFFLINE STT] "
        f"Microphone ready. "
        f"Energy threshold: "
        f"{recognizer.energy_threshold:.0f}"
    )

    return mic


# * =========================================================
# * Listen Once
# * =========================================================

def listen_once(
    mic=None,
    timeout=None,
    phrase_time_limit=10,
):

    if mic is None:

        mic = sr.Microphone()

    try:

        with mic as source:

            print(
                "[OFFLINE STT] Listening..."
            )

            audio = recognizer.listen(

                source,

                timeout=timeout,

                phrase_time_limit=(
                    phrase_time_limit
                ),
            )

        return transcribe_audio(
            audio
        )

    except sr.WaitTimeoutError:

        print(
            "[OFFLINE STT] "
            "Listening timeout."
        )

        return None

    except Exception as e:

        print(
            "[OFFLINE STT ERROR]",
            e
        )

        return None
