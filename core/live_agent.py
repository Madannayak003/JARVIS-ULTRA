"""Structured capability bridge for Gemini Live Agent Mode.

This module deliberately does not replace the dispatcher or registry.  It
gives the Live model a typed escape hatch to an already-registered JARVIS
skill, while ``jarvis_command`` remains available for compatibility and for
capabilities that are intentionally routed through the natural-language
dispatcher.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from time import perf_counter
from typing import Any, Callable, Mapping

from core.diagnostics import debug_print
from core.live_execution import get_live_responses


# These are deliberately small, high-use schemas for handlers whose payloads
# were inspected in the existing skills. All other registered actions remain
# available through the generic capability and legacy command paths.
LIVE_CAPABILITY_SCHEMAS: dict[str, dict[str, Any]] = {
    "assistant_name": {
        "purpose": "Report the configured JARVIS assistant name.",
        "properties": {},
        "expected_result": "The configured assistant name or an honest failure.",
    },
    "greet": {
        "purpose": "Give a local JARVIS greeting; optionally preserve a supplied good-morning, afternoon, or evening style.",
        "properties": {
            "command": {
                "type": "string",
                "description": "Optional greeting text supplied by the user.",
            },
        },
        "expected_result": "The local greeting result or an honest failure.",
    },
    "how_are_you": {
        "purpose": "Give JARVIS's local response to a how-are-you question.",
        "properties": {},
        "expected_result": "The local response or an honest failure.",
    },
    "goodbye": {
        "purpose": "Give JARVIS's local goodbye response without changing application state.",
        "properties": {},
        "expected_result": "The local goodbye response or an honest failure.",
    },
    "back": {
        "purpose": "Navigate the existing browser back one page.",
        "properties": {},
        "expected_result": "The browser navigation result or an honest failure.",
    },
    "forward": {
        "purpose": "Navigate the existing browser forward one page.",
        "properties": {},
        "expected_result": "The browser navigation result or an honest failure.",
    },
    "close_tab": {
        "purpose": "Close the active browser tab through the existing browser controller.",
        "properties": {},
        "expected_result": "The browser tab close result or an honest failure.",
    },
    "refresh": {
        "purpose": "Refresh the active browser page through the existing browser controller.",
        "properties": {},
        "expected_result": "The browser refresh result or an honest failure.",
    },
    "bluetooth_devices": {
        "purpose": "Open Windows Bluetooth device settings. This does not claim that a device was paired or changed.",
        "properties": {},
        "inject_action": True,
        "expected_result": "The actual settings-launch result or an honest failure.",
    },
    "bluetooth_status": {
        "purpose": "Open Windows Bluetooth status/settings. This does not claim a device connection state was changed.",
        "properties": {},
        "inject_action": True,
        "expected_result": "The actual settings-launch result or an honest failure.",
    },
    "camera_close": {
        "purpose": "Close the configured physical camera through the existing camera manager.",
        "properties": {},
        "expected_result": "The camera close result or an honest failure.",
    },
    "camera_preview": {
        "purpose": "Open the configured physical camera preview. This is not a desktop screenshot.",
        "properties": {},
        "expected_result": "The camera preview result or an honest camera-access failure.",
    },
    "camera_status": {
        "purpose": "Report the configured physical camera availability.",
        "properties": {},
        "expected_result": "The actual camera status or an honest availability report.",
    },
    "list_notes": {
        "purpose": "Read the user's existing saved notes without modifying them.",
        "properties": {},
        "expected_result": "The actual saved-note list or an honest failure.",
    },
    "clipboard": {
        "purpose": "Read the current clipboard or request a bounded summary/explanation through the existing clipboard skill.",
        "properties": {
            "mode": {
                "type": "string",
                "enum": ["read", "summary", "explain"],
                "description": "Read, summarize, or explain the clipboard contents.",
            },
        },
        "expected_result": "The actual clipboard result or an honest access/processing failure.",
    },
    "recent_files": {
        "purpose": "List the ten most recently modified files in the user's Downloads folder.",
        "properties": {},
        "expected_result": "The actual recent-file list or an honest unavailable result.",
    },
    "search_file": {
        "purpose": "Search local files using the existing JARVIS file-search service.",
        "properties": {
            "query": {"type": "string", "description": "File name or path text to search for."},
            "extension": {"type": "string", "description": "Optional file extension filter."},
        },
        "expected_result": "The actual matching file paths or an honest failure.",
    },
    "file_intelligence_request": {
        "purpose": "Process the active uploaded file request using the existing file-intelligence service.",
        "properties": {"request": {"type": "string", "description": "Read, summarize, or ask a question about the active file."}},
        "required": ["request"],
        "inject_action": True,
        "expected_result": "The actual file-intelligence result or an honest unavailable/error result.",
    },
    "file_question_request": {
        "purpose": "Ask a question about the active uploaded file using the existing file-intelligence service.",
        "properties": {"question": {"type": "string", "description": "Question to answer from the active file."}},
        "required": ["question"],
        "inject_action": True,
        "expected_result": "The actual answer or an honest unavailable/error result.",
    },
    "file_search_request": {
        "purpose": "Search the active uploaded file using the existing file-intelligence service.",
        "properties": {"query": {"type": "string", "description": "Text to find in the active file."}},
        "required": ["query"],
        "inject_action": True,
        "expected_result": "The actual file matches or an honest unavailable/error result.",
    },
    "show_contacts": {
        "purpose": "List saved personal contacts without changing them.",
        "properties": {},
        "expected_result": "The actual saved contacts or an empty-list response.",
    },
    "show_email_contacts": {
        "purpose": "List saved email contacts without changing them.",
        "properties": {},
        "expected_result": "The actual saved email contacts or an empty-list response.",
    },
    "show_personal_links": {
        "purpose": "List configured personal websites without opening one.",
        "properties": {},
        "expected_result": "The actual configured-link summary or an honest unavailable result.",
    },
    "clear_notes": {
        "purpose": "Clear all saved JARVIS notes after the user's explicit request.",
        "properties": {},
        "expected_result": "Confirmed note clearing or an honest failure.",
    },
    "remember_contact": {
        "purpose": "Save one personal contact alias and its real name.",
        "properties": {
            "alias": {"type": "string", "description": "Short name used to refer to the contact."},
            "real_name": {"type": "string", "description": "Contact's real name."},
        },
        "required": ["alias", "real_name"],
        "expected_result": "Confirmed saved contact or an honest failure.",
    },
    "forget_contact": {
        "purpose": "Remove one saved personal contact by alias.",
        "properties": {"alias": {"type": "string", "description": "Saved contact alias."}},
        "required": ["alias"],
        "expected_result": "Confirmed removal or an honest not-found/failure result.",
    },
    "close_process": {
        "purpose": "Close one named Windows process after the user's explicit request.",
        "properties": {"process": {"type": "string", "description": "Process name or distinctive substring."}},
        "required": ["process"],
        "inject_action": True,
        "expected_result": "Confirmed process termination, no-match result, or honest permission failure.",
    },
    "zip": {
        "purpose": "Create a ZIP archive from a specified folder.",
        "properties": {
            "folder": {"type": "string", "description": "Folder to archive."},
            "output": {"type": "string", "description": "Output archive path without the .zip suffix."},
        },
        "required": ["folder", "output"],
        "inject_action": True,
        "expected_result": "Confirmed archive path or honest failure.",
    },
    "extract": {
        "purpose": "Extract a specified archive into a destination folder.",
        "properties": {
            "zip": {"type": "string", "description": "Archive path."},
            "destination": {"type": "string", "description": "Extraction destination folder."},
        },
        "required": ["zip", "destination"],
        "inject_action": True,
        "expected_result": "Confirmed extraction destination or honest failure.",
    },
    "recycle": {
        "purpose": "Move one specified local path to the Windows recycle bin.",
        "properties": {"path": {"type": "string", "description": "Existing file or folder path."}},
        "required": ["path"],
        "expected_result": "Confirmed recycle-bin operation or honest failure.",
    },
    "open_personal_link": {
        "purpose": "Open one configured personal website by its configured name.",
        "properties": {
            "name": {"type": "string", "description": "Configured personal website name."},
        },
        "required": ["name"],
        "expected_result": "A reported browser-open result or an honest missing-configuration failure.",
    },
    "welcome": {
        "purpose": "Respond to a user's thanks with the existing local JARVIS greeting.",
        "properties": {},
        "expected_result": "A reported local greeting result.",
    },
    "new_tab": {
        "purpose": "Open a new tab in the existing browser controller.",
        "properties": {},
        "expected_result": "The browser new-tab result or an honest failure.",
    },
    "scroll_down": {
        "purpose": "Scroll the active browser page down through the existing browser controller.",
        "properties": {},
        "expected_result": "The browser scroll result or an honest failure.",
    },
    "scroll_up": {
        "purpose": "Scroll the active browser page up through the existing browser controller.",
        "properties": {},
        "expected_result": "The browser scroll result or an honest failure.",
    },
    "close": {
        "purpose": "Close the active browser window through the existing browser controller.",
        "properties": {},
        "expected_result": "The browser close result or an honest failure.",
    },
    "create_image": {
        "purpose": "Generate and save an image from a text prompt through the configured image service.",
        "properties": {
            "prompt": {"type": "string", "description": "Description of the image to generate."},
        },
        "required": ["prompt"],
        "expected_result": "The saved image location or an honest service, validation, or unavailable failure.",
    },
    "send_email": {
        "purpose": "Send an email through the configured Gmail service, or begin the existing local draft flow when only a recipient is supplied.",
        "properties": {
            "recipient": {"type": "string", "description": "Recipient email address or saved email alias."},
            "subject": {"type": "string", "description": "Optional email subject."},
            "body": {"type": "string", "description": "Optional email body."},
        },
        "required": ["recipient"],
        "expected_result": "A reported send/draft result or an honest validation or service failure.",
    },
    "screenshot_ai": {
        "purpose": "Request analysis of an existing screenshot file. Gemini Live reports this capability as unsupported because Live analyzes its own correlated screen image.",
        "properties": {},
        "expected_result": "An honest unsupported result inside Gemini Live; never claim screenshot-file analysis occurred.",
    },
    "home_automation": {
        "purpose": "Control or query a configured home-automation device through the existing ESP32 integration.",
        "properties": {
            "command": {"type": "string", "description": "Device command such as status, turn_on, or turn_off."},
            "device": {"type": "string", "description": "Configured device such as light, led, or fan; omit for status."},
        },
        "required": ["command"],
        "expected_result": "The actual device/status result or an honest unavailable or invalid-command result.",
    },
    "spotify_open": {
        "purpose": "Open the installed Spotify application.",
        "properties": {},
        "expected_result": "A real launch result or an honest failure.",
    },
    "spotify_close": {
        "purpose": "Close the installed Spotify application.",
        "properties": {},
        "expected_result": "A real close result or an honest failure.",
    },
    "spotify_play": {
        "purpose": "Resume Spotify playback using the existing Spotify integration.",
        "properties": {},
        "expected_result": "Confirmed playback start or an honest authentication/device failure.",
    },
    "spotify_pause": {
        "purpose": "Pause Spotify playback using the existing Spotify integration.",
        "properties": {},
        "expected_result": "Confirmed pause request or an honest failure.",
    },
    "spotify_next": {
        "purpose": "Skip to the next Spotify track.",
        "properties": {},
        "expected_result": "A real next-track result or an honest failure.",
    },
    "spotify_previous": {
        "purpose": "Return to the previous Spotify track.",
        "properties": {},
        "expected_result": "A real previous-track result or an honest failure.",
    },
    "spotify_volume_up": {
        "purpose": "Increase system media volume for Spotify playback.",
        "properties": {},
        "expected_result": "A real media-volume action.",
    },
    "spotify_volume_down": {
        "purpose": "Decrease system media volume for Spotify playback.",
        "properties": {},
        "expected_result": "A real media-volume action.",
    },
    "spotify_play_song": {
        "purpose": "Find and start a specific Spotify track through the existing Spotify API integration.",
        "properties": {
            "song": {"type": "string", "description": "Track or artist search text."},
        },
        "required": ["song"],
        "expected_result": "Confirmed track playback or an honest authentication/device/search failure.",
    },
    "battery": {
        "purpose": "Report current battery percentage and charging state.",
        "properties": {},
        "expected_result": "A real battery status response or a reported failure.",
    },
    "android_check_device": {"purpose": "Check the selected Android device connection.", "properties": {}, "expected_result": "The actual ADB connection state."},
    "android_device_info": {"purpose": "Report selected Android device information.", "properties": {}, "expected_result": "Actual device model, Android version, and connection information."},
    "android_battery_status": {"purpose": "Report selected Android battery values.", "properties": {}, "expected_result": "Actual battery values or an honest failure."},
    "android_open_app": {"purpose": "Open an installed Android application by name.", "properties": {"app": {"type": "string"}}, "required": ["app"], "expected_result": "A real launch result or failure."},
    "android_launch_app": {"purpose": "Launch an installed Android application by name.", "properties": {"app": {"type": "string"}}, "required": ["app"], "expected_result": "A real launch result or failure."},
    "android_close_app": {"purpose": "Force-stop an installed Android application.", "properties": {"app": {"type": "string"}, "package": {"type": "string"}}, "expected_result": "A confirmed force-stop or honest failure."},
    "android_list_apps": {"purpose": "List installed Android package names.", "properties": {}, "expected_result": "The actual installed package list."},
    "android_search_apps": {"purpose": "Search installed Android applications.", "properties": {"query": {"type": "string"}}, "required": ["query"], "expected_result": "Actual matching packages."},
    "android_foreground_app": {"purpose": "Report which app is currently foregrounded on the connected Android phone. Use only when the user explicitly says phone, mobile, Android, or foreground Android app; never use for Windows running applications.", "properties": {}, "expected_result": "Actual foreground Android package or honest unavailability."},
    "android_home": {"purpose": "Return the selected Android phone to its home screen.", "properties": {}, "expected_result": "A real home intent result."},
    "android_search_youtube": {"purpose": "Search within YouTube on the Android phone.", "properties": {"query": {"type": "string"}}, "required": ["query"], "expected_result": "A real YouTube URL launch or failure."},
    "android_search_web": {"purpose": "Search the web on Android using the requested provider.", "properties": {"query": {"type": "string"}, "provider": {"type": "string", "enum": ["google", "bing", "duckduckgo"]}}, "required": ["query"], "expected_result": "A real provider URL launch or failure."},
    "android_camera": {"purpose": "Open Android camera; optional legacy front/rear hint may be ignored by the camera app.", "properties": {"facing": {"type": "string", "enum": ["front", "rear"]}}, "expected_result": "Camera opened, without claiming a capture or lens switch."},
    "android_open_front_camera": {"purpose": "Request the front Android camera.", "properties": {}, "expected_result": "Camera launch result with app-specific lens limitation."},
    "android_open_rear_camera": {"purpose": "Request the rear Android camera.", "properties": {}, "expected_result": "Camera launch result with app-specific lens limitation."},
    "android_capture_photo": {"purpose": "Capture and save a phone photo only when a supported capture mechanism is available.", "properties": {"facing": {"type": "string", "enum": ["front", "rear"]}}, "expected_result": "A confirmed saved photo or honest unsupported result."},
    "android_flashlight_on": {"purpose": "Turn the phone flashlight on when a verified mechanism is available.", "properties": {}, "expected_result": "Confirmed state change or honest unsupported result."},
    "android_flashlight_off": {"purpose": "Turn the phone flashlight off when a verified mechanism is available.", "properties": {}, "expected_result": "Confirmed state change or honest unsupported result."},
    "taskmanager": {
        "purpose": "Report current Windows CPU, memory, and disk usage through the existing Windows task-manager skill. This is not an Android capability.",
        "properties": {},
        "expected_result": "A real system-usage response or a reported failure.",
    },
    "running_apps": {
        "purpose": "List processes currently running on this Windows computer. Use for 'running apps', 'list running applications', or 'what apps are open on my computer'. Do not use the Android foreground-app capability unless the user explicitly names a phone or Android device.",
        "properties": {},
        "inject_action": True,
        "expected_result": "The actual Windows process-list result or an honest failure.",
    },
    "lock": {
        "purpose": (
            "Lock the Windows workstation immediately. This is distinct from "
            "shutting down Windows and from closing the JARVIS application. "
            "Use for 'lock my screen', 'lock this computer', or 'lock the PC'."
        ),
        "properties": {},
        "expected_result": "Confirmed Windows workstation lock or an honest failure/unavailable result.",
    },
    "shutdown": {
        "purpose": (
            "Shut down the Windows computer, not the JARVIS application. Use "
            "for 'shut down my computer', 'turn off Windows', or 'power off "
            "the PC'. This is disruptive and requires explicit confirmation "
            "after JARVIS asks the user. Never use for 'shut yourself down' "
            "or 'close JARVIS'."
        ),
        "properties": {
            "confirmed": {
                "type": "boolean",
                "description": (
                    "Only true after the user explicitly confirms a prior "
                    "JARVIS shutdown prompt; omit or use false for the first request."
                ),
            },
        },
        "expected_result": "Confirmed Windows shutdown, a confirmation request, or an honest failure/unavailable result.",
    },
    "terminate_jarvis": {
        "purpose": (
            "Gracefully close the JARVIS ULTRA application while leaving "
            "Windows running. Use for 'shut yourself down', 'close JARVIS', "
            "'exit JARVIS', or 'quit JARVIS'. Never use for turning off Windows."
        ),
        "properties": {},
        "expected_result": "Confirmed application shutdown request or an honest failure.",
    },
    "time": {
        "purpose": "Report the current local time.",
        "properties": {},
        "expected_result": "A real current-time response.",
    },
    "get_news": {
        "purpose": "Retrieve the latest news through the existing news skill.",
        "properties": {},
        "expected_result": "Current headlines returned by the configured news source, or a reported failure.",
    },
    "weather": {
        "purpose": "Retrieve current weather through the existing weather skill.",
        "properties": {
            "location": {"type": "string", "description": "Optional city or place; omit for the configured current location."},
        },
        "expected_result": "Real current weather data or a reported failure.",
    },
    "screen_vision_analyze": {
        "purpose": "Capture and analyze the current desktop through the active Gemini Live session.",
        "properties": {},
        "expected_result": "The actual screen analysis returned by Gemini Live, or a reported capture/analysis failure.",
    },
    "screenshot": {
        "purpose": "Capture the desktop screen only using the existing screenshot skill. This is not a camera photograph and must not be used for photo or camera requests.",
        "properties": {},
        "expected_result": "A reported capture result; the returned boolean does not expose the file contents.",
    },
    "capture": {
        "purpose": "Take a real photograph with the configured camera/photo-capture capability. Never substitute a desktop screenshot.",
        "properties": {},
        "expected_result": "A real camera capture result, or an honest report that the camera is unavailable.",
    },
    "camera_preview": {
        "purpose": "Open the configured physical camera preview. This does not capture a desktop screenshot.",
        "properties": {},
        "expected_result": "The actual camera preview result or an honest camera-access failure.",
    },
    "camera_status": {
        "purpose": "Report whether the configured physical camera is available and open.",
        "properties": {},
        "expected_result": "The actual camera status or an honest availability report.",
    },
    "create_reminder": {
        "purpose": "Create and persist a personal reminder in the existing reminder scheduler.",
        "properties": {
            "text": {"type": "string", "description": "What to remind the user about."},
            "remind_at": {"type": "string", "description": "A future ISO-8601 local date/time or a relative phrase such as 'in 30 seconds'."},
        },
        "required": ["text", "remind_at"],
        "expected_result": "Confirmation only after the reminder is persisted, or an honest failure.",
    },
    "list_reminders": {
        "purpose": "List active reminders from the existing reminder store.",
        "properties": {},
        "expected_result": "The actual active reminders or an empty-list response.",
    },
    "cancel_reminder": {
        "purpose": "Cancel one persisted reminder by its numeric ID.",
        "properties": {"id": {"type": "integer", "description": "Reminder ID returned by the reminder list or creation flow."}},
        "required": ["id"],
        "expected_result": "Confirmation only after the reminder was updated, or an honest failure.",
    },
    "create_schedule": {
        "purpose": "Create and persist a scheduled JARVIS task that runs the requested command at the requested time.",
        "properties": {
            "command": {"type": "string", "description": "The registered JARVIS command to execute when due."},
            "run_at": {"type": "string", "description": "A future ISO-8601 local date/time."},
            "recurrence": {"type": "string", "enum": ["none", "daily"], "description": "One-time or daily execution."},
        },
        "required": ["command", "run_at"],
        "expected_result": "Confirmation only after the scheduled task is persisted, or an honest failure.",
    },
    "list_schedules": {
        "purpose": "List persisted JARVIS scheduled tasks and their current states.",
        "properties": {},
        "expected_result": "The actual scheduled tasks or an empty-list response.",
    },
    "cancel_schedule": {
        "purpose": "Cancel one persisted scheduled task by its numeric ID.",
        "properties": {"id": {"type": "integer", "description": "Scheduled-task ID returned by the schedule list or creation flow."}},
        "required": ["id"],
        "expected_result": "Confirmation only after the scheduled task was updated, or an honest failure.",
    },
    "whatsapp_open": {
        "purpose": "Open the existing WhatsApp application/session.",
        "properties": {},
        "expected_result": "The actual open result or an honest failure.",
    },
    "whatsapp_close": {
        "purpose": "Close the existing WhatsApp application.",
        "properties": {},
        "expected_result": "A reported close result.",
    },
    "whatsapp_send_message": {
        "purpose": "Send a WhatsApp text message through the existing authenticated sender.",
        "properties": {
            "contact": {"type": "string", "description": "Saved contact name or supported self-chat destination."},
            "message": {"type": "string", "description": "Message text to send."},
        },
        "required": ["contact", "message"],
        "expected_result": "Actual sender success or a truthful recipient/session/send failure.",
    },
    "remember_email_contact": {
        "purpose": "Save an email contact alias and address in the existing email-contact store.",
        "properties": {
            "alias": {"type": "string", "description": "Name used to refer to the email contact."},
            "email": {"type": "string", "description": "Email address."},
        },
        "required": ["alias", "email"],
        "expected_result": "Confirmed saved email contact or honest failure.",
    },
    "forget_email_contact": {
        "purpose": "Remove one saved email contact by alias.",
        "properties": {"alias": {"type": "string", "description": "Saved email contact alias."}},
        "required": ["alias"],
        "expected_result": "Confirmed removal or honest not-found/failure result.",
    },
    "whatsapp_wait_contact": {
        "purpose": "Enter the existing WhatsApp follow-up flow when the recipient is missing.",
        "properties": {},
        "expected_result": "A truthful request for the missing recipient.",
    },
    "whatsapp_wait_message": {
        "purpose": "Continue the existing WhatsApp follow-up flow for a known recipient.",
        "properties": {"contact": {"type": "string", "description": "Recipient contact."}},
        "required": ["contact"],
        "expected_result": "A truthful request for the missing message text.",
    },
    "schedule_whatsapp_message": {
        "purpose": "Persist a WhatsApp message for the existing WhatsApp scheduler without sending it now.",
        "properties": {
            "contact": {"type": "string", "description": "Saved contact name or supported self-chat destination."},
            "message": {"type": "string", "description": "Message text to send later."},
            "send_at": {"type": "string", "description": "Future ISO-8601 local date/time."},
        },
        "required": ["contact", "message", "send_at"],
        "expected_result": "Confirmation only after persistence, without sending during creation.",
    },
    "list_scheduled_whatsapp": {
        "purpose": "List persisted pending WhatsApp messages scheduled for later.",
        "properties": {},
        "expected_result": "The actual scheduled messages or an empty-list response.",
    },
    "cancel_scheduled_whatsapp": {
        "purpose": "Cancel one persisted scheduled WhatsApp message by numeric ID.",
        "properties": {"id": {"type": "integer", "description": "Scheduled WhatsApp message ID."}},
        "required": ["id"],
        "expected_result": "Confirmation only after the scheduled message is cancelled, or an honest failure.",
    },
    "reschedule_scheduled_whatsapp": {
        "purpose": "Move one persisted scheduled WhatsApp message to a new future time.",
        "properties": {
            "id": {"type": "integer", "description": "Scheduled WhatsApp message ID."},
            "send_at": {"type": "string", "description": "Future ISO-8601 local date/time."},
        },
        "required": ["id", "send_at"],
        "expected_result": "Confirmation only after persistence, or an honest failure.",
    },
    "whatsapp_send_latest_photo": {
        "purpose": "Send the latest captured photo to a WhatsApp contact.",
        "properties": {"contact": {"type": "string", "description": "Recipient contact."}},
        "required": ["contact"],
        "expected_result": "Actual send result or a truthful failure.",
    },
    "whatsapp_send_latest_screenshot": {
        "purpose": "Send the latest screenshot to a WhatsApp contact.",
        "properties": {"contact": {"type": "string", "description": "Recipient contact."}},
        "required": ["contact"],
        "expected_result": "Actual send result or a truthful failure.",
    },
    "whatsapp_send_file": {
        "purpose": "Send a selected file to a WhatsApp contact.",
        "properties": {
            "contact": {"type": "string", "description": "Recipient contact."},
            "filename": {"type": "string", "description": "File name or search text."},
        },
        "required": ["contact", "filename"],
        "expected_result": "Actual send result or a truthful failure/selection request.",
    },
    "whatsapp_send_selected_file": {
        "purpose": "Send the selected pending WhatsApp file by its numeric option index.",
        "properties": {"index": {"type": "integer", "minimum": 0, "description": "Pending file option index."}},
        "required": ["index"],
        "expected_result": "Actual send result or a truthful failure.",
    },
    "whatsapp_call": {
        "purpose": "Start a WhatsApp voice call to a resolved contact.",
        "properties": {"contact": {"type": "string", "description": "Recipient contact."}},
        "required": ["contact"],
        "expected_result": "Actual call result or a truthful failure.",
    },
    "whatsapp_video_call": {
        "purpose": "Start a WhatsApp video call to a resolved contact.",
        "properties": {"contact": {"type": "string", "description": "Recipient contact."}},
        "required": ["contact"],
        "expected_result": "Actual call result or a truthful failure.",
    },
    "volume": {
        "purpose": "Read or control Windows master volume.",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["up", "down", "mute", "unmute", "status"],
                "description": "Relative volume operation or status query.",
            },
            "percent": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Exact volume percentage.",
            },
        },
        "expected_result": "A reported volume operation result or failure.",
    },
    "brightness": {
        "purpose": "Read or control display brightness.",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["up", "down", "status"],
                "description": "Relative brightness operation or status query.",
            },
            "percent": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Exact brightness percentage.",
            },
        },
        "expected_result": "A reported brightness operation result or failure.",
    },
    "wifi_on": {
        "purpose": "Enable the Windows Wi-Fi interface.",
        "properties": {},
        "inject_action": True,
        "expected_result": "A real enable result or failure.",
    },
    "wifi_off": {
        "purpose": "Disable the Windows Wi-Fi interface.",
        "properties": {},
        "inject_action": True,
        "expected_result": "A real disable result or failure.",
    },
    "wifi_status": {
        "purpose": "Report the Windows Wi-Fi connection state.",
        "properties": {},
        "inject_action": True,
        "expected_result": "A real Wi-Fi status response or failure.",
    },
    "wifi_list": {
        "purpose": "List nearby Windows Wi-Fi network names without connecting to any network.",
        "properties": {},
        "inject_action": True,
        "expected_result": "The actual discovered network names or an honest failure.",
    },
    "translate_text": {
        "purpose": "Translate supplied text with the existing JARVIS translation service.",
        "properties": {
            "text": {"type": "string", "description": "Text to translate."},
            "target": {"type": "string", "description": "Target language name or code."},
        },
        "required": ["text", "target"],
        "expected_result": "The translated text or an honest failure.",
    },
    "open_file": {
        "purpose": "Open an existing local file through JARVIS file handling.",
        "properties": {
            "path": {
                "type": "string",
                "description": "Existing file path or JARVIS-resolvable file reference.",
            },
        },
        "required": ["path"],
        "inject_action": True,
        "expected_result": "A reported open result or failure; never assume a missing file opened.",
    },
    "open_folder": {
        "purpose": "Open an existing local folder through JARVIS file handling.",
        "properties": {
            "path": {
                "type": "string",
                "description": "Existing folder path or JARVIS-resolvable folder reference.",
            },
        },
        "required": ["path"],
        "inject_action": True,
        "expected_result": "A reported open result or failure.",
    },
    "file_info": {
        "purpose": "Report metadata and whether an existing local path is a file or folder.",
        "properties": {
            "path": {
                "type": "string",
                "description": "Existing file or folder path, or a JARVIS-resolvable path reference.",
            },
        },
        "required": ["path"],
        "expected_result": "A reported file-information result or failure; never assume a missing path exists.",
    },
    "file_list": {
        "purpose": "List files currently registered in JARVIS File Intelligence; this is not an arbitrary filesystem-directory listing.",
        "properties": {},
        "inject_action": True,
        "expected_result": "The actual registered-file records, which may be an empty list; a project-folder listing requires a separate supported capability.",
    },
    "file_search": {
        "purpose": "Search extracted text in files registered in JARVIS File Intelligence.",
        "properties": {
            "query": {
                "type": "string",
                "description": "Text to find in extracted file content.",
            },
            "file_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional registered file IDs to search; omit to search all registered files.",
            },
        },
        "required": ["query"],
        "inject_action": True,
        "expected_result": "Actual matching files and bounded line-match records, or an empty result list.",
    },
    "create_note": {
        "purpose": "Save a personal note using the existing notes skill.",
        "properties": {
            "text": {
                "type": "string",
                "description": "The note text to save.",
            },
        },
        "required": ["text"],
        "expected_result": "A reported save result or failure.",
    },
    "google_search": {
        "purpose": "Search the web using the existing Google browser search skill.",
        "properties": {
            "query": {"type": "string", "description": "Topic or search terms."},
        },
        "required": ["query"],
        "expected_result": "Actual search results or a reported failure.",
    },
    "open": {
        "purpose": "Open one supported website or Windows application by its configured name.",
        "properties": {"app": {"type": "string", "description": "Supported website or Windows application name."}},
        "required": ["app"],
        "expected_result": "The opened target details or an honest unsupported/failure result.",
    },
    "youtube_search": {
        "purpose": "Search YouTube using the existing browser search skill.",
        "properties": {
            "query": {"type": "string", "description": "Video or channel search terms."},
        },
        "required": ["query"],
        "expected_result": "Actual search results or a reported failure.",
    },
    "youtube_play_first": {
        "purpose": "Play the first result from a YouTube search, or search the supplied query first.",
        "properties": {"query": {"type": "string", "description": "Optional YouTube search terms."}},
        "expected_result": "A YouTube navigation result with playback verification status.",
    },
    "youtube_pause": {
        "purpose": "Pause the active YouTube video in the existing browser.",
        "properties": {},
        "expected_result": "A reported pause result or honest browser failure.",
    },
    "youtube_resume": {
        "purpose": "Resume the active YouTube video in the existing browser.",
        "properties": {},
        "expected_result": "A reported resume result or honest browser failure.",
    },
    "youtube_next": {
        "purpose": "Play the next item in the current YouTube result queue.",
        "properties": {},
        "expected_result": "A reported navigation result or honest empty-queue failure.",
    },
    "youtube_previous": {
        "purpose": "Play the previous item in the current YouTube result queue.",
        "properties": {},
        "expected_result": "A reported navigation result or honest empty-queue failure.",
    },
    "github_search": {
        "purpose": "Search GitHub using the existing browser search skill.",
        "properties": {
            "query": {"type": "string", "description": "Repository or code search terms."},
        },
        "required": ["query"],
        "expected_result": "Actual search results or a reported failure.",
    },
    "maps_open": {
        "purpose": (
            "Open Google Maps in the browser. Use for requests such as "
            "'open Google Maps' or 'open Maps'."
        ),
        "properties": {},
        "expected_result": "A reported Google Maps browser-open result or failure.",
    },
    "maps_directions": {
        "purpose": (
            "Open Google Maps driving directions. Use for destination-only "
            "requests or routes from one named place to another. Pass place "
            "names exactly as supplied; do not invent coordinates or claim "
            "live traffic or GPS verification."
        ),
        "properties": {
            "destination": {
                "type": "string",
                "description": "Required destination place name or address.",
            },
            "origin": {
                "type": "string",
                "description": "Optional starting place name or address.",
            },
        },
        "required": ["destination"],
        "expected_result": "A reported Google Maps directions browser-open result or failure.",
    },
    "translate_open": {
        "purpose": "Open Google Translate in the browser.",
        "properties": {},
        "expected_result": "A reported Google Translate browser-open result or failure.",
    },
    "browser_open_result": {
        "purpose": "Open an exact URL from the latest JARVIS search result.",
        "properties": {
            "url": {"type": "string", "description": "Exact URL returned by a prior search."},
        },
        "required": ["url"],
        "expected_result": "A reported navigation result or failure.",
    },
    "browser_read_page": {
        "purpose": "Extract text from the current browser page.",
        "properties": {
            "max_chars": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20000,
                "description": "Optional bounded extraction size.",
            },
        },
        "expected_result": "Actual extracted page text or a reported extraction failure.",
    },
}


def _registry():
    """Load the registry only when Agent Mode actually needs it."""
    from core import registry

    return registry


def build_live_capability_tool() -> dict:
    """Build a current tool declaration from the installed skill registry."""
    registry = _registry()
    # Only advertise actions with a reviewed structured schema.  A registry
    # entry alone is not enough: without a schema the model could generate an
    # arbitrary payload that the handler was never designed to accept.
    actions = sorted(
        action for action in registry.list_skills()
        if action in LIVE_CAPABILITY_SCHEMAS and registry.has_skill(action)
    )
    grouped: dict[str, list[str]] = {}
    for action in actions:
        grouped.setdefault(registry.get_skill_category(action) or "uncategorized", []).append(action)

    catalog = "; ".join(
        f"{category}: {', '.join(names)}"
        for category, names in sorted(grouped.items())
    )
    description = (
        "Execute one existing registered JARVIS capability with structured "
        "parameters. Choose this for a supported computer, browser, system, "
        "file, communication, automation, media, or information action when "
        "you can identify the capability and its parameters. The application "
        "executes the registered handler and returns the real result; never "
        "claim success from the request alone. Prefer the dedicated "
        "jarvis_capability__<action> declaration when it is available; use "
        "this generic declaration only when a dedicated declaration is not "
        "available. For ordinary conversation, "
        "questions, unsupported tasks, or dispatcher-dependent natural-language "
        "commands, do not call this tool. Available capabilities: "
        f"{catalog or 'none currently registered'}."
    )
    declarations = [
        {
                "name": "jarvis_capability",
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Exact registered capability name from the catalog.",
                            "enum": actions,
                        },
                        "parameters": {
                            "type": "object",
                            "description": (
                                "Validated capability parameters. Use the action's "
                                "existing schema and include only values supplied or "
                                "strongly implied by the user."
                            ),
                        },
                    },
                    "required": ["action"],
                },
            }
    ]

    for action, schema in LIVE_CAPABILITY_SCHEMAS.items():
        if not registry.has_skill(action):
            continue
        declarations.append(
            {
                "name": f"jarvis_capability__{action}",
                "description": (
                    f"{schema['purpose']} Use the existing registered JARVIS skill. "
                    f"Expected result: {schema['expected_result']} "
                    "Do not claim success without the returned result."
                ),
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            }
        )

    return {"function_declarations": declarations}


def build_live_memory_tool() -> dict:
    """Expose the existing durable memory service to Gemini Live."""
    return {
        "function_declarations": [
            {
                "name": "jarvis_memory",
                "description": (
                    "Use JARVIS's existing persistent personal-memory service. "
                    "Use recall for personal facts, preferences, projects, and "
                    "decisions; remember only when the user explicitly asks to "
                    "save durable information; forget only one explicitly named "
                    "memory. The result is authoritative: do not answer from "
                    "guesswork when recall returns no match."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["recall", "remember", "forget", "list"],
                        },
                        "query": {
                            "type": "string",
                            "description": "Natural-language memory question or explicit fact to save.",
                        },
                        "key": {
                            "type": "string",
                            "description": "Exact memory key for save/update/forget operations.",
                        },
                        "value": {
                            "type": "string",
                            "description": "Explicit durable value to save or update.",
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional memory category such as identity, preference, project, or decision.",
                        },
                    },
                    "required": ["operation"],
                },
            }
        ]
    }


def execute_live_memory(parameters: Any = None) -> dict:
    """Execute a bounded Live memory operation using the existing services."""
    payload = dict(parameters) if isinstance(parameters, Mapping) else {}
    operation = str(payload.get("operation", "")).strip().lower()
    if operation == "recall":
        query = str(payload.get("query", "")).strip()
        if not query:
            return {"ok": False, "status": "invalid_arguments", "message": "A memory question is required."}
        try:
            from ai.memory_answer import answer
            from ai.memory_search import search

            answer_text = answer(query)
            matches = search(query, limit=5)
            records = [
                {"key": item.key, "value": item.value, "category": item.category}
                for item in matches
            ]
            if not answer_text and not records:
                return {
                    "ok": True,
                    "status": "not_found",
                    "query": query,
                    "memories": [],
                    "message": "No stored memory matched that request. Say that you do not know.",
                }
            return {
                "ok": True,
                "status": "recalled",
                "query": query,
                "answer": answer_text or "",
                "memories": records,
                "message": answer_text or "Relevant stored memories are available in the memories field.",
            }
        except Exception as exc:
            return {"ok": False, "status": "failed", "message": "Memory recall failed safely."}

    if operation == "remember":
        key = str(payload.get("key", "")).strip()
        value = str(payload.get("value", "")).strip()
        query = str(payload.get("query", "")).strip()
        try:
            if key and value:
                from ai.memory_store import remember, get
                previous = get(key)
                remember(
                    key,
                    value,
                    category=str(payload.get("category", "other")).strip() or "other",
                )
                return {
                    "ok": True,
                    "status": "updated" if previous and previous.value != value else "remembered",
                    "key": key,
                    "value": value,
                    "message": "The durable memory was saved successfully.",
                }
            if query:
                from ai.memory_pipeline import learn
                result = learn(query)
                if result.get("saved") or result.get("already_known"):
                    return {
                        "ok": True,
                        "status": "remembered" if result.get("saved") else "already_known",
                        "key": result.get("key"),
                        "message": "The durable memory was saved successfully." if result.get("saved") else "That durable memory was already stored.",
                    }
                return {"ok": False, "status": "not_saved", "message": "The request did not contain a confirmed durable fact to save."}
            return {"ok": False, "status": "invalid_arguments", "message": "Provide an explicit key and value or a confirmed fact to remember."}
        except Exception:
            return {"ok": False, "status": "failed", "message": "Memory save failed; it was not confirmed."}

    if operation == "forget":
        key = str(payload.get("key", "")).strip()
        if not key:
            return {"ok": False, "status": "invalid_arguments", "message": "Provide one exact memory key to forget."}
        try:
            from ai.memory_store import forget, get
            existed = get(key) is not None
            forget(key)
            return {
                "ok": True,
                "status": "forgotten" if existed else "not_found",
                "key": key,
                "message": "The requested memory was deleted." if existed else "No stored memory matched that key.",
            }
        except Exception:
            return {"ok": False, "status": "failed", "message": "Memory deletion failed; no success was claimed."}

    if operation == "list":
        try:
            from ai.memory_store import list_all
            records = [
                {"key": item.key, "value": item.value, "category": item.category}
                for item in list_all()[:20]
            ]
            return {"ok": True, "status": "listed", "memories": records, "message": f"{len(records)} stored memories are available."}
        except Exception:
            return {"ok": False, "status": "failed", "message": "Memory listing failed safely."}

    return {"ok": False, "status": "invalid_arguments", "message": "Unsupported memory operation."}


def learn_live_memory(text: Any) -> dict:
    """Conservatively learn one safe durable fact from a completed Live turn."""
    sentence = " ".join(str(text or "").split()).strip()
    lowered = sentence.casefold()
    if not sentence or sentence.endswith("?"):
        return {"saved": False, "status": "ignored"}
    sensitive_markers = (
        "api key", "apikey", "token", "password", "secret", "credential",
        "private key", "access key", "one-time code", "verification code",
    )
    if any(marker in lowered for marker in sensitive_markers):
        return {"saved": False, "status": "sensitive_rejected"}
    candidate_markers = (
        "my ", "i prefer ", "i usually use ", "i always use ",
        "i use ", "my project", "we decided", "we chose", "current project",
        "project status", "project blocker", "next step",
    )
    if not any(marker in lowered for marker in candidate_markers):
        return {"saved": False, "status": "not_a_candidate"}
    uncertainty_markers = ("maybe", "might", "could be", "probably", "not sure", "i think")
    if any(marker in lowered for marker in uncertainty_markers):
        return {"saved": False, "status": "uncertain_rejected"}
    try:
        from ai.memory_ai import extract_memory
        from ai.memory_preference import extract as extract_preference
        from ai.memory_store import remember

        data = extract_memory(sentence)
        if not data or not data.get("remember"):
            data = extract_preference(sentence)
        if not data or not data.get("remember"):
            return {"saved": False, "status": "not_saved"}
        key = str(data.get("key", "")).strip()
        value = str(data.get("value", "")).strip()
        category = str(data.get("category", "other")).strip().lower() or "other"
        if not key or not value or category in {"secret", "credential", "authentication"}:
            return {"saved": False, "status": "rejected"}
        remember(
            key=key,
            value=value,
            category=category,
            keywords=str(data.get("keywords", "")),
            importance=max(1, min(int(data.get("importance", 2)), 5)),
        )
        return {"saved": True, "key": key, "status": "saved"}
    except Exception:
        return {"saved": False, "status": "failed"}


def _validate_structured_parameters(action: str, parameters: Any) -> tuple[dict[str, Any] | None, dict | None]:
    schema = LIVE_CAPABILITY_SCHEMAS.get(action)
    if schema is None:
        return None, {
            "ok": False,
            "status": "unsupported",
            "action": action,
            "message": "That capability has no reviewed structured schema.",
        }
    if not isinstance(parameters, Mapping):
        return None, {
            "ok": False,
            "status": "invalid_arguments",
            "action": action,
            "errors": ["parameters must be an object"],
            "message": "Invalid capability arguments.",
        }

    payload = dict(parameters)
    properties = schema.get("properties", {})
    errors: list[str] = []
    unknown = sorted(set(payload) - set(properties))
    if unknown:
        errors.append(f"unsupported parameter(s): {', '.join(unknown)}")
    for name in schema.get("required", []):
        value = payload.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing required parameter: {name}")

    for name, value in payload.items():
        definition = properties.get(name)
        if definition is None:
            continue
        expected = definition.get("type")
        if expected == "string" and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{name} must be a non-empty string")
        elif expected == "boolean" and not isinstance(value, bool):
            errors.append(f"{name} must be a boolean")
        elif expected == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
            errors.append(f"{name} must be an integer")
        elif expected == "array":
            if not isinstance(value, list):
                errors.append(f"{name} must be an array")
            else:
                item_definition = definition.get("items", {})
                if item_definition.get("type") == "string" and any(
                    not isinstance(item, str) or not item.strip()
                    for item in value
                ):
                    errors.append(f"{name} must contain only non-empty strings")
        if "enum" in definition and value not in definition["enum"]:
            errors.append(f"{name} must be one of: {', '.join(definition['enum'])}")
        if isinstance(value, int) and not isinstance(value, bool):
            if "minimum" in definition and value < definition["minimum"]:
                errors.append(f"{name} must be at least {definition['minimum']}")
            if "maximum" in definition and value > definition["maximum"]:
                errors.append(f"{name} must be at most {definition['maximum']}")

    if action in {"volume", "brightness"} and "direction" in payload and "percent" in payload:
        errors.append("provide either direction or percent, not both")
    if action in {"volume", "brightness"} and not ({"direction", "percent"} & set(payload)):
        errors.append("provide direction or percent")

    if errors:
        return None, {
            "ok": False,
            "status": "invalid_arguments",
            "action": action,
            "errors": errors,
            "message": "Invalid capability arguments: " + "; ".join(errors),
        }
    if schema.get("inject_action"):
        payload["action"] = action
    return payload, None


def structured_action_from_tool_name(function_name: Any) -> str | None:
    prefix = "jarvis_capability__"
    name = str(function_name or "")
    return name[len(prefix):] if name.startswith(prefix) else None


def build_live_search_tools() -> list[dict]:
    """Return semantic browser tools for the common search/follow-up flow."""
    return [
        {
            "function_declarations": [
                {
                    "name": "jarvis_search",
                    "description": (
                        "Search the web using JARVIS's existing browser search capability. "
                        "Use this for any request to search, look up, research, or find "
                        "online information. Choose provider google, youtube, or github; "
                        "google is the default. The result contains the actual titles and "
                        "URLs when the browser extracts them, so a later step can select one."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Topic or search terms."},
                            "provider": {
                                "type": "string",
                                "enum": ["google", "youtube", "github"],
                                "description": "Search provider; defaults to google.",
                            },
                        },
                        "required": ["query"],
                    },
                }
            ]
        },
        {
            "function_declarations": [
                {
                    "name": "jarvis_open_result",
                    "description": (
                        "Open one result from the immediately preceding JARVIS web search. "
                        "Use its 1-based position, or pass a URL returned by jarvis_search. "
                        "Do not invent a URL or position. Opening does not read the page; "
                        "call jarvis_read_page separately when content is needed."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "position": {"type": "integer", "description": "1-based search result position."},
                            "url": {"type": "string", "description": "Exact URL returned by the search."},
                        },
                    },
                }
            ]
        },
        {
            "function_declarations": [
                {
                    "name": "jarvis_read_page",
                    "description": (
                        "Read the current page already open in JARVIS's browser. "
                        "Use this after navigation when the user asks what the page says, "
                        "requests a summary, or needs details from the page. The tool "
                        "returns only text actually extracted from the page, with URL, "
                        "title, extraction status, and a size-limited content field. "
                        "An opened page is not automatically a read page; if extraction "
                        "fails or is empty, explain that and do not invent a summary."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "max_chars": {
                                "type": "integer",
                                "description": "Optional content limit, capped by JARVIS.",
                            },
                        },
                    },
                }
            ]
        },
    ]


def _display_result(value: Any) -> str | None:
    """Convert a handler result into useful model-facing text."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (dict, list, tuple)):
        return repr(value)
    return str(value)


