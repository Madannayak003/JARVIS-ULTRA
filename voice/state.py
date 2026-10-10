"""
JARVIS PRO
Voice Session State

Each AI response gets its own speech session.

This prevents an old response from becoming active again
when a new response starts.
"""

import threading
from dataclasses import dataclass
from time import time


@dataclass
class SpeechSession:

    session_id: int

    cancel_event: threading.Event

    created_at: float


_lock = threading.Lock()

_current_session = None

_session_counter = 0


# * =========================================================
# * Create New Session
# * =========================================================

def create_session():

    global _current_session
    global _session_counter

    with _lock:

        # * Cancel previous session first.
        if _current_session is not None:

            _current_session.cancel_event.set()

        _session_counter += 1

        session = SpeechSession(

            session_id=_session_counter,

            cancel_event=threading.Event(),

            created_at=time(),

        )

        _current_session = session

        return session


# * =========================================================
# * Get Current Session
# * =========================================================

def current_session():

    with _lock:

        return _current_session


# * =========================================================
# * Cancel Current Session
# * =========================================================

def cancel_current():

    with _lock:

        if _current_session is not None:

            _current_session.cancel_event.set()

            return _current_session

    return None


# * =========================================================
# * Check Current
# * =========================================================

def is_current(session):

    with _lock:

        return (

            _current_session is session

            and not session.cancel_event.is_set()

        )


# * =========================================================
# * Cancelled Check
# * =========================================================

def is_cancelled(session):

    if session is None:

        return True

    return session.cancel_event.is_set()


# * =========================================================
# * Legacy Compatibility
# * =========================================================

# * Keep this so older modules importing STOP_EVENT
# ! don't immediately break.
#
# * New voice code should NOT use this event.

STOP_EVENT = threading.Event()