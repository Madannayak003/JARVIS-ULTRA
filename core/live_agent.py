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
    "taskmanager": {
        "purpose": "Report current CPU, memory, and disk usage.",
        "properties": {},
        "expected_result": "A real system-usage response or a reported failure.",
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
    "youtube_search": {
        "purpose": "Search YouTube using the existing browser search skill.",
        "properties": {
            "query": {"type": "string", "description": "Video or channel search terms."},
        },
        "required": ["query"],
        "expected_result": "Actual search results or a reported failure.",
    },
    "github_search": {
        "purpose": "Search GitHub using the existing browser search skill.",
        "properties": {
            "query": {"type": "string", "description": "Repository or code search terms."},
        },
        "required": ["query"],
        "expected_result": "Actual search results or a reported failure.",
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
        "claim success from the request alone. For ordinary conversation, "
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

    rendered = _display_result(raw)
    if raw is False:
        result = {"ok": False, "status": "failed", "action": action_name, "message": rendered or "The capability reported failure."}
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
