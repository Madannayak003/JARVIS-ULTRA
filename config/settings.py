# * ===========================
# * JARVIS PRO SETTINGS
# * ===========================

import json
from pathlib import Path

from config.environment import get_env


# * APP_NAME is the authoritative user-facing assistant identity. The existing
# * Customize Assistant value is loaded into this same setting when the source
# * is still using the built-in default.
APP_NAME = "JARVIS PRO"

# * This marker identifies the built-in fallback only; it is not another active
# * assistant-name setting.
_BUILT_IN_APP_NAME = "JARVIS PRO"
_ASSISTANT_SETTINGS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "settings"
    / "jarvis_settings.json"
)

AI_PROVIDER_OPTIONS = ("AUTO", "GEMINI", "GROK", "OPENAI")

# Gemini Live is the primary conversational runtime.  Keep this identifier
# authoritative and deliberately non-overridable: changing the main Live
# model requires a reviewed source change and verification against the
# installed google-genai SDK/API.
PRIMARY_GEMINI_LIVE_MODEL = "gemini-3.8-live"

# Separate Gemini models are permitted only for explicitly reviewed,
# task-specific capabilities.  The empty mapping is intentional for this
# foundation migration; it prevents accidental model routing chains.
TASK_SPECIFIC_GEMINI_MODELS: dict[str, str] = {}

# Keep the voice mapping in one place. The settings surface intentionally
# exposes only gender; the concrete Live voices are implementation details.
GEMINI_LIVE_DEFAULT_VOICE = "Charon"
GEMINI_LIVE_FEMALE_VOICE = "Aoede"


def get_gemini_live_gender_setting() -> bool:
    settings = _read_persisted_settings()
    return bool(settings.get("geminiLiveFemaleVoiceEnabled", False))


def set_gemini_live_gender_setting(enabled: bool) -> bool:
    settings = _read_persisted_settings()
    settings["geminiLiveFemaleVoiceEnabled"] = bool(enabled)
    _ASSISTANT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _ASSISTANT_SETTINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump(settings, file, indent=2)
        file.write("\n")
    return bool(enabled)


def get_primary_gemini_live_model() -> str:
    """Return the one fixed Gemini Live model for the main conversation."""

    return PRIMARY_GEMINI_LIVE_MODEL


def _read_persisted_settings() -> dict:
    try:
        with _ASSISTANT_SETTINGS_FILE.open("r", encoding="utf-8") as file:
            value = json.load(file)
    except (OSError, TypeError, ValueError, AttributeError):
        return {}
    return value if isinstance(value, dict) else {}


def get_ai_provider_setting() -> str:
    """Return the persisted provider mode, defaulting safely to AUTO."""

    value = str(_read_persisted_settings().get("aiProvider", "AUTO")).upper()
    return value if value in AI_PROVIDER_OPTIONS else "AUTO"


def set_ai_provider_setting(provider: str) -> str:
    """Persist one of the supported provider modes."""

    normalized = str(provider).strip().upper()
    if normalized not in AI_PROVIDER_OPTIONS:
        raise ValueError(f"Unsupported AI provider: {provider}")

    settings = _read_persisted_settings()
    settings["aiProvider"] = normalized
    _ASSISTANT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _ASSISTANT_SETTINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump(settings, file, indent=2)
        file.write("\n")
    return normalized


def _persisted_assistant_name() -> str | None:
    try:
        with _ASSISTANT_SETTINGS_FILE.open("r", encoding="utf-8") as file:
            value = json.load(file).get("assistantName", "")
    except (OSError, TypeError, ValueError, AttributeError):
        return None

    if not isinstance(value, str):
        return None

    value = " ".join(value.strip().split())
    return value or None


if APP_NAME.casefold() == _BUILT_IN_APP_NAME.casefold():
    APP_NAME = _persisted_assistant_name() or APP_NAME


# * These are deliberately explicit pronunciation and compatibility aliases.
# ! Do not expand them fuzzily from the configured name.
PRONUNCIATION_ALIASES = ()
LEGACY_ASSISTANT_ALIASES = ("jarvis",)


def get_assistant_name() -> str:
    """Return the configured user-facing assistant name."""

    return APP_NAME


def get_assistant_name_lower() -> str:
    """Return the configured name in its normalized internal form."""

    return get_assistant_name().casefold()


def get_assistant_display_name() -> str:
    """Return a natural display form while preserving intentional casing."""

    name = get_assistant_name().strip()
    return name.title() if name.islower() else name


def get_assistant_aliases() -> tuple[str, ...]:
    """Return the configured name plus explicit pronunciation/legacy aliases."""

    aliases = (
        get_assistant_name_lower(),
        *(alias.casefold() for alias in PRONUNCIATION_ALIASES),
        *(alias.casefold() for alias in LEGACY_ASSISTANT_ALIASES),
    )
    return tuple(dict.fromkeys(alias for alias in aliases if alias))


def get_wake_words() -> tuple[str, ...]:
    """Build the deterministic wake-word set from the central identity."""

    words = []
    for alias in get_assistant_aliases():
        words.extend((alias, f"hey {alias}", f"hello {alias}"))
    return tuple(dict.fromkeys(words))


WAKE_WORDS = list(get_wake_words())


def set_assistant_name(name: str) -> str:
    """Update APP_NAME for the running process after a saved customization."""

    global APP_NAME

    normalized = " ".join(str(name).strip().split())
    if not normalized:
        raise ValueError("Assistant name cannot be empty.")

    APP_NAME = normalized
    WAKE_WORDS[:] = get_wake_words()
    return APP_NAME

VERSION = "1.0"

AUTHOR = "Madan"

VOICE = "male"

LANGUAGE = "en"

# ! Verbose provider/TTS diagnostics are opt-in. Runtime errors and warnings
# * continue to use their existing normal-output paths.
DEBUG = get_env("JARVIS_DEBUG", "0").strip().casefold() in {
    "1",
    "true",
    "yes",
    "on",
    "debug",
}

# * ===========================
# AI
# * ===========================

AI_PROVIDER = "auto"

# * ===========================
# * Local Vision / Face Recognition
# * ===========================

def _float_setting(name, default):
    try:
        return float(get_env(name, str(default)))
    except (TypeError, ValueError):
        return float(default)


def _int_setting(name, default):
    try:
        return int(get_env(name, str(default)))
    except (TypeError, ValueError):
        return int(default)


VISION_FACE_RECOGNITION_THRESHOLD = _float_setting(
    "JARVIS_VISION_FACE_RECOGNITION_THRESHOLD", 75.0
)
VISION_FACE_MIN_SIZE = _int_setting("JARVIS_VISION_FACE_MIN_SIZE", 80)
VISION_FACE_MIN_QUALITY = _float_setting("JARVIS_VISION_FACE_MIN_QUALITY", 0.20)
VISION_REGISTRATION_SAMPLE_COUNT = _int_setting(
    "JARVIS_VISION_REGISTRATION_SAMPLE_COUNT", 5
)
VISION_REGISTRATION_MAX_ATTEMPTS = _int_setting(
    "JARVIS_VISION_REGISTRATION_MAX_ATTEMPTS", 30
)
VISION_REGISTRATION_SAMPLE_INTERVAL = _float_setting(
    "JARVIS_VISION_REGISTRATION_SAMPLE_INTERVAL", 0.25
)
VISION_SPEECH_COOLDOWN = _float_setting("JARVIS_VISION_SPEECH_COOLDOWN", 5.0)
