"""Safe, reusable click and type capabilities for supported desktop apps.

Browser pages are handled through the existing Playwright controller. Native
Windows applications use UI Automation through pywinauto; coordinate clicks
are only performed after a unique control has been resolved.
"""

from __future__ import annotations

import re
import threading
from typing import Any

from core.registry import register


_EDIT_TYPES = {"edit", "document", "combobox", "autocomplete"}
_CLICK_TYPES = {"button", "tabitem", "menuitem", "hyperlink", "listitem", "checkbox", "radiobutton"}
_CLICKABLE_TYPES = _EDIT_TYPES | _CLICK_TYPES
_EDITOR_CLASS_HINTS = {"edit", "richedit", "rich edit", "notepad", "document", "text", "editor", "scintilla"}
_NATIVE_EDITOR_LOCK = threading.RLock()
_LAST_NATIVE_EDITOR: dict[str, Any] | None = None


def _normalise(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def _tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _normalise(value)))


def _result(action: str, status: str, message: str, **fields: Any) -> dict[str, Any]:
    return {"ok": status in {"completed", "already_present"}, "status": status, "action": action, "message": message, **fields}


def _browser_controller():
    from skills.browser.browser_controller import browser

    return browser


def _native_desktop():
    from pywinauto import Desktop

    return Desktop(backend="uia")


def _native_active_window(desktop: Any, application: str = "") -> tuple[Any | None, dict[str, Any]]:
    """Resolve the current foreground UIA window without using Desktop.get_active()."""

    try:
        windows = desktop.windows(visible_only=True, enabled_only=True)
    except Exception as exc:
        return None, {"status": "automation_unavailable", "reason": type(exc).__name__}

    requested = _normalise(application)
    if requested:
        requested_tokens = _tokens(requested)
        matches = []
        for window in windows:
            info = _control_info(window)
            title_tokens = _tokens(info.get("name", ""))
            if requested in _normalise(info.get("name", "")) or requested_tokens <= title_tokens:
                matches.append(window)
        if not matches:
            return None, {"status": "application_not_found", "application": application}
        if len(matches) > 1:
            return None, {"status": "ambiguous_application", "application": application}
        return matches[0], {}

    try:
        import win32gui

        foreground = int(win32gui.GetForegroundWindow() or 0)
    except Exception:
        foreground = 0

    if foreground:
        for window in windows:
            try:
                if int(getattr(window.element_info, "handle", 0) or 0) == foreground:
                    return window, {}
            except Exception:
                continue

    if len(windows) == 1:
        return windows[0], {}
    if len(windows) > 1:
        return None, {"status": "application_not_focused", "message": "The active application could not be identified."}
    return None, {"status": "application_not_focused", "message": "No visible enabled Windows application is available."}


def _control_info(control: Any) -> dict[str, Any]:
    try:
        info = control.element_info
        return {
            "name": str(getattr(info, "name", "") or ""),
            "automation_id": str(getattr(info, "automation_id", "") or ""),
            "control_type": str(getattr(info, "control_type", "") or ""),
            "class_name": str(getattr(info, "class_name", "") or ""),
        }
    except Exception:
        return {"name": "", "automation_id": "", "control_type": "", "class_name": ""}


def _native_candidates(window: Any, target: str, action: str) -> list[tuple[float, Any]]:
    wanted = _normalise(target)
    wanted_tokens = _tokens(wanted)
    candidates: list[tuple[float, Any]] = []
    try:
        controls = [window, *window.descendants()]
    except Exception:
        controls = [window]

    for control in controls:
        info = _control_info(control)
        control_type = _normalise(info["control_type"])
        if action == "type" and control_type not in _EDIT_TYPES:
            continue
        if action == "click" and control_type not in _CLICKABLE_TYPES:
            continue
        try:
            if not control.is_visible() or not control.is_enabled():
                continue
        except Exception:
            continue

        haystack = _normalise(" ".join(info.values()))
        haystack_tokens = _tokens(haystack)
        score = 0.0
        if wanted and wanted in haystack:
            score += 50
        score += len(wanted_tokens & haystack_tokens) * 10
        if wanted_tokens and wanted_tokens <= haystack_tokens:
            score += 25
        hint_tokens = _tokens(wanted)
        if action == "type" and hint_tokens & {"search", "field", "box", "input", "text", "message", "composer"}:
            if control_type in _EDIT_TYPES:
                score += 18
        if action == "click" and hint_tokens & {"search", "field", "box", "input", "text", "message", "composer", "editing", "area", "document"}:
            if control_type in _EDIT_TYPES:
                score += 18
        if action == "click" and hint_tokens & {"button", "tab", "menu", "send", "settings"}:
            if control_type in _CLICK_TYPES:
                score += 18
        if score > 0:
            candidates.append((score, control))

    return sorted(candidates, key=lambda item: item[0], reverse=True)


