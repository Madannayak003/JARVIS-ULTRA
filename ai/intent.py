"""
Compatibility wrapper.

Old dispatcher still imports this file.

Internally it now uses the new
Brain Intent Engine.
"""

from brain.intent_engine import IntentEngine


_engine = IntentEngine()


def detect(command):

    result = _engine.detect(
        command
    )

    # * ------------------------------------------
    # * Developer
    # * ------------------------------------------

    if result.mode == "developer":

        return "developer"

    # * ------------------------------------------
    # * Planner
    # * ------------------------------------------

    if result.mode == "planner":

        return "action"

    # * ------------------------------------------
    # * Chat
    # * ------------------------------------------

    return "chat"