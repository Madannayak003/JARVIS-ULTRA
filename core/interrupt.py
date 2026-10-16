"""
Interrupt Engine

Stops whatever JARVIS is doing.
"""

import time

from voice.player import stop
from voice.manager import stop_speaking
from core.task_manager import task_manager
from core.command_queue import clear

def interrupt(source="unspecified"):

    try:
        from voice.agent import _agent
        live_state = {
            "connected": bool(_agent.connected),
            "running": bool(_agent.running),
            "turn_active": bool(_agent._is_live_turn_active()),
            "speaking": bool(_agent._hud_speaking),
        }
    except Exception:
        live_state = {"connected": False, "running": False}

    print("[INTERRUPT]", "source=", source, "state=", live_state)

    # Live interruption stops only the active response and preserves the
    # persistent session/microphone. Fall back to the legacy global path when
    # Gemini Live is not active.
    try:
        from voice.agent import interrupt_live_response

        if interrupt_live_response():
            clear()
            print("[INTERRUPT COMPLETE] LIVE")
            return True
    except Exception as error:
        print(f"[INTERRUPT] Live interruption unavailable: {error}")

    stop()

    stop_speaking()

    clear()

    task_manager.stop_all()

    # * Stop cancels the active clarification question as well as speech and
    # * tasks. Conversation history and unrelated memory remain untouched.
    try:
        from brain.conversation_coordinator import conversation_coordinator

        conversation_coordinator.cancel_clarification()
    except Exception as error:
        print(f"[INTERRUPT] Clarification reset failed safely: {error}")

    time.sleep(0.1)

    print("[INTERRUPT COMPLETE]")
    return True