def _diagnostic_error_category(status: Any, *, exception: BaseException | None = None) -> str | None:
    """Return a low-cardinality, non-sensitive diagnostic outcome category."""
    if status in {"invalid_arguments", "invalid_request", "unsupported", "failed", "no_result"}:
        return str(status)
    if exception is not None:
        return "handler_exception"
    return None


def _safe_diagnostic_name(value: Any) -> str:
    """Keep model-controlled names out of diagnostic output unless identifier-like."""
    name = str(value or "")
    if len(name) <= 80 and re.fullmatch(r"[A-Za-z0-9_.:-]+", name):
        return name
    return "<redacted>"


def _safe_diagnostic_result(result: Any) -> dict[str, Any]:
    """Keep diagnostics useful without copying arbitrary handler payloads."""
    if not isinstance(result, Mapping):
        return {
            "result_type": type(result).__name__,
            "result_ok": bool(result) if result is not None else False,
        }

    status = result.get("status")
    safe = {
        "result_type": "mapping",
        "result_ok": result.get("ok") if isinstance(result.get("ok"), bool) else None,
        "result_status": _safe_diagnostic_name(status) if status is not None else None,
        "authoritative": bool(result.get("authoritative", False)),
        "field_names": [_safe_diagnostic_name(key) for key in list(result.keys())[:32]],
    }
    error_category = _diagnostic_error_category(status)
    if error_category:
        safe["error_category"] = error_category
    return safe


