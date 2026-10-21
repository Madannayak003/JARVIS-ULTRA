import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.core.commands import AICommandHandler
from ai.core.policy import AIModelPolicy
from ai.core.preference import AIPreference
from ai.core.registry import ModelRegistry


class GeminiOnlyTests(unittest.TestCase):
    def test_registry_and_policy_contain_only_gemini(self):
        self.assertEqual({model.provider for model in ModelRegistry().all()}, {"gemini"})
        for providers in AIModelPolicy.PROVIDER_PREFERENCES.values():
            self.assertEqual(providers, ["gemini"])

    def test_legacy_preference_values_normalize_to_gemini(self):
        preference = AIPreference()
        for value in ("auto", "openai", "grok", "gemini"):
            preference.set_provider(value)
            self.assertEqual(preference.mode, "gemini")

    def test_unsupported_selection_commands_are_not_dispatched(self):
        preference = AIPreference()
        self.assertIsNone(AICommandHandler.handle("use openai", preference))
        self.assertIsNone(AICommandHandler.handle("use grok", preference))


if __name__ == "__main__":
    unittest.main()
