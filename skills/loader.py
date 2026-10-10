"""
JARVIS PRO
Skill Loader V2

Responsibilities:
- Load all registered skill modules
- Continue loading when an optional skill fails
- Track loaded and failed modules
- Provide loader diagnostics
- Preserve the existing load_all() API
"""

from importlib import import_module
from core.diagnostics import debug_print


# * =========================================================
# * Skill Modules
# * =========================================================

SKILLS = [
    "memory.memory",
    "memory.notes",
    "memory.reminders",
    "automation.scheduling",
    "ai.clarify",
    "media.media",
    "system.volume",
    "browser.browser_ai",
    "browser.youtube",
    "browser_control.browser_controls",
    "navigation.maps",
    "navigation.translate",
    "system.system",
    "system.brightness",
    "screen.screenshot",
    "screen.clipboard",
    "system.battery",
    "news.news",
    "network.wifi",
    "network.bluetooth",
    "network.weather",
    "system.process",
    "system.taskmanager",
    "files.files",
    "files.file_intelligence",
    "files.file_info",
    "files.recent",
    "files.recycle",
    "utilities.search",
    "files.zip_manager",
    "utilities.time_skill",
    "web.personal_links",
    "communication.github",
    "communication.chatgpt",
    "media.spotify",
    "media.image_generation",
    "assistant.greetings",
    "automation.home_automation",
    "communication.whatsapp",
    "communication.contact",
    "communication.email",
    "screen.screenshot_ai",
    "screen.screen_vision_skill",
    "camera.camera",
    "camera.vision_skill",
    "android_control.android_control",
    "payments.payments",
    "phone_call.phone_call",
]


# * =========================================================
# * Loader State
# * =========================================================

_LOADED = []
_FAILED = []
_INITIALIZED = False


# * =========================================================
# * Load One Skill
# * =========================================================

def load_skill(skill):
    """
    Load a single skill module.

    Returns:
        True  -> loaded successfully
        False -> failed
    """

    if not isinstance(skill, str):
        print(
            f"[SKILL LOADER] Invalid skill name: {skill!r}"
        )
        return False

    skill = skill.strip()

    if not skill:
        return False

    try:

        import_module(
            f"skills.{skill}"
        )

        if skill not in _LOADED:
            _LOADED.append(skill)

        debug_print(
            f"[SKILL LOADER] Loaded: {skill}"
        )

        return True

    except Exception as e:

        if skill not in _FAILED:
            _FAILED.append(skill)

        print(
            f"[SKILL LOADER ERROR] "
            f"{skill}: {e}"
        )

        return False


# * =========================================================
# * Load All
# * =========================================================

def load_all():
    """
    Load all configured skill modules.

    Existing API preserved.

    Returns:
        dict containing loader diagnostics.
    """

    global _INITIALIZED

    debug_print(
        "[SKILL LOADER] Starting..."
    )

    for skill in SKILLS:

        load_skill(skill)

    _INITIALIZED = True

    result = loader_info()

    debug_print(
        "[SKILL LOADER] Complete"
    )

    debug_print(
        f"[SKILL LOADER] "
        f"Modules loaded: {result['loaded_count']}"
    )

    debug_print(
        f"[SKILL LOADER] "
        f"Modules failed: {result['failed_count']}"
    )

    return result


# * =========================================================
# * Loaded Skills
# * =========================================================

def loaded_skills():
    """
    Return successfully loaded skill modules.
    """

    return list(_LOADED)


# * =========================================================
# * Failed Skills
# * =========================================================

def failed_skills():
    """
    Return skill modules that failed to load.
    """

    return list(_FAILED)


# * =========================================================
# * Loader Information
# * =========================================================

def loader_info():
    """
    Return loader diagnostics.
    """

    return {
        "initialized": _INITIALIZED,
        "configured_count": len(SKILLS),
        "loaded_count": len(_LOADED),
        "failed_count": len(_FAILED),
        "configured": list(SKILLS),
        "loaded": list(_LOADED),
        "failed": list(_FAILED),
    }
