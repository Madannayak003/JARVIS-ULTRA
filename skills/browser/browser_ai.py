from core.registry import register
from voice.manager import speak
from skills.browser.navigation import navigation
from core.action_memory import set_memory
from core.diagnostics import debug_print
from core.action_memory import dump
from skills.browser.browser_controller import browser

from core.live_execution import is_live_execution

from core.browser_context import browser_context

import os

SITES = {

    "chrome": "https://www.google.com",

    "google": "https://www.google.com",

    "youtube": "https://www.youtube.com",

    "gmail": "https://mail.google.com",

    "github": "https://github.com",

    "spotify": "https://open.spotify.com",

    "chatgpt": "https://chat.openai.com",

}


WINDOWS_APPS = {

    "notepad": "notepad",

    "calculator": "calc",

    "calc": "calc",

    "paint": "mspaint",

    "cmd": "cmd",

    "command prompt": "cmd",

    "powershell": "powershell",

    "explorer": "explorer",
    
    "file explorer": "explorer",

    "task manager": "taskmgr",

    "registry editor": "regedit",

    "device manager": "devmgmt.msc",

    "control panel": "control",

    "settings": "ms-settings:",

}


def ai_open(data):

    app = data.get("app", "").lower()

    # * ---------- Websites ----------

    if app in SITES:

        if not is_live_execution():
            speak(f"Opening {app}")

        navigation.open(SITES[app])
        
        browser_context.set_page(
            url=SITES[app],
            site=app,
        )

        # * Action Memory
        set_memory("app", app)
        set_memory("site", app)
        set_memory("action", "open")
        
        debug_print("[MEMORY]", dump())

        return True

    # * ---------- Windows Apps ----------

    if app in WINDOWS_APPS:

        speak(f"Opening {app}")

        os.startfile(WINDOWS_APPS[app])

        # * Action Memory
        set_memory("app", app)
        set_memory("action", "open")
        
        debug_print("[MEMORY]", dump())

        return True


def ai_google(data):

    query = data.get("query", "").strip()

    if not query:
        return False

    if not is_live_execution():
        speak(f"Searching Google for {query}")

    result = browser.search_google(query)

    browser_context.set_page(
        site="google",
    )

    if not result:
        print("[Google] Search failed")
        return False

    # * Action Memory
    set_memory("site", "google")
    set_memory("search", query)
    set_memory("action", "google_search")
    set_memory("search_platform", "google")

    print("[MEMORY]", dump())

    return True


def ai_youtube(data):
    """
    Compatibility wrapper.

    The authoritative YouTube implementation lives in:
        skills.browser.youtube

    This wrapper delegates to it instead of maintaining
    a second YouTube implementation.
    """

    from skills.browser.youtube import ai_youtube as youtube_search

    return youtube_search(data)

def browser_open_result(data):

    url = (
        data.get("url", "")
        or ""
    ).strip()

    if not url:
        return False

    if not is_live_execution():
        speak("Opening the selected result")

    return browser.open(url)


def browser_read_page(data=None):
    """Read text from the current page using the existing browser worker."""
    data = data or {}
    return browser.read_current_page(
        max_chars=data.get("max_chars", 12000),
        timeout_ms=data.get("timeout_ms", 10000),
    )


register("browser_open_result", browser_open_result)
register("browser_read_page", browser_read_page, category="browser")

register("open", ai_open)

register("google_search", ai_google)