def _active_native_control(window: Any) -> Any | None:
    try:
        from pywinauto.controls.uiawrapper import UIAWrapper
        from pywinauto.uia_element_info import IUIA, UIAElementInfo

        focused = UIAWrapper(UIAElementInfo(IUIA().get_focused_element()))
        window_process = getattr(window.element_info, "process_id", 0)
        focused_process = getattr(focused.element_info, "process_id", 0)
        if window_process and focused_process and window_process != focused_process:
            return None
        return focused
    except Exception:
        return None


def _is_editable_native_control(control: Any) -> bool:
    info = _control_info(control)
    if _normalise(info.get("control_type")) in _EDIT_TYPES:
        return True
    try:
        if not control.is_keyboard_focusable():
            return False
    except Exception:
        return False
    descriptor = _normalise(" ".join((info.get("name", ""), info.get("class_name", ""))))
    return any(hint in descriptor for hint in _EDITOR_CLASS_HINTS)


def _clear_native_editor() -> None:
    global _LAST_NATIVE_EDITOR
    with _NATIVE_EDITOR_LOCK:
        _LAST_NATIVE_EDITOR = None


def _has_retained_native_editor() -> bool:
    with _NATIVE_EDITOR_LOCK:
        return bool(_LAST_NATIVE_EDITOR and _LAST_NATIVE_EDITOR.get("editor"))


def _remember_native_editor(editor: Any, window: Any) -> None:
    global _LAST_NATIVE_EDITOR
    if not editor or not _is_editable_native_control(editor):
        return
    try:
        window_info = window.element_info
        editor_info = editor.element_info
        owner_process = int(getattr(window_info, "process_id", 0) or 0)
        owner_handle = int(getattr(window_info, "handle", 0) or 0)
        editor_process = int(getattr(editor_info, "process_id", 0) or 0)
    except Exception:
        return
    if owner_process and editor_process and owner_process != editor_process:
        return
    with _NATIVE_EDITOR_LOCK:
        _LAST_NATIVE_EDITOR = {
            "editor": editor,
            "owner_process": owner_process or editor_process,
            "owner_handle": owner_handle,
        }


def _retained_native_editor(window: Any) -> Any | None:
    with _NATIVE_EDITOR_LOCK:
        state = dict(_LAST_NATIVE_EDITOR or {})
    editor = state.get("editor")
    if not editor:
        return None
    try:
        window_info = window.element_info
        editor_info = editor.element_info
        owner_process = int(getattr(window_info, "process_id", 0) or 0)
        editor_process = int(getattr(editor_info, "process_id", 0) or 0)
        if state.get("owner_process") and owner_process and state["owner_process"] != owner_process:
            _clear_native_editor()
            return None
        if owner_process and editor_process and owner_process != editor_process:
            _clear_native_editor()
            return None
        if not _is_editable_native_control(editor) or not editor.is_visible() or not editor.is_enabled():
            _clear_native_editor()
            return None
        return editor
    except Exception:
        _clear_native_editor()
        return None


def _focus_native_editor(editor: Any, window: Any) -> Any | None:
    try:
        editor.set_focus()
    except Exception:
        return None
    focused = _active_native_control(window)
    if focused and _is_editable_native_control(focused):
        _remember_native_editor(focused, window)
        return focused
    return None


def _native_click(target: str, application: str = "", window: Any | None = None) -> dict[str, Any]:
    try:
        desktop = _native_desktop()
        if window is None:
            window, window_error = _native_active_window(desktop, application)
            if window is None:
                return _result("desktop_click", window_error.get("status", "application_not_focused"), window_error.get("message", "The intended application is not available."), target=target, **{key: value for key, value in window_error.items() if key not in {"status", "message"}})
        candidates = _native_candidates(window, target, "click")
    except ImportError:
        return _result("desktop_click", "automation_unavailable", "Windows UI Automation dependencies are unavailable.", target=target)
    except Exception as exc:
        return _result("desktop_click", "automation_unavailable", "Windows UI Automation could not initialize.", target=target, reason=type(exc).__name__)

    if not candidates:
        return _result("desktop_click", "target_not_found", "I could not find that control in the active application.", target=target, application=application)
    if len(candidates) > 1 and candidates[0][0] - candidates[1][0] < 12:
        return _result("desktop_click", "ambiguous_target", "More than one control matches that description.", target=target, application=application)

    control = candidates[0][1]
    try:
        control.click_input()
        try:
            control.set_focus()
        except Exception:
            pass
        if _is_editable_native_control(control):
            focused = _active_native_control(window)
            if focused and _is_editable_native_control(focused):
                _remember_native_editor(focused, window)
                verification = "editable control clicked and focus verified"
            else:
                _remember_native_editor(control, window)
                verification = "editable control click completed; focus will be revalidated before typing"
        else:
            _clear_native_editor()
            verification = "unique accessible control resolved and click completed"
        return _result("desktop_click", "completed", "The requested control was clicked.", target=target, verification=verification)
    except Exception:
        _clear_native_editor()
        return _result("desktop_click", "click_failed", "The control was found, but the click could not be completed.", target=target, application=application)


