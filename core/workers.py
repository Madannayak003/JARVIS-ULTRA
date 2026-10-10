from ai.ai_worker import run_chat
from ai.memory_answer import answer

from voice.manager import speak

from core.context import (
    add_message,
    set_value
)

from core.busy_manager import (
    start_task,
    finish_task
)


def chat_worker(question, stop_event):

    start_task("chat")

    try:

        # * ---------------------------------
        # * Instant Memory Answers
        # * ---------------------------------

        memory_reply = answer(question)

        if memory_reply:

            print("[MEMORY ANSWER]", memory_reply)

            add_message("assistant", memory_reply)

            speak(memory_reply)

            return

        # * ---------------------------------
        # AI Chat
        # * ---------------------------------

        run_chat(question, stop_event)

    finally:

        finish_task()

        set_value("chat_mode", False)

        print("[CHAT] Finished")