def _volume_status_reading(action: str, parameters: Mapping[str, Any]) -> int | None:
    """Read the endpoint for diagnostics only; never affect capability execution."""
    if action != "volume" or str(parameters.get("direction", "")).strip().lower() != "status":
        return None
    try:
        from skills.system.volume import current

        reading = current()
        return int(reading) if isinstance(reading, int) and not isinstance(reading, bool) else None
    except Exception:
        return None


def _file_result_payload(action: str, raw: Any) -> dict[str, Any] | None:
    """Preserve file list/search results as structured Live data."""
    if action not in {"file_list", "file_search"} or not isinstance(raw, list):
        return None

    items = []
    for item in raw:
        if action == "file_list" and isinstance(item, Mapping):
            # Inventory responses need metadata, not the full extracted file
            # body that the underlying index may retain.
            items.append({key: value for key, value in item.items() if key != "text"})
        else:
            items.append(item)
    status = "no_results" if not items else "reported_success"
    noun = "registered file" if action == "file_list" else "file search result"
    return {
        "ok": True,
        "status": status,
        "action": action,
        "data_source": "registered_handler",
        "empty": not bool(items),
        "items": items,
        "count": len(items),
        "message": f"{len(items)} {noun}{'' if len(items) == 1 else 's'} returned.",
    }


