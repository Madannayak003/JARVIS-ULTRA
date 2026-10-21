import contextlib
import io
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.diagnostics import debug_enabled, debug_print, status_print


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.previous = os.environ.get("JARVIS_DEBUG")

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("JARVIS_DEBUG", None)
        else:
            os.environ["JARVIS_DEBUG"] = self.previous

    def test_missing_and_invalid_debug_values_are_quiet(self):
        for value in (None, "0", "invalid"):
            if value is None:
                os.environ.pop("JARVIS_DEBUG", None)
            else:
                os.environ["JARVIS_DEBUG"] = value
            self.assertFalse(debug_enabled())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                debug_print("routine transcript")
            self.assertEqual(output.getvalue(), "")

    def test_debug_mode_preserves_diagnostics(self):
        os.environ["JARVIS_DEBUG"] = "1"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            debug_print("routine transcript")
        self.assertEqual(output.getvalue(), "routine transcript\n")

    def test_status_print_uses_robot_prefix_in_quiet_mode(self):
        os.environ["JARVIS_DEBUG"] = "0"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status_print("Response interrupted.", debug_message="[LIVE] detailed interruption")
        self.assertEqual(output.getvalue(), "🤖 Response interrupted.\n")

    def test_status_print_preserves_detail_in_debug_mode(self):
        os.environ["JARVIS_DEBUG"] = "1"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status_print("Response interrupted.", debug_message="[LIVE] detailed interruption")
        self.assertEqual(output.getvalue(), "[LIVE] detailed interruption\n")


if __name__ == "__main__":
    unittest.main()
