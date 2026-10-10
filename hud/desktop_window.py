"""
=============================================================
JARVIS PRO — NATIVE DESKTOP HUD WINDOW
=============================================================

Native Windows window for the existing Next.js HUD.

The native window opens immediately.

Next.js HUD loading happens in the background.

Closing this window requests a full JARVIS shutdown.
"""

from __future__ import annotations

import os
import sys
import time
import threading
import urllib.request
import shutil
from pathlib import Path

import webview
from config.settings import get_assistant_display_name
from core.diagnostics import debug_print
from core.paths import CAPTURES, GENERATED_IMAGES, RECORDINGS, SCREENSHOTS


HUD_URL = "http://127.0.0.1:3000"


WINDOW_TITLE = get_assistant_display_name()

WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 750

SHUTDOWN_URL = (
    "http://127.0.0.1:8766/shutdown"
)

# * =============================================================
# * GLOBAL NATIVE WINDOW
# * =============================================================

_native_window = None


class _WindowApi:

    def save_gallery_file(self, category: str, filename: str):
        directories = {
            "screenshots": (SCREENSHOTS, {".png", ".jpg", ".jpeg", ".webp", ".gif"}),
            "captures": (CAPTURES, {".png", ".jpg", ".jpeg", ".webp", ".gif"}),
            "generated_images": (GENERATED_IMAGES, {".png", ".jpg", ".jpeg", ".webp", ".gif"}),
            "recordings": (RECORDINGS, {".mp4", ".webm", ".mkv", ".avi", ".mov", ".wav", ".mp3", ".m4a", ".ogg"}),
        }
        entry = directories.get(category)
        if not entry or Path(filename).name != filename:
            return {"ok": False, "cancelled": False, "error": "Invalid Gallery file."}
        source_root, extensions = entry
        source = (source_root / filename).resolve()
        try:
            source.relative_to(source_root.resolve())
        except ValueError:
            return {"ok": False, "cancelled": False, "error": "Invalid Gallery file."}
        if not source.is_file() or source.suffix.lower() not in extensions:
            return {"ok": False, "cancelled": False, "error": "Gallery file not found."}
        try:
            target = _native_window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=str(source_root),
                save_filename=source.name,
                file_types=(f"{source.suffix.upper().lstrip('.')} files (*{source.suffix})", "All files (*.*)"),
            )
            if not target:
                return {"ok": True, "cancelled": True}
            destination = Path(target[0] if isinstance(target, (list, tuple)) else target)
            shutil.copy2(source, destination)
            return {"ok": True, "cancelled": False, "filename": destination.name}
        except Exception as error:
            print(f"[DESKTOP HUD] Gallery save failed: {error}")
            return {"ok": False, "cancelled": False, "error": "Could not save Gallery file."}

    def toggle_fullscreen(self):

        window = _native_window

        if window is None:

            print(
                "[DESKTOP HUD] "
                "Native fullscreen unavailable: window is not ready."
            )

            return False

        try:

            window.toggle_fullscreen()

            return True

        except Exception as error:

            print(
                "[DESKTOP HUD] "
                "Could not toggle native fullscreen:"
            )

            print(
                f"[DESKTOP HUD] {error}"
            )

            return False


# * =============================================================
# * INITIAL LOADING SCREEN
# * =============================================================

LOADING_HTML = """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>__ASSISTANT_DISPLAY_NAME__</title>

<style>

html,
body {

    margin: 0;

    width: 100%;
    height: 100%;

    background:  # * 050505;

    color:  # * f5a400;

    font-family:
        "Courier New",
        monospace;

    overflow: hidden;

}

.loading {

    width: 100%;
    height: 100%;

    display: flex;

    align-items: center;
    justify-content: center;

    flex-direction: column;

}

.title {

    font-size: 32px;

    letter-spacing: 8px;

    margin-bottom: 20px;

}

.status {

    font-size: 13px;

    letter-spacing: 3px;

    opacity: 0.75;

}

.dot {

    display: inline-block;

    animation:
        blink 1s infinite;

}

@keyframes blink {

    0% {
        opacity: 0.2;
    }

    50% {
        opacity: 1;
    }

    100% {
        opacity: 0.2;
    }

}

</style>

</head>


<body>

<div class="loading">

    <div class="title">
        __ASSISTANT_DISPLAY_NAME__
    </div>

    <div class="status">

        INITIALIZING
        <span class="dot">...</span>

    </div>

</div>

</body>

</html>
"""


# * =============================================================
# * HUD READINESS CHECK
# * =============================================================

