"""
=============================================================
JARVIS PRO — LIVE EXECUTION CONTEXT
=============================================================

Global execution state used to identify commands originating
from Gemini Agent.

This is intentionally process-wide because Live commands may
cross worker/thread boundaries.
"""

from __future__ import annotations

import threading
import contextvars
from contextlib import contextmanager


_lock = threading.RLock()

_live_execution_count = 0

_live_responses = []
_live_session = contextvars.ContextVar("jarvis_live_session", default=None)
_live_loop = contextvars.ContextVar("jarvis_live_loop", default=None)
_live_tasks = contextvars.ContextVar("jarvis_live_tasks", default=None)


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
    tasks = _live_tasks.get() or []
    if tasks:
        await __import__("asyncio").gather(*tasks, return_exceptions=True)
        tasks.clear()


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
