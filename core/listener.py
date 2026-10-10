import threading
from queue import Queue
import speech_recognition as sr
from core.diagnostics import debug_print


# * ============================================================
# * COMMAND QUEUE
# * ============================================================

COMMAND_QUEUE = Queue()


# * ============================================================
# * SPEECH RECOGNIZER
# * ============================================================

recognizer = sr.Recognizer()

recognizer.energy_threshold = 200
recognizer.dynamic_energy_threshold = True

recognizer.pause_threshold = 1.1
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.6

# * ============================================================
# * INTERNAL STATE
# * ============================================================

_pending_text = None
_timer = None

_lock = threading.Lock()

_listener_stop = None

_listener_running = False

_listener_paused = False

_shutdown_requested = False


# * ============================================================
# * DISPATCH RECOGNIZED TEXT
# * ============================================================

def _dispatch():

    global _pending_text

    with _lock:

        if _pending_text:

            if _listener_paused:

                _pending_text = None

                return

            print(
                "You :",
                _pending_text
            )

            COMMAND_QUEUE.put(
                _pending_text.lower()
            )

            _pending_text = None


# * ============================================================
# * GOOGLE SPEECH CALLBACK
# * ============================================================

def _callback(
    recognizer,
    audio,
):

    global _pending_text
    global _timer

    with _lock:

        if (
            _listener_paused
            or _shutdown_requested
        ):

            return

    try:

        text = (
            recognizer
            .recognize_google(
                audio
            )
            .strip()
        )

        if not text:

            return

        with _lock:

            if (
                _listener_paused
                or _shutdown_requested
            ):

                return

            _pending_text = text

            if _timer:

                _timer.cancel()

            _timer = threading.Timer(
                0.4,
                _dispatch,
            )

            _timer.daemon = True

            _timer.start()

    except Exception:

        pass


# * ============================================================
# * START LISTENER
# * ============================================================

def start_listener():

    global _listener_stop
    global _listener_running
    global _listener_paused
    global _shutdown_requested

    with _lock:

        if _listener_running:

            _listener_paused = False

            print(
                "[MIC] Background listener already running"
            )

            return

        _shutdown_requested = False

    mic = sr.Microphone()

    with mic as source:

        recognizer.adjust_for_ambient_noise(
            source,
            duration=1,
        )

    _listener_stop = (
        recognizer.listen_in_background(
            mic,
            _callback,
            phrase_time_limit=30,
        )
    )

    with _lock:

        _listener_running = True

        _listener_paused = False

    print("[BOOT] Microphone    : READY")


# * ============================================================
# * PAUSE LISTENER
# * ============================================================

def pause_listener():

    global _listener_paused
    global _pending_text
    global _timer

    with _lock:

        _listener_paused = True

        _pending_text = None

        if _timer:

            _timer.cancel()

            _timer = None

    print(
        "[MIC] Background listener paused"
    )


# * ============================================================
# * RESUME LISTENER
# * ============================================================

def resume_listener():

    global _listener_paused

    with _lock:

        if not _listener_running:

            print(
                "[MIC] Cannot resume: "
                "listener is not running"
            )

            return False

        _listener_paused = False

    print(
        "[MIC] Background listener resumed"
    )

    return True


# * ============================================================
# * STOP LISTENER
# * ============================================================

def stop_listener():

    global _listener_stop
    global _listener_running
    global _listener_paused
    global _pending_text
    global _timer

    with _lock:

        _listener_paused = True

        _pending_text = None

        if _timer:

            _timer.cancel()

            _timer = None

        stop_function = _listener_stop

        _listener_stop = None

        _listener_running = False

    if stop_function:

        try:

            stop_function(
                wait_for_stop=False
            )

        except Exception:

            try:

                stop_function()

            except Exception:

                pass

    print(
        "[MIC] Background listener stopped"
    )


# * ============================================================
# * REQUEST SHUTDOWN
# * ============================================================

def request_shutdown():

    global _shutdown_requested

    with _lock:

        _shutdown_requested = True

    stop_listener()


# * ============================================================
# * SHUTDOWN STATUS
# * ============================================================

def shutdown_requested():

    with _lock:

        return _shutdown_requested


# * ============================================================
# * LISTENER STATUS
# * ============================================================

def listener_running():

    with _lock:

        return _listener_running


def listener_paused():

    with _lock:

        return _listener_paused


# * ============================================================
# * COMMAND
# * ============================================================

def get_command():

    if COMMAND_QUEUE.empty():

        return None

    return COMMAND_QUEUE.get()
