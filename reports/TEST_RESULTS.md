# Test results

## Static

- Command: `python tools/live_capability_audit.py --output reports/action_inventory.json --csv-output reports/SKILL_ACTION_INVENTORY.csv`
- Result: PASS_STATIC; 48/48 configured modules exist, 145 actions found, 27 structured schemas, 0 duplicate action names.
- `git diff --check`: passed.
- Installed SDK source inspection: PASS_STATIC for `FunctionResponse.parts` and `FunctionResponsePart.from_bytes`.

## Focused unit/regression

- Command: `python -m pytest -q test_action_edges.py test_browser_vision_regressions.py test_live_routing.py skills/assistant/test_greetings.py --maxfail=1 -o faulthandler_timeout=20`
- Result: 36 passed, 15 subtests passed.
- Coverage includes structured argument validation, generic/structured result preservation, delayed task success/failure, typed routing helpers, camera-vs-screenshot routing, and correlated screen media construction.

## Full suite

- Command: `python -m pytest -q --maxfail=1 -o faulthandler_timeout=20`
- Result: BLOCKED during collection by `PermissionError` from the Windows security filter's `ssl.create_default_context()` keylog path while importing `aiohttp` via `google-genai`.
- A `tests`-only run hit the same environment blocker during collection.

## Runtime safety

No real payments, calls, messages, device control, browser side effects, camera capture, or production-data mutations were performed. No Gemini credentialed Live session was started in unattended testing.