def desktop_click(data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = data if isinstance(data, dict) else {}
    target = str(payload.get("target", "")).strip()
    application = str(payload.get("application", "")).strip()
    if not target:
        return _result("desktop_click", "invalid_arguments", "A visible control description is required.")

    try:
        browser = _browser_controller()
        browser_result = browser.click_target(target)
        if isinstance(browser_result, dict) and browser_result.get("status") not in {"browser_unavailable", "unavailable"}:
            _clear_native_editor()
            return browser_result
    except Exception:
        pass
    return _native_click(target, application)


def _native_type(text: str, target: str = "", application: str = "") -> dict[str, Any]:
    try:
        desktop = _native_desktop()
    except ImportError:
        return _result("desktop_type", "automation_unavailable", "Windows UI Automation dependencies are unavailable.", target=target)
    except Exception as exc:
        return _result("desktop_type", "automation_unavailable", "Windows UI Automation could not initialize.", target=target, reason=type(exc).__name__)

    try:
        window, window_error = _native_active_window(desktop, application)
        if window is None:
            return _result("desktop_type", window_error.get("status", "application_not_focused"), window_error.get("message", "The intended application is not available."), target=target, **{key: value for key, value in window_error.items() if key not in {"status", "message"}})
        if not application and "jarvis ultra" in _normalise(_control_info(window).get("name", "")):
            return _result("desktop_type", "unsupported_target", "The JARVIS ULTRA HUD is not a typing destination.", target=target)
        if target:
            clicked = _native_click(target, application, window)
            if not clicked.get("ok"):
                return _result("desktop_type", clicked.get("status", "failed"), clicked.get("message", "The target field could not be focused."), target=target)
            focused = _active_native_control(window)
            if not focused or not _is_editable_native_control(focused):
                retained = _retained_native_editor(window)
                focused = _focus_native_editor(retained, window) if retained else None
        else:
            focused = _active_native_control(window)
            if focused and _is_editable_native_control(focused):
                _remember_native_editor(focused, window)
            else:
                focused_type = _normalise(_control_info(focused).get("control_type")) if focused else ""
                if focused_type in _CLICK_TYPES:
                    _clear_native_editor()
                    return _result("desktop_type", "unsupported_target", "The current focus is not an editable text surface.", target=target, application=application)
                retained = _retained_native_editor(window)
                focused = _focus_native_editor(retained, window) if retained else None
        info = _control_info(focused) if focused is not None else {}
        if not focused or not _is_editable_native_control(focused):
            _clear_native_editor()
            return _result("desktop_type", "unsupported_target", "The intended text field is not focused or is not editable.", target=target, application=application)
        try:
            focused.set_focus()
        except Exception as exc:
            return _result("desktop_type", "focus_failed", "The intended text field could not receive focus.", target=target, reason=type(exc).__name__)

        import pyperclip
        from pywinauto.keyboard import send_keys

        previous_clipboard = pyperclip.paste()
        try:
            pyperclip.copy(text)
            send_keys("^v")
        finally:
            pyperclip.copy(previous_clipboard)
        return _result("desktop_type", "completed", "The exact text was entered into the focused field.", target=target, application=application, characters=len(text), verification="editable control focused and paste completed")
    except ImportError:
        return _result("desktop_type", "automation_unavailable", "Windows keyboard automation dependencies are unavailable.", target=target)
    except Exception as exc:
        return _result("desktop_type", "type_failed", "The text could not be entered into the intended field.", target=target, reason=type(exc).__name__)


def desktop_type(data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = data if isinstance(data, dict) else {}
    text = payload.get("text")
    target = str(payload.get("target", "")).strip()
    application = str(payload.get("application", "")).strip()
    if not isinstance(text, str) or not text:
        return _result("desktop_type", "invalid_arguments", "Exact non-empty text is required.", target=target)

    if not target and _has_retained_native_editor():
        return _native_type(text, target, application)

    try:
        browser = _browser_controller()
        browser_result = browser.type_text(text, target=target)
        if isinstance(browser_result, dict) and browser_result.get("status") not in {"browser_unavailable", "unavailable"}:
            return browser_result
    except Exception:
        pass
    return _native_type(text, target, application)


register("desktop_click", desktop_click, category="desktop_control")
register("desktop_type", desktop_type, category="desktop_control")
