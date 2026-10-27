import unittest

from core.live_execution import LiveInvocationDeduplicator


class LiveInvocationDeduplicatorTests(unittest.TestCase):
    def test_duplicate_completed_id_is_cached_without_a_second_dispatch(self):
        deduplicator = LiveInvocationDeduplicator()
        physical_dispatches = []

        status, _ = deduplicator.begin("call-1")
        self.assertEqual(status, "new")
        physical_dispatches.append("same text")
        response = {"id": "call-1", "ok": True}
        deduplicator.complete("call-1", response)

        status, cached = deduplicator.begin("call-1")
        self.assertEqual(status, "cached")
        self.assertIs(cached, response)
        self.assertEqual(physical_dispatches, ["same text"])

    def test_distinct_ids_with_identical_text_are_independent(self):
        deduplicator = LiveInvocationDeduplicator()
        physical_dispatches = []

        for invocation_id in ("call-1", "call-2"):
            status, _ = deduplicator.begin(invocation_id)
            self.assertEqual(status, "new")
            physical_dispatches.append("same text")
            deduplicator.complete(
                invocation_id,
                {"id": invocation_id, "ok": True},
            )

        self.assertEqual(physical_dispatches, ["same text", "same text"])

    def test_inflight_duplicate_is_marked_waiting_without_dispatching(self):
        deduplicator = LiveInvocationDeduplicator()
        status, _ = deduplicator.begin("call-1")
        self.assertEqual(status, "new")

        status, pending = deduplicator.begin("call-1")
        self.assertEqual(status, "wait")

        response = {"id": "call-1", "ok": False, "status": "failed"}
        deduplicator.complete("call-1", response)
        self.assertTrue(pending.done())
        self.assertIs(pending.result(), response)

    def test_failed_result_is_cached_once_and_not_retried(self):
        deduplicator = LiveInvocationDeduplicator()
        failed_response = {
            "id": "call-1",
            "ok": False,
            "status": "unsupported_target",
        }

        status, _ = deduplicator.begin("call-1")
        self.assertEqual(status, "new")
        deduplicator.complete("call-1", failed_response)

        status, cached = deduplicator.begin("call-1")
        self.assertEqual(status, "cached")
        self.assertIs(cached, failed_response)

    def test_calls_without_protocol_ids_are_not_conflated(self):
        deduplicator = LiveInvocationDeduplicator()
        first_status, _ = deduplicator.begin("")
        second_status, _ = deduplicator.begin("")
        self.assertEqual(first_status, "new")
        self.assertEqual(second_status, "new")
if __name__ == "__main__":
    unittest.main()
