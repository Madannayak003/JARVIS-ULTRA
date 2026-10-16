# Confirmed integration findings

## Repaired in the pre-existing worktree

1. Delayed Live tasks could complete after the synchronous handler returned while their outcomes were discarded. `core/live_execution.py` now returns drained outcomes, and `voice/agent.py` folds them into the tool result before replying.
2. Live result handling could lose authoritative structured results or convert failures into success-like text. Shared normalization now preserves dictionaries, booleans, empty results, exceptions, and delayed failures.
3. Screen analysis carried private PNG bytes through a JSON-shaped result. The response builder now strips `_live_*` fields from JSON and uses the installed SDK media-part contract.
4. Correlation IDs are retained for screen analysis, and duplicate correlated screen responses are suppressed in the Live response loop.
5. The static audit manifest omitted action source paths. `tools/live_capability_audit.py` now records them and can emit the required CSV.

## No confirmed additional product defect

Focused regression tests passed after the audit. No skill implementation was rewritten or replaced as part of this audit pass. The existing modified skill files remain user-owned changes and were not reverted or broadly reformatted.
