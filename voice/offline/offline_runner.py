"""Offline voice runtime using the shared JARVIS action layer."""

from __future__ import annotations

import time

from hud.adapter import HUDAdapter
from voice.offline.offline_action_bridge import OfflineActionBridge, OfflineRoute
from voice.offline.offline_ai import get_ai
from config.settings import get_assistant_display_name


def process_command(
    text,
    ai=None,
    bridge=None,
    dispatch_result=None,
    emit_command=True,
):
    """Process one already-transcribed command synchronously."""

    text = str(text or "").strip()
    if not text:
        return ""

    bridge = bridge or OfflineActionBridge()
    if emit_command:
        HUDAdapter.command(text)
    started = time.perf_counter()
    result = dispatch_result or bridge.handle(text)
    print(f"[OFFLINE] Input: {text}")
    print(f"[OFFLINE] Route: {result.route.value}")

    if result.route == OfflineRoute.NETWORK_REQUIRED:
        response = result.message
        HUDAdapter.response(response)
        print("[OFFLINE] Result: network unavailable")
        return response

    if result.route == OfflineRoute.LOCAL_ACTION:
        action_names = [step.get("action", "") for step in result.plan]
        success = (not result.plan) or (
            bool(result.results) and all(
                value is not False for value in result.results
            )
        )
        print(f"[OFFLINE] Action: {', '.join(action_names)}")
        print(f"[OFFLINE] Result: {'success' if success else 'failed'}")
        print(f"[OFFLINE] Action latency: {time.perf_counter() - started:.3f}s")
        response = (
            result.message
            or ("Done." if success else "I couldn't complete that local action.")
        )
        HUDAdapter.response(response)
        # * Existing local skills own their spoken result through the shared
        # ! voice manager, so do not speak a second generic acknowledgement.
        return response

    ai = ai or get_ai()
    response = ai.ask(text)
    if not response:
        response = (
            "My local AI is unavailable. Please start Ollama and make sure "
            f"the configured model is installed."
        )
        HUDAdapter.error(response)
    else:
        HUDAdapter.response(response)

    print("[OFFLINE] Result: success" if response else "[OFFLINE] Result: failed")
    return response


def handle_text_command(
    text,
    ai=None,
    bridge=None,
    emit_command=True,
):
    """Handle typed HUD input and voice input through the same path."""

    from voice.offline.offline_tts import speak

    bridge = bridge or OfflineActionBridge()
    result = bridge.handle(text)
    response = process_command(
        text,
        ai=ai,
        bridge=bridge,
        dispatch_result=result,
        emit_command=emit_command,
    )

    # * Local skills already speak their own result through the shared voice
    # * manager. Offline-only responses need Piper here.
    if response and (
        result.route != OfflineRoute.LOCAL_ACTION
        or not result.plan
    ):
        HUDAdapter.speaking()
        speak(response)
        HUDAdapter.idle()

    return response


def run():
    # * Audio dependencies are loaded only when the voice runtime is actually
    # * started, keeping the action bridge usable for tests and other local
    # ! callers that do not need a microphone.
    from voice.offline.offline_stt import calibrate, initialize, listen_once
    from voice.offline.offline_tts import piper_available, speak
    from brain import profile
    from skills.assistant.greetings import speak_startup_greeting

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

    print("[OFFLINE] Runtime initialized")
    print("[OFFLINE] Skills ready")
    ai = get_ai()
    # ! main.py has already selected this runtime mode. Do not probe the
    # * internet again while starting the offline runtime.
    HUDAdapter.voice_mode("offline")
    HUDAdapter.ai_model("ollama", ai.model)
    HUDAdapter.idle()

    stt_ready = initialize()
    if not stt_ready:
        HUDAdapter.error("Faster-Whisper is unavailable in offline mode.")
    piper_ready = piper_available()
    if not piper_ready:
        HUDAdapter.error("Piper is unavailable in offline mode.")

    print("[OFFLINE VOICE] Preparing microphone...")
    mic = calibrate()
    print(f"[OFFLINE] STT {'ready' if stt_ready else 'unavailable'}")
    print(f"[OFFLINE] Piper {'ready' if piper_ready else 'unavailable'}")
    print("[OFFLINE] Action layer ready")
    print(f"[OFFLINE] {get_assistant_display_name()} ready")

    # * Reuse the normal Greeting Engine. Passing offline Piper explicitly
    # * keeps startup independent from Gemini/OpenAI and voice.manager.
    speak_startup_greeting(speaker=speak, profile=profile)

    print("[OFFLINE VOICE] Speak a command.")
    print("[OFFLINE VOICE] Press Ctrl+C to exit.")
    print()

    bridge = OfflineActionBridge()

    try:
        while True:
            HUDAdapter.listening()
            text = listen_once(mic, timeout=None, phrase_time_limit=10)
            if not text:
                HUDAdapter.idle()
                continue

            HUDAdapter.thinking()
            handle_text_command(text, ai=ai, bridge=bridge)

    except KeyboardInterrupt:
        HUDAdapter.idle()
        print("\n[OFFLINE VOICE] Stopped.")


if __name__ == "__main__":
    run()
