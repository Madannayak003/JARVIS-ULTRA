import unittest
from unittest.mock import Mock, patch

from skills.desktop_control.desktop_controls import (
    _native_click,
    _clear_native_editor,
    _native_desktop,
    _native_type,
    _is_editable_native_control,
    desktop_click,
    desktop_type,
)
from skills.browser.browser_controller import BrowserController


class _FakeBrowserElement:
    def __init__(self, data, value=""):
        self.data = data
        self.value = value
        self.clicked = False
        self.filled = None

    def evaluate(self, script):
        if "'value' in node" in script:
            return True
        return self.data

    def click(self, timeout=0):
        self.clicked = True

    def count(self):
        return 1

    def input_value(self):
        return self.value

    def fill(self, value):
        self.filled = value
        self.value = value

    def press_sequentially(self, value):
        self.fill(value)


class _FakeBrowserLocator:
    def __init__(self, elements):
        self.elements = elements

    def all(self):
        return self.elements

    @property
    def first(self):
        return self.elements[0]


class _FakeBrowserPage:
    def __init__(self, elements):
        self.elements = elements

    def is_closed(self):
        return False

    def locator(self, selector):
        return _FakeBrowserLocator(self.elements)

    def wait_for_timeout(self, _milliseconds):
        return None


class DesktopInteractionTests(unittest.TestCase):
    def setUp(self):
        _clear_native_editor()

    def tearDown(self):
        _clear_native_editor()

    def test_click_routes_to_existing_browser_controller(self):
        browser = Mock()
        browser.click_target.return_value = {
            "ok": True,
            "status": "completed",
            "action": "desktop_click",
            "target": "search box",
        }
        with patch("skills.desktop_control.desktop_controls._browser_controller", return_value=browser):
            result = desktop_click({"target": "search box"})
        self.assertEqual(result["status"], "completed")
        browser.click_target.assert_called_once_with("search box")

    def test_type_preserves_exact_multiline_text_and_does_not_repeat_verified_input(self):
        browser = Mock()
        text = "Line 1, exactly.\nLine 2 — keep spacing."
        browser.type_text.return_value = {
            "ok": True,
            "status": "already_present",
            "action": "desktop_type",
            "characters": len(text),
        }
        with patch("skills.desktop_control.desktop_controls._browser_controller", return_value=browser):
            result = desktop_type({"target": "message field", "text": text})
        self.assertEqual(result["status"], "already_present")
        browser.type_text.assert_called_once_with(text, target="message field")

    def test_missing_target_and_text_are_reported_without_ui_access(self):
        with patch("skills.desktop_control.desktop_controls._browser_controller") as browser:
            self.assertEqual(desktop_click({})["status"], "invalid_arguments")
            self.assertEqual(desktop_type({"text": ""})["status"], "invalid_arguments")
            browser.assert_not_called()

    def test_browser_ambiguity_is_not_replaced_by_native_guess(self):
        browser = Mock()
        browser.click_target.return_value = {
            "ok": False,
            "status": "ambiguous",
            "action": "desktop_click",
            "target": "settings",
        }
        with patch("skills.desktop_control.desktop_controls._browser_controller", return_value=browser), patch(
            "skills.desktop_control.desktop_controls._native_click"
        ) as native_click:
            result = desktop_click({"target": "settings"})
        self.assertEqual(result["status"], "ambiguous")
        native_click.assert_not_called()

    def test_native_click_requires_and_uses_one_resolved_control(self):
        control = Mock()
        control.element_info.name = "Settings"
        control.element_info.automation_id = "settingsTab"
        control.element_info.control_type = "TabItem"
        control.element_info.class_name = "Tab"
        control.is_visible.return_value = True
        control.is_enabled.return_value = True
        window = Mock()
        window.element_info.name = "Test App"
        window.element_info.automation_id = ""
        window.element_info.control_type = "Window"
        window.element_info.class_name = "Window"
        window.descendants.return_value = [control]
        desktop = Mock()
        desktop.windows.return_value = [window]
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=desktop):
            result = _native_click("Settings tab")
        self.assertEqual(result["status"], "completed")
        control.click_input.assert_called_once_with()

    def test_file_menu_click_reports_only_the_verified_click(self):
        menu = Mock()
        menu.element_info.name = "File"
        menu.element_info.automation_id = "File"
        menu.element_info.control_type = "MenuItem"
        menu.element_info.class_name = "MenuItem"
        menu.is_visible.return_value = True
        menu.is_enabled.return_value = True
        window = Mock()
        window.element_info.name = "Notepad"
        window.descendants.return_value = [menu]
        desktop = Mock()
        desktop.windows.return_value = [window]

        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=desktop):
            result = _native_click("File")

        self.assertEqual(result["status"], "completed")
        self.assertIn("click completed", result["verification"])
        menu.click_input.assert_called_once_with()

    def test_uia_backend_can_enumerate_top_level_windows(self):
        desktop = _native_desktop()
        windows = desktop.windows(visible_only=True, enabled_only=True)
        self.assertIsInstance(windows, list)

    def test_uia_initialization_failure_has_precise_status(self):
        with patch("skills.desktop_control.desktop_controls._native_desktop", side_effect=RuntimeError("backend init")):
            result = _native_click("Settings button")
        self.assertEqual(result["status"], "automation_unavailable")
        self.assertEqual(result["reason"], "RuntimeError")

        with patch("skills.desktop_control.desktop_controls._native_desktop", side_effect=RuntimeError("backend init")):
            type_result = _native_type("safe test")
        self.assertEqual(type_result["status"], "automation_unavailable")
        self.assertEqual(type_result["reason"], "RuntimeError")

    def test_ambiguous_native_target_is_not_clicked(self):
        controls = []
        for _ in range(2):
            control = Mock()
            control.element_info.name = "Settings"
            control.element_info.automation_id = "settingsTab"
            control.element_info.control_type = "TabItem"
            control.element_info.class_name = "Tab"
            control.is_visible.return_value = True
            control.is_enabled.return_value = True
            controls.append(control)
        window = Mock()
        window.element_info.name = "Test App"
        window.descendants.return_value = controls
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=Mock()), patch(
            "skills.desktop_control.desktop_controls._native_active_window", return_value=(window, {})
        ):
            result = _native_click("Settings tab")
        self.assertEqual(result["status"], "ambiguous_target")
        for control in controls:
            control.click_input.assert_not_called()

    def test_native_editable_control_receives_exact_unicode_multiline_text(self):
        edit = Mock()
        edit.element_info.control_type = "Edit"
        edit.element_info.name = "Message"
        edit.element_info.automation_id = "message"
        edit.element_info.class_name = "Edit"
        edit.window_text.return_value = ""
        window = Mock()
        window.element_info.name = "Test App"
        window.get_focus.return_value = edit
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=Mock()), patch(
            "skills.desktop_control.desktop_controls._native_active_window", return_value=(window, {})
        ), patch("skills.desktop_control.desktop_controls._active_native_control", return_value=edit), patch(
            "pyperclip.paste", return_value=""
        ), patch("pyperclip.copy"), patch(
            "pywinauto.keyboard.send_keys"
        ) as send_keys:
            result = _native_type("Hello, 世界\nKeep this exact.", application="Test App")
        self.assertEqual(result["status"], "completed")
        send_keys.assert_called_once_with("^v")

    def test_document_control_and_unnamed_editor_pattern_are_supported(self):
        document = Mock()
        document.element_info.control_type = "Document"
        document.element_info.name = ""
        document.element_info.class_name = "RichEditD2DPT"
        self.assertTrue(_is_editable_native_control(document))

    def test_focused_non_editor_is_rejected(self):
        button = Mock()
        button.element_info.control_type = "Button"
        button.element_info.name = "Open"
        button.element_info.class_name = "Button"
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=Mock()), patch(
            "skills.desktop_control.desktop_controls._native_active_window", return_value=(Mock(), {})
        ), patch("skills.desktop_control.desktop_controls._active_native_control", return_value=button):
            result = _native_type("safe test")
        self.assertEqual(result["status"], "unsupported_target")

    def test_hud_is_never_used_as_default_typing_destination(self):
        hud = Mock()
        hud.element_info.name = "JARVIS ULTRA"
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=Mock()), patch(
            "skills.desktop_control.desktop_controls._native_active_window", return_value=(hud, {})
        ):
            result = _native_type("safe test")
        self.assertEqual(result["status"], "unsupported_target")

    def test_unknown_application_is_not_typed_into(self):
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=Mock()), patch(
            "skills.desktop_control.desktop_controls._native_active_window",
            return_value=(None, {"status": "application_not_found", "application": "Unknown App"}),
        ):
            result = _native_type("safe test", application="Unknown App")
        self.assertEqual(result["status"], "application_not_found")

    def test_click_followed_by_multiple_native_typing_operations_keeps_verified_focus(self):
        editor = Mock()
        editor.element_info.control_type = "Edit"
        editor.element_info.name = "Document"
        editor.element_info.class_name = "RichEdit"
        editor.element_info.process_id = 42
        editor.element_info.handle = 100
        editor.is_keyboard_focusable.return_value = True
        editor.is_visible.return_value = True
        editor.is_enabled.return_value = True
        editor.window_text.side_effect = ["", "same text"]
        window = Mock()
        window.element_info.name = "Notepad"
        window.element_info.process_id = 42
        window.element_info.handle = 100
        window.descendants.return_value = [editor]
        desktop = Mock()
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=desktop), patch(
            "skills.desktop_control.desktop_controls._native_active_window", return_value=(window, {})
        ), patch("skills.desktop_control.desktop_controls._active_native_control", return_value=editor), patch(
            "pyperclip.paste", return_value=""
        ), patch("pyperclip.copy"), patch("pywinauto.keyboard.send_keys") as send_keys:
            clicked = _native_click("text editing area", window=window)
            first = desktop_type({"text": "same text"})
            second = desktop_type({"text": "same text"})
        self.assertEqual(clicked["status"], "completed")
        self.assertEqual(first["status"], "completed")
        self.assertEqual(second["status"], "completed")
        self.assertEqual(send_keys.call_count, 2)

    def test_retained_editor_is_invalidated_when_window_or_control_is_stale(self):
        editor = Mock()
        editor.element_info.control_type = "Edit"
        editor.element_info.process_id = 42
        editor.element_info.handle = 200
        editor.is_visible.return_value = False
        editor.is_enabled.return_value = True
        window = Mock()
        window.element_info.name = "Notepad"
        window.element_info.process_id = 42
        window.element_info.handle = 200
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=Mock()), patch(
            "skills.desktop_control.desktop_controls._native_active_window", return_value=(window, {})
        ), patch("skills.desktop_control.desktop_controls._active_native_control", return_value=None):
            from skills.desktop_control.desktop_controls import _remember_native_editor
            _remember_native_editor(editor, window)
            result = _native_type("safe test")
        self.assertEqual(result["status"], "unsupported_target")

    def test_switching_foreground_application_does_not_restore_old_editor(self):
        editor = Mock()
        editor.element_info.control_type = "Edit"
        editor.element_info.process_id = 42
        editor.element_info.handle = 300
        editor.is_visible.return_value = True
        editor.is_enabled.return_value = True
        old_window = Mock()
        old_window.element_info.name = "Notepad"
        old_window.element_info.process_id = 42
        old_window.element_info.handle = 300
        new_window = Mock()
        new_window.element_info.name = "Other App"
        new_window.element_info.process_id = 99
        new_window.element_info.handle = 400
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=Mock()), patch(
            "skills.desktop_control.desktop_controls._native_active_window", return_value=(old_window, {})
        ), patch("skills.desktop_control.desktop_controls._active_native_control", return_value=editor):
            from skills.desktop_control.desktop_controls import _remember_native_editor
            _remember_native_editor(editor, old_window)
        with patch("skills.desktop_control.desktop_controls._native_desktop", return_value=Mock()), patch(
            "skills.desktop_control.desktop_controls._native_active_window", return_value=(new_window, {})
        ), patch("skills.desktop_control.desktop_controls._active_native_control", return_value=None):
            result = _native_type("must not go to another app")
        self.assertEqual(result["status"], "unsupported_target")

    def test_browser_unavailable_falls_back_to_native_resolution(self):
        browser = Mock()
        browser.click_target.return_value = {
            "ok": False,
            "status": "browser_unavailable",
            "action": "desktop_click",
        }
        native = {"ok": True, "status": "completed", "action": "desktop_click"}
        with patch("skills.desktop_control.desktop_controls._browser_controller", return_value=browser), patch(
            "skills.desktop_control.desktop_controls._native_click", return_value=native
        ) as native_click:
            result = desktop_click({"target": "search box"})
        self.assertEqual(result["status"], "completed")
        native_click.assert_called_once_with("search box", "")

    def test_browser_dom_click_and_exact_type(self):
        search = _FakeBrowserElement({
            "text": "",
            "aria": "Search",
            "placeholder": "Search",
            "title": "",
            "role": "input",
            "visible": True,
            "disabled": False,
        })
        controller = BrowserController()
        controller.page = _FakeBrowserPage([search])
        clicked = controller._click_target_impl("search box")
        typed = controller._type_text_impl("Rahul — exact\ntext", "search box")
        self.assertEqual(clicked["status"], "completed")
        self.assertEqual(typed["status"], "completed")
        self.assertEqual(search.filled, "Rahul — exact\ntext")
        self.assertTrue(search.clicked)


if __name__ == "__main__":
    unittest.main()
