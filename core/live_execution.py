"""
=============================================================
JARVIS ULTRA — LIVE EXECUTION CONTEXT
=============================================================

Global execution state used to identify commands originating
from Gemini Agent.

This is intentionally process-wide because Live commands may
cross worker/thread boundaries.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import Future
import threading
import contextvars
import base64
import json
from collections import OrderedDict
from contextlib import contextmanager


_lock = threading.RLock()

_live_execution_count = 0

_live_responses = []
_live_session = contextvars.ContextVar("jarvis_live_session", default=None)
_live_loop = contextvars.ContextVar("jarvis_live_loop", default=None)
_live_tasks = contextvars.ContextVar("jarvis_live_tasks", default=None)
_live_developer_generation = contextvars.ContextVar(
    "jarvis_live_developer_generation",
    default=False,
)


class LiveInvocationDeduplicator:
    """Coalesce repeated Live tool deliveries by stable function-call ID."""

    def __init__(self, max_entries=256):
        self.max_entries = max(1, int(max_entries))
        self._completed = OrderedDict()
        self._inflight = {}
        self._lock = threading.RLock()

    def begin(self, invocation_id):
        """Return ``new``, ``cached``, or ``wait`` plus its associated value."""

        if not invocation_id:
            return "new", None

        with self._lock:
            if invocation_id in self._completed:
                self._completed.move_to_end(invocation_id)
                return "cached", self._completed[invocation_id]
            future = self._inflight.get(invocation_id)
            if future is not None:
                return "wait", future
            future = Future()
            self._inflight[invocation_id] = future
            return "new", None

    def complete(self, invocation_id, response):
        if not invocation_id:
            return
        with self._lock:
            future = self._inflight.pop(invocation_id, None)
            self._completed[invocation_id] = response
            self._completed.move_to_end(invocation_id)
            while len(self._completed) > self.max_entries:
                self._completed.popitem(last=False)
            if future is not None and not future.done():
                future.set_result(response)

    async def wait(self, future, timeout=10.0):
        try:
            return await asyncio.wait_for(
                asyncio.wrap_future(future),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return None


def is_live_developer_generation_allowed() -> bool:
    """Return whether the active Live turn explicitly approved Developer generation."""

    return bool(_live_developer_generation.get())


@contextmanager
def live_developer_generation():
    """Temporarily approve one scoped Developer secondary-generation call."""

    token = _live_developer_generation.set(True)
    try:
        yield
    finally:
        _live_developer_generation.reset(token)


def build_live_function_response(types_module, function_call_id, function_name, result):
    """Build one Live tool response, including correlated screen media."""
    response_parts = None
    response_payload = result
    if isinstance(result, dict):
        image_bytes = result.get("_live_image_bytes")
        image_mime_type = result.get("_live_image_mime_type")
        is_screen_analysis = result.get("action") == "screen_vision_analyze"
        if is_screen_analysis and (not image_bytes or not image_mime_type):
            response_payload = {
                key: value
                for key, value in result.items()
                if not key.startswith("_live_")
            }
            response_payload.update({
                "ok": False,
                "status": "failed",
                "message": "The screen capture did not contain image data, so analysis was not completed.",
            })
        else:
            response_payload = {
                key: value
                for key, value in result.items()
                if not key.startswith("_live_")
            }
            if image_bytes and image_mime_type:
                response_parts = [
                    types_module.FunctionResponsePart.from_bytes(
                        data=image_bytes,
                        mime_type=image_mime_type,
                    )
                ]
    return types_module.FunctionResponse(
        id=function_call_id,
        name=function_name,
        response=response_payload,
        parts=response_parts,
    )


def _live_json_value(value, *, convert_keys=True):
    """Convert Live response values to JSON-safe wire values."""
    if isinstance(value, bytes):
        return base64.urlsafe_b64encode(value).decode("ascii")
    if isinstance(value, bytearray):
        return base64.urlsafe_b64encode(bytes(value)).decode("ascii")
    if hasattr(value, "model_dump"):
        return _live_json_value(
            value.model_dump(exclude_none=True, mode="json", by_alias=True),
            convert_keys=False,
        )
    if isinstance(value, dict):
        return {
            _live_camel_key(key) if convert_keys else key: _live_json_value(
                item,
                convert_keys=False,
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_live_json_value(item, convert_keys=False) for item in value]
    return value


def _live_camel_key(key):
    key = str(key)
    result = []
    uppercase = False
    for char in key:
        if char == "_":
            uppercase = True
        elif uppercase:
            result.append(char.upper())
            uppercase = False
        else:
            result.append(char)
    return "".join(result)


def _contains_live_bytes(value):
    if isinstance(value, (bytes, bytearray)):
        return True
    if hasattr(value, "model_dump"):
        return _contains_live_bytes(value.model_dump(exclude_none=True))
    if isinstance(value, dict):
        return any(_contains_live_bytes(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_live_bytes(item) for item in value)
    return False


def _live_tool_response_payload(function_responses):
    responses = function_responses
    if isinstance(responses, (dict,)) or hasattr(responses, "model_dump"):
        responses = [responses]
    return {
        "tool_response": {
            "functionResponses": [
                _live_json_value(response)
                for response in responses
            ]
        }
    }


async def send_live_tool_response(session, function_responses):
    """Send Live tool responses without exposing media bytes to json.dumps().

    google-genai 2.29.0's public send_tool_response path leaves bytes inside
    FunctionResponse.parts and then calls json.dumps directly. For media
    responses, use the same documented wire shape with base64 inlineData and
    the session's websocket. Ordinary responses keep the SDK path.
    """
    if not _contains_live_bytes(function_responses):
        return await session.send_tool_response(
            function_responses=function_responses
        )

    websocket = getattr(session, "_ws", None)
    if websocket is None or not hasattr(websocket, "send"):
        raise RuntimeError("Gemini Live websocket is unavailable for media response.")

    payload = _live_tool_response_payload(function_responses)
    await websocket.send(json.dumps(payload))


def preserve_live_media(result, source_result):
    """Carry media fields through a text-only compatibility wrapper."""
    if not isinstance(result, dict) or not isinstance(source_result, dict):
        return result
    if source_result.get("action") != "screen_vision_analyze":
        return result
    media = {
        key: source_result[key]
        for key in ("_live_image_bytes", "_live_image_mime_type", "correlation_id")
        if key in source_result
    }
    if media:
        result = dict(result)
        result.setdefault("action", "screen_vision_analyze")
        result.update(media)
    return result


def resolve_live_task_results(initial_result, task_results, action=None):
    """Fold delayed Live task outcomes into a truthful tool result."""
    outcomes = list(task_results or [])
    for outcome in outcomes:
        if outcome is False or isinstance(outcome, BaseException):
            return {"ok": False, "status": "failed", "action": action,
                    "message": "The Live capability failed during asynchronous execution."}
    for outcome in reversed(outcomes):
        if isinstance(outcome, dict):
            result = dict(outcome)
            if action:
                result.setdefault("action", action)
            result.setdefault("ok", result.get("status") not in {"failed", "error"})
            return result
        if isinstance(outcome, str) and outcome.strip():
            return {"ok": True, "status": "reported_success", "action": action, "message": outcome.strip()}
    if any(outcome is True for outcome in outcomes):
        if isinstance(initial_result, dict):
            result = dict(initial_result)
            result.update({"ok": True, "status": "completed"})
            result.setdefault("action", action)
            result["message"] = result.get("message") or "The Live capability completed successfully."
            return result
        return {"ok": True, "status": "completed", "action": action, "message": "The Live capability completed successfully."}
    return initial_result


def is_live_execution() -> bool:
    """
    Return True when JARVIS is currently executing a command
    originating from Gemini Live.
    """

    with _lock:
        return _live_execution_count > 0


def capture_live_response(text: str) -> None:
    """
    Capture authoritative JARVIS speech generated while a
    Live command is executing.

    This does NOT speak anything. It only stores the text so
    Gemini Live can receive the real JARVIS skill result.
    """

    if not text:
        return

    with _lock:

        if _live_execution_count <= 0:
            return

        _live_responses.append(str(text))


def get_live_responses() -> list[str]:
    """
    Return all authoritative responses captured during the
    current Live execution context.
    """

    with _lock:
        return list(_live_responses)


def get_live_session_context():
    """Return the active Live session context for Live-aware skills."""
    return _live_session.get(), _live_loop.get(), _live_tasks.get()


def schedule_live_task(coroutine):
    """Register async work a Live-aware synchronous skill needs completed."""
    tasks = _live_tasks.get()
    loop = _live_loop.get()
    if tasks is None or loop is None:
        try:
            coroutine.close()
        except Exception:
            pass
        return False
    tasks.append(loop.create_task(coroutine))
    return True


async def drain_live_tasks():
    """Wait for Live-scheduled work and return its outcomes.

    Callers must inspect the returned values. A scheduled action can return a
    pending result synchronously and fail later, so discarding task outcomes
    would let Gemini report a false success.
    """
    tasks = _live_tasks.get() or []
    if tasks:
        try:
            return await __import__("asyncio").gather(*tasks, return_exceptions=True)
        finally:
            # Clear completed or cancelled task handles so repeated drains do
            # not replay outcomes or retain coroutine state.
            tasks.clear()
    return []


def clear_live_responses() -> None:
    """
    Clear previously captured Live responses.
    """

    with _lock:
        _live_responses.clear()


@contextmanager
def live_execution(session=None, loop=None):
    global _live_execution_count

    clear_live_responses()

    session_token = _live_session.set(session)
    loop_token = _live_loop.set(loop)
    tasks_token = _live_tasks.set([])
    with _lock:
        _live_execution_count += 1

    try:
        yield
    finally:
        with _lock:
            _live_execution_count = max(
                0,
                _live_execution_count - 1,
            )
        _live_session.reset(session_token)
        _live_loop.reset(loop_token)
        _live_tasks.reset(tasks_token)