def _list_result_payload(action: str, raw: Any) -> dict[str, Any] | None:
    """Preserve legacy list returns while giving Live a structured payload."""
    if action != "list_schedules" or not isinstance(raw, list):
        return None
    return {
        "ok": True,
        "status": "no_results" if not raw else "reported_success",
        "action": action,
        "items": raw,
        "count": len(raw),
    }


def _emit_live_diagnostic(
    event: str,
    *,
    action: str,
    parameters: Mapping[str, Any] | None = None,
    started: float | None = None,
    result: Any = None,
    status: str | None = None,
    exception: BaseException | None = None,
    volume_reading: int | None = None,
) -> None:
    """Emit bounded Agent diagnostics without ever becoming part of execution."""
    try:
        fields: dict[str, Any] = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": _safe_diagnostic_name(action),
            "parameter_names": [_safe_diagnostic_name(key) for key in list((parameters or {}).keys())[:32]],
        }
        if started is not None:
            fields["duration_ms"] = round((perf_counter() - started) * 1000, 2)
        if result is not None:
            fields.update(_safe_diagnostic_result(result))
        if status is not None:
            fields["status"] = status
            error_category = _diagnostic_error_category(status, exception=exception)
            if error_category:
                fields["error_category"] = error_category
        if exception is not None:
            fields["exception_type"] = _safe_diagnostic_name(type(exception).__name__)
        if volume_reading is not None:
            fields["volume_endpoint_percent"] = volume_reading
        debug_print("[LIVE DIAGNOSTIC]", fields)
    except Exception:
        # Diagnostics must never interfere with a Live tool or session.
        return


