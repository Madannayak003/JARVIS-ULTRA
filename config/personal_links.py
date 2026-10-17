"""
JARVIS ULTRA
Personal Links Configuration

Stores user-specific websites, profiles,
repositories, dashboards and project links.

This file contains configuration only.
No routing or browser logic belongs here.
"""

from config.environment import get_env
from config.settings import get_assistant_display_name
from urllib.parse import urlparse

# * =========================================================
# * Personal Links
# * =========================================================

PERSONAL_LINKS = {

    # * -----------------------------------------------------
    # * Social / Profiles
    # * -----------------------------------------------------

    "github": get_env("PERSONAL_GITHUB_URL"),
    "github_profile": get_env("PERSONAL_GITHUB_PROFILE_URL"),
    
    "github_repository": get_env("PERSONAL_GITHUB_REPOSITORIES_URL"),

    "facebook": get_env("PERSONAL_FACEBOOK_URL"),
    "facebook_profile": get_env("PERSONAL_FACEBOOK_PROFILE_URL"),

    "linkedin": get_env("PERSONAL_LINKEDIN_URL"),
    "linkedin_profile": get_env("PERSONAL_LINKEDIN_PROFILE_URL"),

    # * -----------------------------------------------------
    # * Personal Websites
    # * -----------------------------------------------------

    "website": get_env("PERSONAL_WEBSITE_URL"),
    "portfolio": get_env("PERSONAL_PORTFOLIO_URL"),

    "iot": get_env("PERSONAL_IOT_URL"),
    "iot_website": get_env("PERSONAL_IOT_WEBSITE_URL"),
    "iotrix_lab": get_env("IOTRIX_LAB_URL"),

    # * -----------------------------------------------------
    # * JARVIS
    # * -----------------------------------------------------

    "jarvis_github": get_env("JARVIS_GITHUB_URL"),
    "jarvis_repository": get_env("JARVIS_REPOSITORY_URL"),

    # * -----------------------------------------------------
    # * Projects
    # * -----------------------------------------------------

    "smart_parking": get_env("SMART_PARKING_URL"),
    "atmers": get_env("ATMERS_URL"),
}


# * Friendly labels for the existing configuration keys. These labels are only
# * presentation metadata; URLs remain exclusively in PERSONAL_LINKS/.env.
PERSONAL_LINK_NAMES = {
    "github": "GitHub",
    "github_profile": "GitHub Profile",
    "github_repository": "GitHub Repositories",
    "facebook": "Facebook",
    "facebook_profile": "Facebook Profile",
    "linkedin": "LinkedIn",
    "linkedin_profile": "LinkedIn Profile",
    "website": "Website",
    "portfolio": "Portfolio",
    "iot": "IoT",
    "iot_website": "IoT Website",
    "iotrix_lab": "IoTrix Lab",
    "jarvis_github": f"{get_assistant_display_name()} GitHub",
    "jarvis_repository": f"{get_assistant_display_name()} Repository",
    "smart_parking": "Smart Parking",
    "atmers": "ATMERS",
}


def is_safe_personal_url(value):
    """Accept only absolute HTTP(S) URLs for the clickable HUD list."""

    url = str(value or "").strip()

    if not url or any(character.isspace() for character in url):
        return False

    parsed = urlparse(url)

    return (
        parsed.scheme.lower() in {"http", "https"}
        and bool(parsed.netloc)
    )


def configured_links():
    """Return validated, display-ready links from the existing configuration.

    Blank, unsafe, and duplicate URL aliases are omitted. The first configured
    key in PERSONAL_LINKS remains the canonical label for a duplicate URL.
    """

    entries = []
    seen_urls = set()

    for key, value in PERSONAL_LINKS.items():
        url = str(value or "").strip()

        if not is_safe_personal_url(url) or url in seen_urls:
            continue

        seen_urls.add(url)
        entries.append({
            "name": PERSONAL_LINK_NAMES.get(key, key.replace("_", " ").title()),
            "url": url,
        })

    return entries


# * =========================================================
# * Get Link
# * =========================================================

def get_link(name):
    """
    Return a configured personal link.

    Returns:
        str | None
    """

    if not name:
        return None

    key = str(name).strip().lower()

    return PERSONAL_LINKS.get(key)


# * =========================================================
# * Check Link
# * =========================================================

def has_link(name):
    """
    Return True when a personal link is configured.
    """

    link = get_link(name)

    return bool(link)