def wait_for_hud(
    timeout: float = 30.0,
) -> bool:

    debug_print(
        "[DESKTOP HUD] "
        "Waiting for Next.js HUD..."
    )

    start = time.time()

    while (
        time.time() - start
        < timeout
    ):

        try:

            with urllib.request.urlopen(
                HUD_URL,
                timeout=1,
            ):

                debug_print(
                    "[DESKTOP HUD] "
                    "Next.js HUD is ready."
                )

                return True

        except Exception:

            time.sleep(
                0.25
            )

    print(
        "[DESKTOP HUD] ERROR: "
        "Next.js HUD did not start."
    )

    return False


# * =============================================================
# * LOAD NEXT.JS IN BACKGROUND
# * =============================================================

def _load_nextjs_when_ready(
    window,
    stop_event,
):

    if stop_event.is_set():

        return

    ready = wait_for_hud()

    if stop_event.is_set():

        return

    if not ready:

        debug_print(
            "[DESKTOP HUD] "
            "Keeping loading screen because "
            "Next.js HUD is unavailable."
        )

        return

    try:

        debug_print(
            "[DESKTOP HUD] "
            "Loading Next.js HUD into native window..."
        )

        window.load_url(
            HUD_URL
        )

        debug_print(
            "[DESKTOP HUD] "
            "Next.js HUD loaded into native window."
        )

    except Exception as error:

        print(
            "[DESKTOP HUD] "
            "Could not load Next.js HUD:"
        )

        print(
            f"[DESKTOP HUD] {error}"
        )


# * =============================================================
# * SHUTDOWN
# * =============================================================

def request_jarvis_shutdown():

    print(
        "[DESKTOP HUD] Window closed."
    )

    debug_print(
        "[DESKTOP HUD] "
        f"Requesting {get_assistant_display_name()} shutdown..."
    )

    try:

        request = urllib.request.Request(
            SHUTDOWN_URL,
            method="POST",
        )

        urllib.request.urlopen(
            request,
            timeout=1,
        )

        print(
            "[DESKTOP HUD] "
            f"{get_assistant_display_name()} shutdown requested."
        )

    except Exception as error:

        print(
            "[DESKTOP HUD] "
            "Could not request shutdown:"
        )

        print(
            f"[DESKTOP HUD] {error}"
        )

# * =============================================================
# * CLOSE NATIVE WINDOW
# * =============================================================

def close_native_window():

    global _native_window

    window = _native_window

    if window is None:
        return

    try:

        print(
            "[DESKTOP HUD] "
            f"Closing native {get_assistant_display_name()} window..."
        )

        window.destroy()

    except Exception as error:

        print(
            "[DESKTOP HUD] "
            "Could not close native window:"
        )

        print(
            f"[DESKTOP HUD] {error}"
        )

# * =============================================================
# * NATIVE WINDOW
# * =============================================================

def run():
    
    global _native_window

    # * ---------------------------------------------------------
    # * Stop signal for the background Next.js loader.
    # * ---------------------------------------------------------

    stop_event = threading.Event()


    # * =========================================================
    # * CREATE NATIVE WINDOW IMMEDIATELY
    #
    # ! IMPORTANT:
    #
    # ! Do NOT wait for Next.js before creating this window.
    # * =========================================================

    debug_print(
        "[DESKTOP HUD] "
        f"Creating native {get_assistant_display_name()} window..."
    )


    _native_window = webview.create_window(

        WINDOW_TITLE,

        html=LOADING_HTML.replace(
            "__ASSISTANT_DISPLAY_NAME__",
            get_assistant_display_name(),
        ),

        js_api=_WindowApi(),

        width=WINDOW_WIDTH,

        height=WINDOW_HEIGHT,

        min_size=(
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
        ),

        resizable=True,

        text_select=False,

        zoomable=False,

    )
    
    window = _native_window


    # * =========================================================
    # * WINDOW CLOSED
    # * =========================================================

    window.events.closed += (
        request_jarvis_shutdown
    )


    debug_print(
        "[DESKTOP HUD] "
        f"Native {get_assistant_display_name()} window created."
    )


    # * =========================================================
    # * NEXT.JS LOADER
    #
    # * Runs independently while pywebview is running.
    # * =========================================================

    loader_thread = threading.Thread(

        target=_load_nextjs_when_ready,

        args=(
            window,
            stop_event,
        ),

        name="JARVIS-HUD-Loader",

        daemon=True,

    )

    loader_thread.start()


    debug_print(
        "[DESKTOP HUD] "
        "Starting pywebview..."
    )


    # * =========================================================
    # ! IMPORTANT
    #
    # * pywebview stays on the MAIN THREAD.
    # * =========================================================

    try:

        webview.start(
            debug=False,
            private_mode=False,
        )

    finally:

        stop_event.set()
        
        _native_window = None


    print(
        "[DESKTOP HUD] "
        "Desktop HUD closed."
    )

    return 0


# * =============================================================
# * ENTRY POINT
# * =============================================================

if __name__ == "__main__":

    sys.exit(
        run()
    )
