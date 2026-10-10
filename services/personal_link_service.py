"""
JARVIS PRO
Personal Link Service

Resolves a personal-link name from configuration
and opens it using the web launcher.

No voice logic.
No command routing.
"""

from config.personal_links import configured_links, get_link
from hud.integration import HUDIntegration
from skills.browser.browser_controller import browser


def show_personal_links():
    """Publish the configured personal websites to the existing HUD log."""

    entries = configured_links()

    print("[PERSONAL LINKS] Website list requested")
    print(f"[PERSONAL LINKS] Loaded {len(entries)} configured links")

    HUDIntegration.personal_links(entries)

    if not entries:
        return "No personal websites are configured."

    return f"Found {len(entries)} configured personal websites."

def open_personal_link(name):
    """
    Open a configured personal destination.

    Returns:
        True  -> opened successfully
        False -> missing configuration or failure
    """

    if not name:
        print("[PERSONAL LINK] No link name provided.")
        return False

    link_name = str(name).strip().lower()

    if not link_name:
        print("[PERSONAL LINK] Empty link name.")
        return False

    url = get_link(link_name)

    if not url:

        print(
            f"[PERSONAL LINK] Not configured: {link_name}"
        )

        return False

    print(
        f"[PERSONAL LINK] Opening: "
        f"{link_name} -> {url}"
    )

    return browser.open(url)
