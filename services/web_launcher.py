"""
JARVIS PRO
Web Launcher Service

Responsible only for opening URLs
using the system's default browser.

No voice logic.
No routing logic.
No personal-link logic.
"""

import webbrowser


# * =========================================================
# * Open URL
# * =========================================================

def open_url(url):
    """
    Open a URL using the system default browser.

    Returns:
        True  -> URL opened/requested successfully
        False -> invalid URL or launcher failure
    """

    if not url:
        print("[WEB LAUNCHER] No URL provided.")
        return False

    url = str(url).strip()

    if not url:
        print("[WEB LAUNCHER] Empty URL.")
        return False

    # * -----------------------------------------------------
    # * Basic URL validation
    # * -----------------------------------------------------

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        print(
            f"[WEB LAUNCHER] Invalid URL: {url}"
        )
        return False

    # * -----------------------------------------------------
    # * Open browser
    # * -----------------------------------------------------

    try:

        result = webbrowser.open(url)

        if result:

            print(
                f"[WEB LAUNCHER] Opened: {url}"
            )

            return True

        print(
            f"[WEB LAUNCHER] Browser did not open: {url}"
        )

        return False

    except Exception as e:

        print(
            f"[WEB LAUNCHER ERROR] {e}"
        )

        return False