def execute_live_capability(
    action: Any,
    parameters: Any = None,
    *,
    executor: Callable[[str, Mapping[str, Any]], Any] | None = None,
    invocation_id: Any = None,
) -> dict:
    """Validate and execute one registered skill without registry fallback.

    The normal registry intentionally has an AI fallback for legacy callers.
    Agent Mode must not silently turn an invalid model action into an unrelated
    fallback request, so unknown actions are rejected before execution.
    """
    started = perf_counter()
    action_name = str(action or "").strip()
    payload_for_diagnostics = parameters if isinstance(parameters, Mapping) else {}
    _emit_live_diagnostic(
        "invocation",
        action=action_name,
        parameters=payload_for_diagnostics,
    )
    payload, validation_error = _validate_structured_parameters(action_name, parameters)
    if validation_error:
        _emit_live_diagnostic(
            "completion",
            action=action_name,
            parameters=payload_for_diagnostics,
            started=started,
            result=validation_error,
            status=validation_error.get("status"),
        )
        return validation_error
    payload = payload or {}
    if action_name in {"create_reminder", "screen_vision_analyze"} and invocation_id:
        payload = dict(payload)
        payload["_invocation_id" if action_name == "create_reminder" else "_live_request_id"] = str(invocation_id)

    if not action_name:
        result = {"ok": False, "status": "invalid_request", "message": "No capability was provided."}
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=result, status=result["status"],
        )
        return result
    registry = _registry()
    if not registry.has_skill(action_name):
        result = {
            "ok": False,
            "status": "unsupported",
            "action": action_name,
            "message": "That capability is not registered in JARVIS.",
        }
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=result, status=result["status"],
        )
        return result

    try:
        raw = (executor or registry.execute)(action_name, payload)
    except Exception as exc:
        result = {
            "ok": False,
            "status": "failed",
            "action": action_name,
            "message": str(exc),
        }
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=result, status=result["status"], exception=exc,
            volume_reading=_volume_status_reading(action_name, payload),
        )
        return result

    rendered = _display_result(raw)
    if raw is False:
        result = {"ok": False, "status": "failed", "action": action_name, "message": rendered or "The capability reported failure."}
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=result, status=result["status"],
            volume_reading=_volume_status_reading(action_name, payload),
        )
        return result

    authoritative = " ".join(
        text.strip() for text in get_live_responses() if text and text.strip()
    )
    if authoritative:
        result = {
            "ok": True,
            "status": "reported_success",
            "action": action_name,
            "authoritative": True,
            "message": authoritative,
        }
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=result, status=result["status"],
            volume_reading=_volume_status_reading(action_name, payload),
        )
        return result
    if isinstance(raw, dict):
        structured = dict(raw)
        structured.setdefault("action", action_name)
        # Some existing skills return a meaningful payload without an explicit
        # success field. A non-empty payload is evidence of a reported result;
        # explicit ``ok: False`` remains a failure.
        structured.setdefault("ok", bool(structured))
        structured.setdefault(
            "status",
            "reported_success" if structured.get("ok") else "failed",
        )
        structured.setdefault("message", rendered or "")
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=structured, status=structured.get("status"),
            volume_reading=_volume_status_reading(action_name, payload),
        )
        return structured
    file_result = _file_result_payload(action_name, raw)
    if file_result is not None:
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=file_result, status=file_result["status"],
            volume_reading=_volume_status_reading(action_name, payload),
        )
        return file_result
    list_result = _list_result_payload(action_name, raw)
    if list_result is not None:
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=list_result, status=list_result["status"],
        )
        return list_result
    if rendered:
        result = {"ok": True, "status": "reported_success", "action": action_name, "message": rendered}
        _emit_live_diagnostic(
            "completion", action=action_name, parameters=payload_for_diagnostics,
            started=started, result=result, status=result["status"],
            volume_reading=_volume_status_reading(action_name, payload),
        )
        return result
    result = {
        "ok": False,
        "status": "no_result",
        "action": action_name,
        "message": "The capability ran but returned no result, so completion could not be verified.",
    }
    _emit_live_diagnostic(
        "completion", action=action_name, parameters=payload_for_diagnostics,
        started=started, result=result, status=result["status"],
        volume_reading=_volume_status_reading(action_name, payload),
    )
    return result


