import importlib
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

from core.live_execution import (
    build_live_function_response,
    preserve_live_media,
    send_live_tool_response,
    _live_tool_response_payload,
)


class BrowserVisionRegressionTests(unittest.TestCase):
    def test_live_media_response_serializes_bytes_as_inline_image_json(self):
        class FakeFunctionResponse:
            def model_dump(self, **_kwargs):
                return {
                    "id": "call-1",
                    "name": "jarvis_capability__screen_vision_analyze",
                    "response": {"ok": True, "correlation_id": "call-1"},
                    "parts": [{
                        "inlineData": {
                            "data": b"PNG-FRAME",
                            "mimeType": "image/png",
                        }
                    }],
                }

        payload = _live_tool_response_payload(FakeFunctionResponse())
        encoded = json.dumps(payload)
        self.assertNotIn("PNG-FRAME", encoded)
        response = payload["tool_response"]["functionResponses"][0]
        self.assertEqual(response["id"], "call-1")
        self.assertEqual(response["response"]["correlation_id"], "call-1")
        self.assertEqual(
            response["parts"][0]["inlineData"]["data"],
            "UE5HLUZSQU1F",
        )
        self.assertEqual(
            response["parts"][0]["inlineData"]["mimeType"],
            "image/png",
        )

    def test_live_json_safe_responses_stay_on_sdk_send_path(self):
        response = {"id": "call-2", "name": "tool", "response": {"ok": True}}
        self.assertNotIn("bytes", repr(response))
        source = Path("core/live_execution.py").read_text(encoding="utf-8")
        self.assertIn("if not _contains_live_bytes(function_responses):", source)
        self.assertIn("session.send_tool_response", source)

    def test_live_media_send_reports_missing_websocket(self):
        class FakeFunctionResponse:
            def model_dump(self, **_kwargs):
                return {"parts": [{"inlineData": {"data": b"PNG"}}]}

        source = Path("core/live_execution.py").read_text(encoding="utf-8")
        self.assertIn("Gemini Live websocket is unavailable for media response.", source)
        payload = _live_tool_response_payload(FakeFunctionResponse())
        self.assertEqual(payload["tool_response"]["functionResponses"][0]["parts"][0]["inlineData"]["data"], "UE5H")

    def test_live_screen_limits_and_timeout_remain_configured(self):
        source = Path("voice/agent.py").read_text(encoding="utf-8")
        self.assertIn("SCREEN_VISION_TIMEOUT_SECONDS = 10.0", source)
        self.assertIn("MAX_LIVE_SCREEN_IMAGE_BYTES = 8 * 1024 * 1024", source)
        self.assertIn("asyncio.wait_for(", source)
        self.assertIn('"status": "timeout"', source)
        self.assertIn("Screen image exceeded the Live payload limit.", source)

    def test_browser_worker_serializes_page_lifecycle_with_extraction(self):
        source = Path("skills/browser/browser_controller.py").read_text(encoding="utf-8")
        marker = "def _run_browser("
        start = source.index(marker)
        end = source.index("    # * =========================================================", start)
        worker_section = source[start:end]
        self.assertIn("with _browser_lock:", worker_section)
        self.assertIn("_browser_worker.run(", worker_section)

    def test_screen_analysis_returns_same_turn_analysis_outside_live(self):
        image = types.SimpleNamespace(size=(1200, 800))
        image.save = Mock()
        response = types.SimpleNamespace(
            success=True,
            text="A browser window is showing the YouTube results.",
            provider="test",
            model="test-vision",
            error=None,
        )
        service = types.SimpleNamespace(generate=Mock(return_value=response))
        vision = types.SimpleNamespace(capture=Mock(return_value=image))
        screen_context = types.SimpleNamespace(set_context=Mock())
        service_module = types.ModuleType("ai.core.service")
        service_module.ai_service = service
        vision_module = types.ModuleType("skills.screen.screen_vision")
        vision_module.screen_vision = vision
        context_module = types.ModuleType("brain.screen_context")
        context_module.screen_context = screen_context
        genai_module = types.ModuleType("google.genai")
        genai_module.types = types.SimpleNamespace(Blob=object)
        sys.modules.pop("skills.screen.screen_vision_skill", None)
        with patch.dict(sys.modules, {
            "ai.core.service": service_module,
            "skills.screen.screen_vision": vision_module,
            "brain.screen_context": context_module,
            "google.genai": genai_module,
        }):
            module = importlib.import_module("skills.screen.screen_vision_skill")
            with patch.object(module, "is_live_execution", return_value=False):
                result = module.screen_vision_analyze({})
        self.assertEqual(result, response.text)
        vision.capture.assert_called_once_with()
        service.generate.assert_called_once()
        screen_context.set_context.assert_called_once()

    def test_live_screen_request_is_correlated_and_not_duplicated(self):
        image = types.SimpleNamespace(size=(800, 600))
        image.save = Mock(side_effect=lambda buffer, format: buffer.write(b"PNG-FRAME"))
        vision = types.SimpleNamespace(capture=Mock(return_value=image))
        service_module = types.ModuleType("ai.core.service")
        service_module.ai_service = types.SimpleNamespace()
        vision_module = types.ModuleType("skills.screen.screen_vision")
        vision_module.screen_vision = vision
        genai_module = types.ModuleType("google.genai")
        genai_module.types = types.SimpleNamespace(Blob=object)
        sys.modules.pop("skills.screen.screen_vision_skill", None)
        with patch.dict(sys.modules, {
            "ai.core.service": service_module,
            "skills.screen.screen_vision": vision_module,
            "google.genai": genai_module,
        }):
            module = importlib.import_module("skills.screen.screen_vision_skill")
            module._LIVE_SCREEN_REQUESTS.clear()
            with patch.object(module, "is_live_execution", return_value=True):
                first = module.screen_vision_analyze({"_live_request_id": "call-1"})
                second = module.screen_vision_analyze({"_live_request_id": "call-1"})
                fresh = module.screen_vision_analyze({"_live_request_id": "call-2"})
        self.assertEqual(first["status"], "completed")
        self.assertEqual(first["correlation_id"], "call-1")
        self.assertEqual(second, first)
        self.assertEqual(first["_live_image_bytes"], b"PNG-FRAME")
        self.assertEqual(fresh["correlation_id"], "call-2")
        self.assertEqual(vision.capture.call_count, 2)

    def test_search_and_pause_results_are_not_swallowed(self):
        voice = types.ModuleType("voice.manager")
        voice.speak = Mock()
        sys.modules.pop("skills.browser.youtube", None)
        with patch.dict(sys.modules, {"voice.manager": voice}):
            module = importlib.import_module("skills.browser.youtube")
            videos = [{"title": "One", "url": "https://example/1", "video_id": "one"}]
            module.browser_context.clear_search()
            with patch.object(module.browser, "search_youtube"), patch.object(module, "get_video_list", return_value=videos):
                search = module.ai_youtube({"query": "Kalyani"})
            self.assertEqual(search["result_count"], 1)
            self.assertEqual(search["results"][0]["data"]["video_id"], "one")
            voice.speak.reset_mock()
            with patch.object(module, "is_live_execution", return_value=True), patch.object(module.browser, "pause_video", return_value=True):
                pause = module.youtube_pause({})
            self.assertTrue(pause["ok"])
            self.assertFalse(pause["playback_state_verified"])
            voice.speak.assert_not_called()

    def test_live_function_response_carries_screen_frame_as_media_part(self):
        fake_types = types.SimpleNamespace(
            FunctionResponsePart=types.SimpleNamespace(
                from_bytes=staticmethod(lambda *, data, mime_type: {
                    "data": data,
                    "mime_type": mime_type,
                })
            ),
            FunctionResponse=lambda **kwargs: kwargs,
        )
        result = build_live_function_response(
            fake_types,
            "call-1",
            "jarvis_capability__screen_vision_analyze",
            {
                "ok": True,
                "status": "completed",
                "action": "screen_vision_analyze",
                "correlation_id": "call-1",
                "message": "Describe the image.",
                "_live_image_bytes": b"PNG-FRAME",
                "_live_image_mime_type": "image/png",
            },
        )
        self.assertEqual(result["parts"][0]["data"], b"PNG-FRAME")
        self.assertEqual(result["parts"][0]["mime_type"], "image/png")
        self.assertNotIn("_live_image_bytes", result["response"])

    def test_jarvis_command_wrapper_preserves_screen_media_for_same_turn(self):
        wrapped = preserve_live_media(
            {
                "success": True,
                "message": "JARVIS result: screen captured.",
                "authoritative": True,
            },
            {
                "ok": True,
                "status": "completed",
                "action": "screen_vision_analyze",
                "correlation_id": "call-1",
                "_live_image_bytes": b"PNG-FRAME",
                "_live_image_mime_type": "image/png",
            },
        )
        response = build_live_function_response(
            types.SimpleNamespace(
                FunctionResponsePart=types.SimpleNamespace(
                    from_bytes=staticmethod(lambda *, data, mime_type: {
                        "data": data,
                        "mime_type": mime_type,
                    })
                ),
                FunctionResponse=lambda **kwargs: kwargs,
            ),
            "call-1",
            "jarvis_command",
            wrapped,
        )
        self.assertEqual(response["parts"][0]["data"], b"PNG-FRAME")
        self.assertEqual(response["response"]["action"], "screen_vision_analyze")

    def test_missing_screen_image_is_never_reported_as_success(self):
        fake_types = types.SimpleNamespace(FunctionResponse=lambda **kwargs: kwargs)
        result = build_live_function_response(
            fake_types,
            "call-1",
            "jarvis_capability__screen_vision_analyze",
            {
                "ok": True,
                "status": "completed",
                "action": "screen_vision_analyze",
                "correlation_id": "call-1",
            },
        )
        self.assertFalse(result["response"]["ok"])
        self.assertEqual(result["response"]["status"], "failed")

    def test_live_capture_failure_is_truthful(self):
        vision = types.SimpleNamespace(capture=Mock(return_value=None))
        service_module = types.ModuleType("ai.core.service")
        service_module.ai_service = types.SimpleNamespace()
        vision_module = types.ModuleType("skills.screen.screen_vision")
        vision_module.screen_vision = vision
        genai_module = types.ModuleType("google.genai")
        genai_module.types = types.SimpleNamespace(Blob=object)
        sys.modules.pop("skills.screen.screen_vision_skill", None)
        with patch.dict(sys.modules, {
            "ai.core.service": service_module,
            "skills.screen.screen_vision": vision_module,
            "google.genai": genai_module,
        }):
            module = importlib.import_module("skills.screen.screen_vision_skill")
            with patch.object(module, "is_live_execution", return_value=True):
                result = module.screen_vision_analyze({"_live_request_id": "call-1"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["action"], "screen_vision_analyze")


if __name__ == "__main__":
    unittest.main()
