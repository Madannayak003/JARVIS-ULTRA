import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


def _voice_stub():
    module = types.ModuleType("voice.manager")
    module.speak = Mock()
    return module


class ActionEdgeTests(unittest.TestCase):
    def test_youtube_search_returns_structured_browser_results(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.browser.youtube")
            module.browser_context.clear_search()
            videos = [
                {"title": "First", "url": "https://youtube.test/1", "video_id": "v1", "channel": "A"},
                {"title": "Second", "url": "https://youtube.test/2", "video_id": "v2", "channel": "B"},
            ]
            with patch.object(module.browser, "search_youtube"), patch.object(module, "get_video_list", return_value=videos):
                result = module.ai_youtube({"query": "Kalyani"})
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["result_count"], 2)
            self.assertEqual(result["results"][1]["data"]["video_id"], "v2")
            self.assertEqual(module.browser_context.get_result(2).data["video_id"], "v2")

    def test_youtube_pause_returns_browser_failure_without_live_speech(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.browser.youtube")
            with patch.object(module, "is_live_execution", return_value=True), patch.object(module.browser, "pause_video", return_value=False):
                result = module.youtube_pause({})
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "failed")
            module.speak.assert_not_called()

    def test_youtube_control_phrases_reach_expected_actions(self):
        from core.fast_router import fast_route

        expected = {
            "pause video": "youtube_pause",
            "pause the video": "youtube_pause",
            "resume video": "youtube_resume",
            "continue playing": "youtube_resume",
            "play the video": "youtube_resume",
            "next video": "youtube_next",
            "previous video": "youtube_previous",
        }
        for command, action in expected.items():
            with self.subTest(command=command):
                self.assertEqual(fast_route(command)[0]["action"], action)

    def test_clarify_starts_coordinator_and_speaks_question(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.ai.clarify")
            with patch.object(module.conversation_coordinator, "start_clarification") as start:
                self.assertTrue(module.ai_clarify({"question": "Which one?", "original_request": "open it"}))
                start.assert_called_once()
            module.speak.assert_called_once_with("Which one?")

    def test_running_apps_reports_processes_without_termination(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.system.process")
            fake = types.SimpleNamespace(info={"pid": 7, "name": "demo.exe"})
            with patch.object(module.psutil, "process_iter", return_value=[fake]):
                self.assertTrue(module.process_action({"action": "running_apps"}))
            module.speak.assert_called_once()

    def test_phone_confirmation_rejects_invalid_number_without_calling(self):
        module = importlib.import_module("skills.phone_call.phone_call")
        with patch.object(module, "_start_call") as start:
            self.assertFalse(module.phone_call_confirmed({"phone_number": "not-a-number"}))
            start.assert_not_called()

    def test_youtube_result_rejects_missing_video_id(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.browser.youtube")
            with patch.object(module.browser, "play_video") as play:
                self.assertFalse(module.youtube_play_result({}))
                play.assert_not_called()

    def test_youtube_result_reports_navigation_without_fake_playback_verification(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.browser.youtube")
            with patch.object(module.browser, "play_video", return_value=True):
                result = module.youtube_play_result({"video_id": "abc123"})
            self.assertTrue(result["ok"])
            self.assertFalse(result["playback_state_verified"])
            self.assertIn("not verified", result["message"])

    def test_spotify_play_uses_local_media_control_without_web_api(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.media.spotify")
            with patch.object(module, "ensure_spotify") as ensure, \
                 patch.object(module.keyboard, "press") as press, \
                 patch.object(module.keyboard, "release") as release:
                result = module.spotify_play({})
            self.assertTrue(result["ok"])
            self.assertFalse(result["playback_state_verified"])
            ensure.assert_called_once_with()
            press.assert_called_once_with(module.Key.media_play_pause)
            release.assert_called_once_with(module.Key.media_play_pause)

            with patch.object(module, "ensure_spotify", side_effect=RuntimeError("Spotify unavailable")):
                failed = module.spotify_play({})
            self.assertFalse(failed["ok"])
            self.assertFalse(failed["playback_state_verified"])

    def test_spotify_next_does_not_report_api_success_after_control_failure(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.media.spotify")
            with patch.object(module.keyboard, "press", side_effect=RuntimeError("media key unavailable")):
                result = module.spotify_next({})
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "failed")
            self.assertFalse(result["playback_state_verified"])

    def test_whatsapp_wait_contact_only_enters_prompt_state(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.communication.whatsapp")
            self.assertTrue(module.whatsapp_wait_contact({}))
            module.speak.assert_called_once_with("Which contact should I send it to?")

    def test_chatgpt_search_delegates_to_navigation(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.communication.chatgpt")
            with patch.object(module.navigation, "chatgpt") as navigate:
                self.assertTrue(module.ai_chatgpt({"query": "python"}))
                navigate.assert_called_once_with("python")

    def test_play_delegates_first_result_without_external_side_effect(self):
        with patch.dict(sys.modules, {"voice.manager": _voice_stub()}):
            module = importlib.import_module("skills.media.media")
            with patch.object(module.browser, "play_first_video", return_value=True) as play:
                self.assertTrue(module.ai_play({"target": "first_result"}))
                play.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
