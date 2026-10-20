import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice.hud_intents import classify_hud_voice_intent


class HudVoiceIntentTests(unittest.TestCase):
    def test_mode_variations_and_transcription_errors(self):
        self.assertEqual(classify_hud_voice_intent("Switch to APEX")["mode"], "apex")
        self.assertEqual(classify_hud_voice_intent("Switch to Apex Monite")["mode"], "apex")
        self.assertEqual(classify_hud_voice_intent("Activate humanoid mode")["mode"], "apex")
        self.assertEqual(classify_hud_voice_intent("Switch to Ultram")["mode"], "ultron")

    def test_assembly_variations(self):
        for phrase in (
            "Reassemble",
            "Reassemble the humanoid",
            "Assemble again",
            "Replay humanoid assembly",
            "Show the humanoid assembly",
        ):
            self.assertEqual(classify_hud_voice_intent(phrase)["type"], "assembly")

    def test_ambiguous_conversation_does_not_trigger(self):
        for phrase in (
            "Tell me about humanoid assembly",
            "Open YouTube on my Android phone",
            "What is the humanoid mode used for?",
        ):
            self.assertIsNone(classify_hud_voice_intent(phrase))

    def test_repeated_requests_are_not_time_suppressed(self):
        first = classify_hud_voice_intent("Reassemble")
        second = classify_hud_voice_intent("Reassemble")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_event_identity_deduplicates_delivery_but_not_new_request(self):
        seen_event_ids = set()

        def deliver(event_id, text):
            if event_id in seen_event_ids:
                return False
            seen_event_ids.add(event_id)
            return classify_hud_voice_intent(text) is not None

        self.assertTrue(deliver("event-1", "Reassemble"))
        self.assertFalse(deliver("event-1", "Reassemble"))
        self.assertTrue(deliver("event-2", "Reassemble"))


if __name__ == "__main__":
    unittest.main()