def execute_live_search(query: Any, provider: Any = "google") -> dict:
    """Execute an existing search skill and return its real browser context."""
    query_text = str(query or "").strip()
    provider_name = str(provider or "").strip().lower()

    # Gemini occasionally omits the optional provider field even when the
    # user's natural-language query names one. Preserve the explicit provider
    # instead of silently sending a YouTube request to Google's default path.
    if not provider_name:
        provider_name, query_text = _infer_search_provider(query_text)
    provider_name = provider_name or "google"
    actions = {
        "google": "google_search",
        "youtube": "youtube_search",
        "github": "github_search",
    }
    if not query_text:
        return {"ok": False, "status": "invalid_request", "message": "A search query is required."}
    action = actions.get(provider_name)
    if not action:
        return {"ok": False, "status": "unsupported", "message": f"Unsupported search provider: {provider_name}."}

    result = execute_live_capability(action, {"query": query_text})
    if not result.get("ok"):
        return result

    try:
        from core.browser_context import browser_context

        snapshot = browser_context.search_snapshot()
        results = snapshot["results"]
        result["results"] = results
        result["search_context"] = {
            "query": snapshot["query"],
            "platform": snapshot["platform"],
            "result_count": len(results),
        }
        result["message"] = (
            f"Search completed with {len(results)} result(s)."
            if results
            else "The search action completed, but no result metadata was extracted."
        )
    except Exception as exc:
        result["results"] = []
        result["message"] = f"Search completed, but result metadata was unavailable: {exc}"
    return result


