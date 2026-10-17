"""
JARVIS ULTRA
Skill Categories

Logical categorization for registered JARVIS actions.
"""

CATEGORIES = {
    "system": {
        "shutdown",
        "restart",
        "sleep",
        "lock",
        "battery",
        "brightness",
        "volume",
        "taskmanager",
        "running_apps",
        "close_process",
    },

    "files": {
        "create_file",
        "create_folder",
        "open_file",
        "open_folder",
        "delete",
        "copy",
        "move",
        "rename",
        "search_file",
        "zip",
        "extract",
    },

    "browser": {
        "open",
        "google_search",
        "youtube_search",
        "browser_open_result",
        "browser_read_page",
    },

    "browser_control": {
        "refresh",
        "back",
        "forward",
        "new_tab",
        "close_tab",
        "scroll_down",
        "scroll_up",
    },

    "media": {
        "play",
        "spotify_open",
        "spotify_close",
        "spotify_play",
        "spotify_pause",
        "spotify_next",
        "spotify_previous",
        "spotify_play_song",
        "spotify_volume_up",
        "spotify_volume_down",
    },

    "camera": {
        "camera_preview",
        "camera_status",
        "camera_close",
        "capture",
        "start_recording",
        "stop_recording",
    },

    "android_control": {
        "android_check_adb",
        "android_check_device",
        "android_device_info",
        "android_open_app",
        "android_launch_app",
    },

    "payments": {
        "make_payment",
    },

    "phone_calls": {
        "phone_call_number",
        "phone_call_contact",
        "phone_call_confirmed",
        "missed_calls",
        "answer_call",
        "reject_call",
        "end_call",
        "call_status",
    },

    "communication": {
        "whatsapp_open",
        "whatsapp_close",
        "whatsapp_send_message",
        "whatsapp_send_file",
        "whatsapp_send_latest_photo",
        "whatsapp_send_latest_screenshot",
        "whatsapp_send_selected_file",
        "whatsapp_wait_contact",
        "whatsapp_wait_message",
        "chatgpt_search",
        "github_search",
        "show_contacts",
    },

    "memory": {
        "remember",
        "recall",
        "remember_contact",
        "forget_contact",

        "create_note",
        "list_notes",
        "clear_notes",

        "create_reminder",
        "list_reminders",
        "cancel_reminder",
    },
    
    "news": {
        "get_news",
    },

    "network": {
        "wifi_on",
        "wifi_off",
        "wifi_status",
        "wifi_list",
        "bluetooth_status",
        "bluetooth_devices",
        "weather",
    },

    "screen": {
        "screenshot",
        "screenshot_ai",
        "clipboard",
    },

    "ai": {
        "clarify",
    },

    "assistant": {
        "greet",
        "how_are_you",
        "welcome",
        "goodbye",
    },

    "utilities": {
        "time",
    },
}


# * ---------------------------------------------------------
# * Build reverse lookup
# * ---------------------------------------------------------

ACTION_CATEGORIES = {}

for category, actions in CATEGORIES.items():
    for action in actions:
        ACTION_CATEGORIES[action] = category


# * ---------------------------------------------------------
# * Default category
# * ---------------------------------------------------------

DEFAULT_CATEGORY = "uncategorized"


LOCAL_APPLICATIONS = {
    "notepad",
    "calculator",
    "calc",
    "paint",
    "cmd",
    "command prompt",
    "powershell",
    "explorer",
    "file explorer",
    "task manager",
    "registry editor",
    "device manager",
    "control panel",
    "settings",
}


def get_category(action: str) -> str:
    """
    Return the category for an action.
    """

    return ACTION_CATEGORIES.get(
        action,
        DEFAULT_CATEGORY,
    )


def list_categories() -> list[str]:
    """
    Return all available categories.
    """

    return sorted(CATEGORIES.keys())


def list_actions_by_category(category: str) -> list[str]:
    """
    Return actions belonging to a category.
    """

    return sorted(
        CATEGORIES.get(category, set())
    )
