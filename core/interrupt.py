"""
Interrupt Engine

Stops whatever JARVIS is doing.
"""

import time

from voice.player import stop
from voice.manager import stop_speaking
from core.task_manager import task_manager
from core.command_queue import clear

def interrupt():

    print("[INTERRUPT]")

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
