"""Fast routes for simple Android Control commands."""

from __future__ import annotations


ANDROID_APP_COMMANDS = {
    # * Core phone apps
    "camera": "camera",
    "settings": "settings",
    "browser": "browser",

    # * Samsung Gallery
    "gallery": "Gallery",
    "samsung gallery": "Gallery",

    "photos": "Photos",
    "google photos": "Photos",

    "phone": "phone",
    "dialer": "phone",
    "messages": "messages",
    "sms": "messages",
    "contacts": "contacts",
    "calculator": "calculator",

    # * Communication
    "whatsapp": "WhatsApp",
    "whatsapp messenger": "WhatsApp",
    "telegram": "Telegram",
    "messenger": "Messenger",
    "facebook messenger": "Messenger",

    # * Google / media
    "youtube": "YouTube",
    "youtube music": "YouTube Music",
    "chrome": "Chrome",
    "google chrome": "Chrome",
    "google maps": "Google Maps",
    "maps": "Google Maps",
    "gmail": "Gmail",
    "google": "Google",
    "google drive": "Google Drive",
    "drive": "Google Drive",

    # * Music / streaming
    "spotify": "Spotify",

    # * OTT / streaming
    "jiohotstar": "JioHotstar",
    "jio hotstar": "JioHotstar",
    "hotstar": "JioHotstar",

    # * Payments
    "phonepe": "PhonePe",
    "google pay": "Google Pay",
    "gpay": "Google Pay",
    "paytm": "Paytm",

    # * Social media
    "instagram": "Instagram",
    "snapchat": "Snapchat",
    "facebook": "Facebook",
    "linkedin": "LinkedIn",
    "twitter": "Twitter",
    "x": "X",

    # * Common Android / Samsung apps
    "clock": "Clock",
    "calendar": "Calendar",
    "files": "Files",
    "file manager": "Files",
    "downloads": "Downloads",
    "music": "Music",
    "notes": "Notes",
}


PHONE_PREFIXES = (
    "open phone ",
    "open my phone ",
    "open android ",
    "open my android ",
    "open mobile ",
    "open my mobile ",
)


LAUNCH_PREFIXES = (
    "launch phone ",
    "launch my phone ",
    "launch android ",
    "launch my android ",
    "launch mobile ",
    "launch my mobile ",
)


def _extract_android_target(command: str) -> str | None:
    """Extract an Android app name from phone/mobile commands."""

    # * ---------------------------------------------------------
    # * Style 1:
    # * open phone camera
    # * open mobile whatsapp
    # * open my phone spotify
    # * ---------------------------------------------------------
    for prefix in PHONE_PREFIXES:
        if command.startswith(prefix):
            target = command.removeprefix(prefix).strip()

            if target:
                return target

    # * ---------------------------------------------------------
    # * Style 2:
    # * open camera on phone
    # * open whatsapp on mobile
    # * open spotify on my phone
    # * open instagram on my mobile
    # * ---------------------------------------------------------
    suffixes = (
        " on my phone",
        " on my mobile",
        " on phone",
        " on mobile",
    )

    for suffix in suffixes:
        if command.startswith("open ") and command.endswith(suffix):
            target = command[len("open "):-len(suffix)].strip()

            if target:
                return target

    return None


def android_route(command):
    if not command:
        return None

    command = str(command).strip().casefold()

    if not command:
        return None

    if command in {
        "check adb",
        "adb status",
        "check android adb",
    }:
        return [{"action": "android_check_adb"}]

    if command in {
        "check phone",
        "check android",
        "check android phone",
        "check device",
        "check android device",
    }:
        return [{"action": "android_check_device"}]

    if command in {
        "android device info",
        "android device information",
        "phone information",
        "check android information",
    }:
        return [{"action": "android_device_info"}]

    # * ---------------------------------------------------------
    # * Open Android apps
    #
    # * Supports:
    # * open phone camera
    # * open mobile camera
    # * open camera on phone
    # * open camera on mobile
    # * open phone whatsapp
    # * open whatsapp on phone
    # * ---------------------------------------------------------

    target = _extract_android_target(command)

    if target:
        app = ANDROID_APP_COMMANDS.get(target)

        if app:
            return [
                {
                    "action": "android_open_app",
                    "app": app,
                }
            ]

    # * ---------------------------------------------------------
    # * Launch Android apps
    # * ---------------------------------------------------------

    for prefix in LAUNCH_PREFIXES:
        if command.startswith(prefix):
            target = command.removeprefix(prefix).strip()

            if target.endswith(" on phone"):
                target = target.removesuffix(" on phone").strip()
            elif target.endswith(" on mobile"):
                target = target.removesuffix(" on mobile").strip()

            if target:
                return [
                    {
                        "action": "android_launch_app",
                        "app": target,
                    }
                ]

    # * Generic open/launch commands belong to the existing
    # ! desktop/browser routes and must never be intercepted
    # * by Android Control.
    return None