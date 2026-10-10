import unittest
from datetime import datetime
import importlib
import sys
import types
from unittest.mock import Mock, patch

# * The production registry currently imports optional AI providers at import
# * time. Keep this unit test runnable in a minimal checkout when those runtime
# * dependencies are not installed; the application still uses core.registry.
try:
    importlib.import_module("core.registry")
except ImportError:
    registry_stub = types.ModuleType("core.registry")
    registry_stub.registered = []

    def register(*args, **kwargs):
        registry_stub.registered.append(args[0])

    registry_stub.register = register
    sys.modules["core.registry"] = registry_stub

from skills.assistant import greetings


class GreetingEngineTests(unittest.TestCase):

    def setUp(self):
        greetings._engine.reset()
        with greetings._startup_lock:
            greetings._startup_spoken = False

    def test_time_contexts(self):
        cases = (
            (datetime(2026, 1, 1, 8), "morning"),
            (datetime(2026, 1, 1, 14), "afternoon"),
            (datetime(2026, 1, 1, 19), "evening"),
            (datetime(2026, 1, 1, 23), "night"),
        )

        for moment, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(greetings._time_context(moment), expected)

    def test_existing_actions_remain_registered(self):
        registry = sys.modules["core.registry"]
        actions = {"greet", "how_are_you", "welcome", "goodbye"}

        if hasattr(registry, "get_handler"):
            self.assertTrue(all(registry.get_handler(action) for action in actions))
        else:
            self.assertEqual(set(registry.registered), actions)

    def test_startup_greeting_is_non_empty_for_each_context(self):
        for hour in (8, 14, 19, 23):
            with self.subTest(hour=hour):
                result = greetings.startup_greeting(
                    datetime(2026, 1, 1, hour),
                    profile={},
                )
                self.assertTrue(result.strip())

    def test_startup_variation_avoids_immediate_repetition(self):
        results = [
            greetings.startup_greeting(
                datetime(2026, 1, 1, 8),
                profile={},
            )
            for _ in range(4)
        ]

        self.assertGreater(len(set(results)), 1)
        self.assertTrue(all(a != b for a, b in zip(results, results[1:])))

    def test_personalization_is_optional_and_safe(self):
        with patch.object(
            greetings.random,
            "choice",
            side_effect=lambda options: options[0],
        ):
            personalized = greetings.startup_greeting(
                datetime(2026, 1, 1, 8),
                profile={"name": "Madan"},
            )
        self.assertIn("Madan", personalized)

        unavailable = Mock()
        unavailable.get.side_effect = RuntimeError("profile unavailable")
        result = greetings.startup_greeting(
            datetime(2026, 1, 1, 8),
            profile=unavailable,
        )
        self.assertTrue(result.strip())
        self.assertNotIn("Madan", result)

    def test_generation_failure_uses_fallback(self):
        with patch.object(
            greetings._engine,
            "startup",
            side_effect=RuntimeError("selection failed"),
        ):
            result = greetings.startup_greeting(
                datetime(2026, 1, 1, 8),
                profile={},
            )

        self.assertEqual(result, "Good morning. Ready when you are.")

    def test_startup_duplicate_protection(self):
        speaker = Mock()

        self.assertTrue(greetings.speak_startup_greeting(speaker, profile={}))
        self.assertFalse(greetings.speak_startup_greeting(speaker, profile={}))
        speaker.assert_called_once()

    def test_tts_failure_does_not_crash(self):
        speaker = Mock(side_effect=RuntimeError("tts unavailable"))

        self.assertFalse(greetings.speak_startup_greeting(speaker, profile={}))

    def test_explicit_time_greetings(self):
        speaker = Mock()
        with patch.object(greetings, "_get_speaker", return_value=speaker):
            greetings.greet({"command": "good morning"})
            greetings.greet({"command": "good afternoon"})
            greetings.greet({"command": "good evening"})

        self.assertEqual(speaker.call_count, 3)
        self.assertTrue(speaker.call_args_list[0].args[0].startswith("Good morning"))
        self.assertTrue(speaker.call_args_list[1].args[0].startswith("Good afternoon"))
        self.assertTrue(speaker.call_args_list[2].args[0].startswith("Good evening"))

    def test_general_greetings(self):
        speaker = Mock()
        with patch.object(greetings, "_get_speaker", return_value=speaker):
            for command in ("hello", "hi", "hey"):
                self.assertTrue(greetings.greet({"command": command}))

        self.assertEqual(speaker.call_count, 3)
        self.assertTrue(all(call.args[0] for call in speaker.call_args_list))

    def test_how_are_you_welcome_and_goodbye(self):
        speaker = Mock()
        with patch.object(greetings, "_get_speaker", return_value=speaker):
            self.assertTrue(greetings.how_are_you({}))
            self.assertTrue(greetings.welcome({}))
            self.assertTrue(greetings.goodbye({}))

        self.assertEqual(speaker.call_count, 3)
        self.assertTrue(all(call.args[0] for call in speaker.call_args_list))

    def test_user_speech_failure_is_safe(self):
        with patch.object(
            greetings,
            "_get_speaker",
            side_effect=RuntimeError("tts unavailable"),
        ):
            self.assertTrue(greetings.greet({"command": "hello"}))
            self.assertTrue(greetings.how_are_you({}))
            self.assertTrue(greetings.welcome({}))
            self.assertTrue(greetings.goodbye({}))


if __name__ == "__main__":
    unittest.main()
