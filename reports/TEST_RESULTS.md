# Test results

## Static

- Command: `python tools/live_capability_audit.py --output reports/action_inventory.json --csv-output reports/SKILL_ACTION_INVENTORY.csv`
- Result: PASS_STATIC; 48/48 configured modules exist, 160 actions found, 76 structured schemas, 0 duplicate action names.
- Dynamic loader check: **48/48 configured modules loaded, 0 failures**, and every structured Live action was present in the runtime registry.
- The generated inventory also records seven explicit mocked Live-boundary
  evidence entries; these do not count as real external integration runtime
  verification.
- `git diff --check`: passed.
- Installed SDK source inspection: PASS_STATIC for `FunctionResponse.parts` and `FunctionResponsePart.from_bytes`.

## Focused unit/regression

- Command: `python -m pytest -q tests/test_live_capability_matrix.py tests/test_live_agent.py tests/test_live_routing.py tests/test_live_memory_integration.py tests/test_live_voice_regressions.py --maxfail=1 -o faulthandler_timeout=20`
- Result: 70 passed for the focused Live capability matrix/regression set.
- Coverage includes structured argument validation, generic/structured result preservation, delayed task success/failure, typed routing helpers, camera-vs-screenshot routing, and correlated screen media construction.
- System-control coverage verifies dedicated Live declarations, spoken lock/shutdown/application-shutdown routing, Windows shutdown confirmation gating, separate lock versus shutdown handlers, and application lifecycle callback dispatch using mocks only.
- Windows application-status coverage verifies that generic running-apps requests expose and route to the existing Windows `running_apps` process handler, while explicit phone/Android foreground requests remain Android-specific.
- Brightness coverage verifies safe registration when the Windows display backend is unavailable and an honest `unavailable` result, plus normal behavior with a mocked backend.
- Additional coverage verifies `voice.agent` can be imported without initializing
  the optional Gemini SDK, while an actual Live connection still loads the same
  configured provider at runtime.
- `python -m pytest -q tests --maxfail=1 -o faulthandler_timeout=20`
  — **352 passed, 4 skipped, 4 warnings, 44 subtests passed**.
- `python -m pytest -q tests/test_system_live_controls.py tests/test_live_routing.py --maxfail=1 -o faulthandler_timeout=20`
  — **18 passed, 2 warnings**.
- Combined focused Live/system-control rerun: **76 passed, 2 warnings**.

## Full suite

- Command: `python -m pytest -q --maxfail=1 -o faulthandler_timeout=20`
- The recursive repository-wide command also discovers the embedded
  `workspace/Python/FaceRecognition/tests` project, whose `src` import assumes
  that project is the working directory. This unrelated nested-project test
  layout remains outside the JARVIS `tests/` result above.

## Runtime safety

No real payments, calls, messages, device control, browser side effects, camera capture, or production-data mutations were performed. No Gemini credentialed Live session was started in unattended testing.