def _infer_search_provider(query: str) -> tuple[str, str]:
    """Infer only an explicitly named provider from a natural-language query."""
    normalized = str(query or "").strip()
    lowered = normalized.lower()
    prefixes = (
        ("youtube", "search youtube for "),
        ("youtube", "search youtube "),
        ("youtube", "search on youtube for "),
        ("youtube", "search on youtube "),
        ("google", "search google for "),
        ("google", "search google "),
        ("github", "search github for "),
        ("github", "search github "),
    )
    for provider, prefix in prefixes:
        if lowered.startswith(prefix):
            return provider, normalized[len(prefix):].strip()
    return "", normalized


def execute_live_open_result(position: Any = None, url: Any = None) -> dict:
    """Resolve and open a result from the latest valid search context."""
    from core.browser_context import browser_context

    snapshot = browser_context.search_snapshot()
    results = snapshot["results"]
    if not results:
        return {
            "ok": False,
            "status": "stale_result_context",
            "message": "No valid prior search result is available. Please search again first.",
        }
    target_url = ""
    selected_position = None

    # A position is stronger evidence than a duplicated URL supplied by the
    # model. Resolve it against the stored ordered result list first.
    if position is not None:
        try:
            selected_position = int(position)
        except (TypeError, ValueError):
            return {"ok": False, "status": "invalid_request", "message": "Result position must be an integer."}
        if selected_position < 1 or selected_position > len(results):
            return {
                "ok": False,
                "status": "stale_result_context",
                "message": "That search-result position is no longer available. Please search again or specify which result you mean.",
                "search_context": {
                    "query": snapshot["query"],
                    "platform": snapshot["platform"],
                    "result_count": len(results),
                },
            }
        target = results[selected_position - 1]
        target_url = str(target.get("url", "")).strip()
    elif url:
        candidate = str(url).strip()
        matches = [item for item in results if item.get("url") == candidate]
        if results and not matches:
            return {
                "ok": False,
                "status": "ambiguous_result",
                "message": "That URL is not in the latest search results. Please choose a numbered result from the latest search.",
                "search_context": {
                    "query": snapshot["query"],
                    "platform": snapshot["platform"],
                    "result_count": len(results),
                },
            }
        target_url = candidate
    if not target_url:
        return {
            "ok": False,
            "status": "stale_result_context",
            "message": "No valid prior search result is available. Please search again first.",
        }

    if browser_context.current_url.rstrip("/") == target_url.rstrip("/"):
        return {
            "ok": True,
            "status": "already_open",
            "opened": False,
            "url": target_url,
            "position": selected_position,
            "search_context": {
                "query": snapshot["query"],
                "platform": snapshot["platform"],
                "result_count": len(results),
            },
            "page_content": {
                "available": False,
                "reason": "The page is open but has not been read; call jarvis_read_page to extract content.",
            },
            "message": "That result is already the current page; it was not opened again.",
        }

    result = execute_live_capability("browser_open_result", {"url": target_url})
    result["url"] = target_url
    result["opened"] = bool(result.get("ok"))
    if selected_position is not None:
        result["position"] = selected_position
    result["search_context"] = {
        "query": snapshot["query"],
        "platform": snapshot["platform"],
        "result_count": len(results),
    }
    result["page_content"] = {
        "available": False,
        "reason": "The page is open but has not been read; call jarvis_read_page to extract content.",
    }
    if result.get("ok"):
        result["status"] = "opened"
        result["message"] = (
            "The result page opened successfully, but page content was not extracted."
        )
    return result


def execute_live_read_page(parameters: Any = None) -> dict:
    """Read the current page through the existing registered browser skill."""
    payload = parameters if isinstance(parameters, Mapping) else {}
    return execute_live_capability("browser_read_page", payload)
