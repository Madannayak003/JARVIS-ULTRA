"""Standard Android intent specifications used by Android Control."""

from __future__ import annotations

from .models import IntentSpec


ACTION_MAIN = "android.intent.action.MAIN"
ACTION_VIEW = "android.intent.action.VIEW"
ACTION_DIAL = "android.intent.action.DIAL"
ACTION_CALL = "android.intent.action.CALL"
ACTION_SENDTO = "android.intent.action.SENDTO"
ACTION_IMAGE_CAPTURE = "android.media.action.IMAGE_CAPTURE"
ACTION_SETTINGS = "android.settings.SETTINGS"
CATEGORY_LAUNCHER = "android.intent.category.LAUNCHER"


STANDARD_APP_INTENTS = {
    "camera": IntentSpec(action=ACTION_IMAGE_CAPTURE),
    "settings": IntentSpec(action=ACTION_SETTINGS),
    "browser": IntentSpec(action=ACTION_VIEW, data="https://www.google.com"),
    "phone": IntentSpec(action=ACTION_DIAL),
    "messages": IntentSpec(action=ACTION_SENDTO, data="smsto:"),
    "contacts": IntentSpec(action=ACTION_VIEW, data="content://contacts/people"),
}


# * These are only discovery hints. A package is used only after it is found
# * in the connected device's installed-package list.
PACKAGE_HINTS = {
    "chrome": ("com.android.chrome",),
    "youtube": ("com.google.android.youtube",),
    "google maps": ("com.google.android.apps.maps",),
    "phonepe": ("com.phonepe.app",),
    "google pay": ("com.google.android.apps.nbu.paisa.user",),
    "paytm": ("net.one97.paytm",),
    "gallery": ("com.google.android.apps.photos",),
    "calculator": ("com.google.android.calculator",),
    "whatsapp": ("com.whatsapp",),
}


def normalize_app_name(value: str) -> str:
    return " ".join(str(value).strip().casefold().split())


def standard_intent_for(app_name: str) -> IntentSpec | None:
    return STANDARD_APP_INTENTS.get(normalize_app_name(app_name))


def package_hints_for(app_name: str) -> tuple[str, ...]:
    return PACKAGE_HINTS.get(normalize_app_name(app_name), ())
