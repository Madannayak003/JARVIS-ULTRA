from core.interrupt import interrupt
from config.settings import get_assistant_aliases

INTERRUPTS = {

    "stop",
    
    "stop chart",

    "jarvis stop",

    "cancel",

    "abort",

    "never mind",

    "exit chat",

    "stop chatting",
    
    "stop conversation",
    
    "jarvis stop conversation",

}

def handle_priority(command):

    command = command.lower().strip()

    assistant_interrupts = {
        f"{alias} {suffix}"
        for alias in get_assistant_aliases()
        for suffix in ("stop", "stop conversation")
    }

    if command in INTERRUPTS or command in assistant_interrupts:

        interrupt()

        return True

    return False
