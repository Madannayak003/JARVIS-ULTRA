from core.context import get_value, set_value
from core.confirmation import ask


def is_busy():

    return get_value("busy") is True


def start_task(task_name):

    set_value("busy", True)
    set_value("busy_task", task_name)


def finish_task():

    set_value("busy", False)
    set_value("busy_task", None)


def ask_switch(new_command):

    ask(
        "switch_task",
        {
            "new_command": new_command
        }
    )

    return True