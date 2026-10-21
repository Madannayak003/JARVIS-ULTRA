import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings


class LastActiveHudSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = settings._ASSISTANT_SETTINGS_FILE
        settings._ASSISTANT_SETTINGS_FILE = Path(self.temp_dir.name) / "jarvis_settings.json"

    def tearDown(self):
        settings._ASSISTANT_SETTINGS_FILE = self.original_path
        self.temp_dir.cleanup()

    def test_missing_and_invalid_values_fall_back_to_ultron(self):
        self.assertEqual(settings.get_last_active_hud(), "ultron")
        settings._ASSISTANT_SETTINGS_FILE.write_text(json.dumps({"lastActiveHud": "unsupported"}), encoding="utf-8")
        self.assertEqual(settings.get_last_active_hud(), "ultron")

    def test_save_preserves_existing_settings(self):
        settings._ASSISTANT_SETTINGS_FILE.write_text(
            json.dumps({"assistantColour": "#ffab17", "lastActiveHud": "ultron"}),
            encoding="utf-8",
        )
        self.assertEqual(settings.set_last_active_hud("APEX"), "apex")
        saved = json.loads(settings._ASSISTANT_SETTINGS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(saved["lastActiveHud"], "apex")
        self.assertEqual(saved["assistantColour"], "#ffab17")

    def test_invalid_save_is_rejected(self):
        with self.assertRaises(ValueError):
            settings.set_last_active_hud("hologram")

    def test_legacy_ai_provider_values_normalize_to_gemini(self):
        for value in (None, "AUTO", "OPENAI", "GROK", "unsupported"):
            payload = {} if value is None else {"aiProvider": value}
            settings._ASSISTANT_SETTINGS_FILE.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(settings.get_ai_provider_setting(), "GEMINI")

    def test_ai_provider_save_preserves_existing_settings(self):
        settings._ASSISTANT_SETTINGS_FILE.write_text(
            json.dumps({"assistantName": "JARVIS", "aiProvider": "AUTO"}),
            encoding="utf-8",
        )
        self.assertEqual(settings.set_ai_provider_setting("OPENAI"), "GEMINI")
        saved = json.loads(settings._ASSISTANT_SETTINGS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(saved["aiProvider"], "GEMINI")
        self.assertEqual(saved["assistantName"], "JARVIS")


if __name__ == "__main__":
    unittest.main()
