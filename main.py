"""
# * ============================================================
# * ! JARVIS PRO — MAIN APPLICATION ENTRY POINT
# * ============================================================

# * * Single-application desktop architecture.

# * ! JARVIS:
# * * Runs the existing Python voice engine
# * * Runs the existing HUD bridge
# * * Starts Next.js silently
# * * Displays the HUD through native pywebview
# * * Does NOT open the HUD in a normal browser
# * ! Closing the native HUD shuts down JARVIS

# ! ! IMPORTANT:
# ! ! pywebview.start() MUST run on the MAIN THREAD.

"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

# * Load local configuration before importing application components.
import config  # * noqa: F401
from config.settings import get_assistant_display_name
from core.diagnostics import debug_print

# * * =============================================================
# * ! JARVIS CORE
# * * =============================================================

from skills.loader import load_all
from ai.memory import init_memory
from core.services import start_all, stop_all
from core.core_state import mark_core_ready
from core.core_state import wait_for_core

from hud.integration import HUDIntegration
from hud.runtime import hud_runtime
from hud.web_bridge import hud_web

from dashboard.server import DashboardServer

# * =============================================================
# * GLOBAL STATE
# * =============================================================

_web_hud_process = None
_voice_thread = None
_shutdown_event = threading.Event()
_shutdown_lock = threading.Lock()
_shutdown_started = False

# * =============================================================
# * PATHS
# * =============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
WEB_HUD_DIRECTORY = PROJECT_ROOT / "hud" / "web"
WEB_HUD_URL = "http://127.0.0.1:3000"


# * =============================================================
# * START NEXT.JS HUD
# * =============================================================

def start_web_hud() -> bool:
    global _web_hud_process

    if _web_hud_process is not None and _web_hud_process.poll() is None:
        debug_print("[MAIN HUD] Next.js HUD already running.")
        return True

    package_json = WEB_HUD_DIRECTORY / "package.json"

    if not package_json.is_file():
        print("[MAIN HUD] ERROR: HUD package.json not found.")
        print(f"[MAIN HUD] {package_json}")
        return False

    npm_command = "npm.cmd" if os.name == "nt" else "npm"

    log_directory = PROJECT_ROOT / "data" / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    web_log_path = log_directory / "hud_web.log"

    try:
        web_log = open(web_log_path, "a", encoding="utf-8", buffering=1)
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        debug_print("[MAIN HUD] Starting Next.js HUD...")

        _web_hud_process = subprocess.Popen(
            [npm_command, "run", "dev"],
            cwd=str(WEB_HUD_DIRECTORY),
            stdin=subprocess.DEVNULL,
            stdout=web_log,
            stderr=web_log,
            creationflags=creation_flags,
        )

        debug_print("[MAIN HUD] Next.js HUD started.")
        debug_print("[MAIN HUD] HUD URL:", WEB_HUD_URL)
        debug_print(f"[MAIN HUD] Web logs: {web_log_path}")
        return True

    except FileNotFoundError:
        print("[MAIN HUD] ERROR: npm was not found.")
        return False
    except Exception as error:
        print(f"[MAIN HUD] Failed to start Next.js HUD: {error}")
        return False


# * =============================================================
# * WAIT FOR NEXT.JS
# * =============================================================

def wait_for_web_hud(timeout: float = 30.0) -> bool:
    import urllib.request

    debug_print("[MAIN HUD] Waiting for Next.js HUD...")
    started = time.time()

    while time.time() - started < timeout:
        if _shutdown_event.is_set():
            return False

        try:
            with urllib.request.urlopen(WEB_HUD_URL, timeout=1):
                debug_print("[MAIN HUD] Next.js HUD is ready.")
                return True
        except Exception:
            time.sleep(0.25)

    print("[MAIN HUD] ERROR: Next.js HUD did not become ready.")
    return False


# * =============================================================
# * VOICE ENGINE
# * =============================================================

def run_voice_engine():
    try:
        debug_print("[MAIN] Voice engine waiting for core...")
        wait_for_core()

        if _shutdown_event.is_set():
            return

        debug_print("[MAIN] Core ready. Starting voice engine...")
        from voice.agent import start_agent

        debug_print(
            f"[MAIN] Gemini Live {get_assistant_display_name()} voice engine starting."
        )
        start_agent()

        # start_agent() launches the Live agent on its own worker thread and
        # returns once that worker has been started.  Keep this lifecycle
        # thread alive until the application receives an explicit shutdown;
        # otherwise the finally block would interpret a successful, non-
        # blocking start as an engine exit and shut down the whole app.
        _shutdown_event.wait()

    except Exception as error:
        print(f"[MAIN] Voice engine stopped: {error}")
        if not _shutdown_event.is_set():
            request_jarvis_shutdown()


def start_voice_engine():
    global _voice_thread

    _voice_thread = threading.Thread(
        target=run_voice_engine,
        name="jarvis-voice-engine",
        daemon=True,
    )
    _voice_thread.start()
    debug_print("[MAIN] Voice engine thread started.")


# * =============================================================
# * SHUTDOWN
# * =============================================================

def request_jarvis_shutdown():
    global _shutdown_started

    with _shutdown_lock:
        if _shutdown_started:
            return
        _shutdown_started = True

    print()
    print(
        f"[MAIN] Complete {get_assistant_display_name()} shutdown requested."
    )
    _shutdown_event.set()

    # * 1. Stop microphone listener
    try:
        from core.listener import request_shutdown
        request_shutdown()
    except Exception as error:
        print(f"[MAIN] Listener shutdown error: {error}")

    # Stop the primary Gemini Live Agent explicitly.  A Live connection error
    # is surfaced by the Agent; it is never replaced by a hidden fallback runtime.
    try:
        from voice.agent import stop_agent
        stop_agent()
    except Exception as error:
        print(f"[MAIN] Gemini Live shutdown error: {error}")

    # * 2. Close native pywebview HUD
    try:
        from hud.desktop_window import close_native_window
        close_native_window()
    except Exception as error:
        print(f"[MAIN HUD] Native window shutdown error: {error}")


# * =============================================================
# * HUD SHUTDOWN CALLBACK
# * =============================================================

def configure_hud_shutdown():
    hud_web.set_shutdown_callback(request_jarvis_shutdown)
    debug_print("[MAIN HUD] Desktop shutdown callback registered.")


# * =============================================================
# * START NATIVE HUD
# * =============================================================

def start_native_hud():
    if not wait_for_web_hud():
        return False

    print("[BOOT] HUD           : READY")

    try:
        from dashboard.heartbeat import start_heartbeat
        start_heartbeat()
    except Exception as error:
        print(f"[HEARTBEAT] Startup skipped: {error}")

    print()
    print("=" * 50)
    print(f"{(get_assistant_display_name() + ' READY'):^50}")
    print("=" * 50)

    debug_print(
        f"[MAIN HUD] Opening {get_assistant_display_name()} desktop window..."
    )

    try:
        from hud.desktop_window import run

        # * pywebview requires the MAIN THREAD.
        result = run()
        debug_print(f"[MAIN HUD] Desktop HUD exited: {result}")

        if not _shutdown_event.is_set():
            request_jarvis_shutdown()

        return True

    except Exception as error:
        print(f"[MAIN HUD] Native HUD failed: {error}")
        request_jarvis_shutdown()
        return False


# * =============================================================
# * STOP NEXT.JS (INSTANT PROCESS TREE TERMINATION)
# * =============================================================

def stop_web_hud():
    global _web_hud_process

    process = _web_hud_process
    _web_hud_process = None

    if process is None:
        return

    try:
        if process.poll() is None:
            print("[MAIN HUD] Stopping Next.js HUD...")

            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                process.terminate()

            print("[MAIN HUD] Next.js HUD stopped.")

    except Exception as error:
        print(f"[MAIN HUD] Next.js cleanup error: {error}")


# * =============================================================
# * BACKGROUND CORE INITIALIZATION
# * =============================================================

def initialize_core_background():
    try:
        debug_print("[CORE] Background initialization started.")
        debug_print("[CORE] Loading skills...")
        skill_info = load_all()
        print(f"[BOOT] Skills        : {skill_info['loaded_count']} loaded")

        debug_print("[CORE] Initializing memory...")
        init_memory()

        debug_print("[CORE] Starting services...")
        start_all()
        print("[BOOT] Services      : READY")

        debug_print("[CORE] Background initialization complete.")
        mark_core_ready()
        print("[BOOT] Core          : READY")

    except Exception as error:
        print(f"[CORE] Background initialization failed: {error}")
        raise


# * =============================================================
# * MAIN
# * =============================================================

def main():
    try:
        assistant_name = get_assistant_display_name()
        print("=" * 50)
        print(f"{assistant_name:^50}")
        print("=" * 50)
        print()
        print("[BOOT] Voice Mode    : GEMINI LIVE")
        HUDIntegration.voice_mode("online")
        debug_print("[MAIN HUD] Voice mode sent to HUD: Gemini Live")
        debug_print(
            f"[MAIN] Starting existing online {get_assistant_display_name()}..."
        )

        core_thread = threading.Thread(
            target=initialize_core_background,
            name="jarvis-core-init",
            daemon=True,
        )
        core_thread.start()
        debug_print("[MAIN] Core initialization started in background.")

        hud_runtime.start()
        debug_print("[MAIN HUD] HUD runtime started.")

        if not hud_web.start():
            print("[MAIN HUD] WARNING: HUD bridge failed.")
        else:
            debug_print("[MAIN HUD] Web HUD bridge started.")

        configure_hud_shutdown()

        if not start_web_hud():
            print("[MAIN HUD] Next.js HUD failed to start.")
            return 1

        # Gemini Live is the sole conversational controller.  It starts
        # automatically below; do not expose a second start/stop mode through
        # the dispatcher or HUD.
        print("[BOOT] Gemini Live   : AUTO-START")

        # * Remote dashboard
        from core.dispatcher import dispatch

        remote_server = DashboardServer(
            command_handler=dispatch,
            # Application shutdown is handled by request_jarvis_shutdown;
            # the Live session itself is not user-toggleable.
            agent_stop_handler=None,
        )
        remote_server.new_pairing_pin()

        if remote_server.start():
            print(f"[REMOTE] Address     : {remote_server.url()}")
            print(f"[REMOTE] Pairing PIN : {remote_server._pin}")
            print("[BOOT] Remote        : READY")

        start_voice_engine()

        debug_print(
            f"[MAIN HUD] Starting native {get_assistant_display_name()} HUD..."
        )
        start_native_hud()

        debug_print("[MAIN] Native HUD closed.")
        request_jarvis_shutdown()

        # * Instant check instead of hanging on join
        if _voice_thread is not None and _voice_thread.is_alive():
            _voice_thread.join(timeout=0.5)

        return 0

    except KeyboardInterrupt:
        print("\n[MAIN] Shutdown requested.")
        request_jarvis_shutdown()
        return 0

    finally:
        print(f"[MAIN] Cleaning up {get_assistant_display_name()}...")

        try:
            from core.listener import stop_listener
            stop_listener()
        except Exception:
            pass

        try:
            stop_all()
        except Exception:
            pass

        try:
            hud_web.stop()
        except Exception:
            pass

        stop_web_hud()

        try:
            from dashboard.heartbeat import stop_heartbeat
            stop_heartbeat()
        except Exception as error:
            print(f"[HEARTBEAT] Shutdown skipped: {error}")

        print(f"[MAIN] {get_assistant_display_name()} shutdown complete.")
        # * Instantly releases terminal prompt without socket/thread hanging
        os._exit(0)


# * =============================================================
# * ENTRY POINT
# * =============================================================

if __name__ == "__main__":
    sys.exit(main() or 0)
