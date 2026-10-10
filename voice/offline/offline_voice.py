"""
JARVIS PRO
Completely Isolated Offline Voice Mode

Pipeline:

Microphone
    ↓
Faster-Whisper
    ↓
Offline Stage-4 AI
    ↓
Ollama
    ↓
Piper
    ↓
Speaker

IMPORTANT:
This module NEVER imports or uses:
- voice.manager
- voice.online_edge
- voice.speech_state
- core.listener
- Google STT
- Gemini
- OpenAI
- Edge TTS
"""

from voice.offline.offline_stt import (
    calibrate,
    listen_once,
)

from voice.offline.offline_ai import (
    get_ai,
)
from config.settings import get_assistant_display_name

from voice.offline.offline_tts import (
    speak,
)


# * =========================================================
# * Banner
# * =========================================================

def print_banner():

    print()
    print("==========================================")
    print(f"       {get_assistant_display_name()} OFFLINE VOICE MODE")
    print("==========================================")
    print("[OFFLINE VOICE] STT  : Faster-Whisper")
    print("[OFFLINE VOICE] AI   : Ollama")
    print("[OFFLINE VOICE] TTS  : Piper")
    print("[OFFLINE VOICE] NET  : Not required")
    print("==========================================")
    print()


# * =========================================================
# * Main Offline Voice Loop
# * =========================================================

def run():

    print_banner()

    # * -----------------------------------------------------
    # * Load offline AI
    # * -----------------------------------------------------

    print(
        "[OFFLINE VOICE] Initializing AI..."
    )

    ai = get_ai()

    # * -----------------------------------------------------
    # * Calibrate microphone
    # * -----------------------------------------------------

    mic = calibrate()

    print()
    print(
        "[OFFLINE VOICE] Ready."
    )

    print(
        "[OFFLINE VOICE] Speak a command."
    )

    print(
        "[OFFLINE VOICE] Press Ctrl+C to exit."
    )

    print()

    # * =====================================================
    # * Continuous Offline Conversation
    # * =====================================================

    while True:

        try:

            # * -------------------------------------------------
            # * STT
            # * -------------------------------------------------

            text = listen_once(
                mic,
                timeout=None,
                phrase_time_limit=15,
            )

            if not text:

                continue

            text = text.strip()

            if not text:

                continue

            print()
            print(
                "[OFFLINE VOICE] You:",
                text
            )

            # * -------------------------------------------------
            # AI
            # * -------------------------------------------------

            response = ai.ask(
                text
            )

            if not response:

                print(
                    "[OFFLINE VOICE] "
                    "No response from Ollama."
                )

                continue

            print()
            print(
                f"[OFFLINE VOICE] {get_assistant_display_name()}:",
                response
            )

            # * -------------------------------------------------
            # * Piper TTS
            # * -------------------------------------------------

            result = speak(
                response
            )

            if not result:

                print(
                    "[OFFLINE VOICE] "
                    "TTS failed."
                )

            print()

        except KeyboardInterrupt:

            print()
            print(
                "[OFFLINE VOICE] Stopped."
            )

            break

        except Exception as e:

            print(
                "[OFFLINE VOICE ERROR]",
                e
            )


# * =========================================================
# * Entry Point
# * =========================================================

if __name__ == "__main__":

    run()
