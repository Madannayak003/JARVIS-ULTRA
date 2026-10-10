from voice.manager import speak
from core.registry import register
from core.action_memory import set_memory
from brain.conversation_coordinator import conversation_coordinator


def ai_clarify(data):

    question = data.get(
        "question",
        "Can you please clarify?"
    )
    
    context = data.get("context") or {}

    # * A clarification is conversational state, not a confirmation. Keeping it
    # * in the coordinator makes the next user turn available to the existing
    # * clarification/follow-up flow before normal routing begins.
    original_request = (
        data.get("original_request")
        or context.get("original_request")
        or context.get("subject")
        or data.get("task")
    )

    field = (
        data.get("field")
        or context.get("field")
        or "clarification"
    )

    conversation_coordinator.start_clarification(
        field=field,
        question=question,
        task=original_request,
        owner=data.get("owner") or "planner",
        metadata=context,
    )

    # ! Retire the legacy, hard-coded clarification interceptor. It must not
    # * override the generic coordinator path on the reply turn.
    set_memory("clarify_context", None)

    speak(question)

    return True


register("clarify", ai_clarify)
