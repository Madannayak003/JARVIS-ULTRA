import unittest
from unittest.mock import Mock, patch

from core.live_agent import LIVE_CAPABILITY_SCHEMAS, _validate_structured_parameters, execute_live_capability
from core.live_execution import resolve_live_task_results
from core.routers.memory_router import memory_route
from core.routers.vision_router import vision_route


class LiveRoutingRegressionTests(unittest.TestCase):
    def test_photo_and_screenshot_have_distinct_routes(self):
        self.assertEqual(vision_route("take a photo"), [{"action": "capture"}])
        self.assertEqual(vision_route("capture a photo with my camera"), [{"action": "capture"}])
        self.assertIsNone(vision_route("take a screenshot"))

    def test_reminder_router_preserves_text_and_time(self):
        plan = memory_route("remind me in 30 seconds to drink water")
        self.assertEqual(plan[0]["action"], "create_reminder")
        self.assertEqual(plan[0]["text"], "drink water")
        self.assertTrue(plan[0]["remind_at"])

    def test_live_schemas_expose_camera_and_reminders(self):
        for action in ("capture", "camera_preview", "camera_status", "screenshot", "create_reminder", "list_reminders", "cancel_reminder"):
            self.assertIn(action, LIVE_CAPABILITY_SCHEMAS)

    def test_live_schemas_expose_existing_spotify_capabilities(self):
        for action in ("spotify_open", "spotify_close", "spotify_play", "spotify_pause", "spotify_next", "spotify_previous", "spotify_play_song"):
            self.assertIn(action, LIVE_CAPABILITY_SCHEMAS)
        payload, error = _validate_structured_parameters("spotify_play_song", {"song": "Daft Punk"})
        self.assertEqual(payload["song"], "Daft Punk")
        self.assertIsNone(error)

    def test_generic_spotify_play_pause_route_to_local_controls(self):
        from core.fast_router import fast_route

        self.assertEqual(fast_route("play"), [{"action": "spotify_play"}])
        self.assertEqual(fast_route("play music"), [{"action": "spotify_play"}])
        self.assertEqual(fast_route("pause"), [{"action": "spotify_pause"}])
        self.assertEqual(fast_route("resume music"), [{"action": "spotify_play"}])

    def test_reminder_arguments_are_validated(self):
        payload, error = _validate_structured_parameters("create_reminder", {"text": "drink water", "remind_at": "2026-10-10T20:00:00"})
        self.assertEqual(payload["text"], "drink water")
        self.assertIsNone(error)
        payload, error = _validate_structured_parameters("cancel_reminder", {"id": "1"})
        self.assertIsNone(payload)
        self.assertEqual(error["status"], "invalid_arguments")

    def test_live_result_preserves_false_and_structured_success(self):
        fake_registry = Mock()
        fake_registry.has_skill.return_value = True
        with patch("core.live_agent._registry", return_value=fake_registry):
            failed = execute_live_capability("capture", {}, executor=lambda action, data: False)
            succeeded = execute_live_capability("capture", {}, executor=lambda action, data: {"ok": True, "path": "photo.jpg"})
        self.assertFalse(failed["ok"])
        self.assertTrue(succeeded["ok"])
        self.assertEqual(succeeded["action"], "capture")

    def test_delayed_results_are_truthful(self):
        pending = {"ok": True, "status": "pending_weather", "message": "scheduled"}
        self.assertEqual(resolve_live_task_results(pending, [True], "weather")["status"], "completed")
        self.assertEqual(resolve_live_task_results(pending, [{"ok": True, "status": "reported_success", "message": "22 C"}], "weather")["message"], "22 C")
        self.assertFalse(resolve_live_task_results(pending, [False], "weather")["ok"])
        self.assertFalse(resolve_live_task_results(pending, [RuntimeError("boom")], "weather")["ok"])
        self.assertEqual(resolve_live_task_results(pending, [None], "weather")["status"], "pending_weather")


if __name__ == "__main__":
    unittest.main()
