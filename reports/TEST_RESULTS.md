# Test results

## Static

- Command: `python tools/live_capability_audit.py --output reports/action_inventory.json --csv-output reports/SKILL_ACTION_INVENTORY.csv`
- Result: PASS_STATIC; 48/48 configured modules exist, 178 actions found, 129 structured schemas, 0 duplicate action names.
- Scope: 149 non-Android actions / 111 structured schemas are in scope. The 29
  Android, Android-dependent payment, and ADB-dependent phone-call actions are
  labeled `EXCLUDED_BY_USER` and were not tested in this continuation.
- Action classification: **116 PASS, 20 PARTIAL, 0 FAIL, 13 UNTESTED** in
  scope; the 29 excluded actions are `EXCLUDED_BY_USER`.
- Historical dynamic loader check: **48/48 configured modules loaded, 0
  failures**, and every structured Live action was present in the runtime
  registry. It was not repeated in this continuation because doing so would
  import excluded Android modules.
- The generated inventory also records the focused mocked Live-boundary
  evidence entries; these do not count as real external integration runtime
  verification.
- `git diff --check`: passed.
- Installed SDK source inspection: PASS_STATIC for `FunctionResponse.parts` and `FunctionResponsePart.from_bytes`.

## Focused unit/regression

- Command: `python -m pytest -q tests/test_live_non_android_inventory.py tests/test_maps_live.py tests/test_brightness_live.py tests/test_system_live_controls.py tests/test_live_agent.py tests/test_live_memory_integration.py tests/test_live_voice_regressions.py --maxfail=1 -o faulthandler_timeout=20`
- Result: **70 passed, 2 warnings** for the focused non-Android Live capability matrix/regression set.
- Coverage includes structured argument validation, generic/structured result preservation, delayed task success/failure, typed routing helpers, camera-vs-screenshot routing, and correlated screen media construction.
- System-control coverage verifies dedicated Live declarations, spoken lock/shutdown/application-shutdown routing, Windows shutdown confirmation gating, separate lock versus shutdown handlers, and application lifecycle callback dispatch using mocks only.
- Windows application-status coverage verifies that generic running-apps requests expose and route to the existing Windows `running_apps` process handler, while explicit phone/Android foreground requests remain Android-specific.
- Brightness coverage verifies safe registration when the Windows display backend is unavailable and an honest `unavailable` result, plus normal behavior with a mocked backend.
- Additional coverage verifies `voice.agent` can be imported without initializing
  the optional Gemini SDK, while an actual Live connection still loads the same
  configured provider at runtime.
- Safe command excluding Android/ADB and Android-dependent tests:
  `python -m pytest -q <all tests except test_android_*.py, test_live_capability_matrix.py, test_live_routing.py, test_phone_call.py> --maxfail=1 -o faulthandler_timeout=20`
  — **369 passed, 4 skipped, 13 warnings, 31 subtests passed**.
- Batch 5 focused command:
  `python -m pytest -q tests/test_live_batch5_results.py tests/test_live_batch4_greetings.py tests/test_live_batch3_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **6 passed**.
- Batch 6 focused command:
  `python -m pytest -q tests/test_live_batch6_files.py tests/test_live_batch5_results.py --maxfail=1 -o faulthandler_timeout=20`
  — **5 passed**.
- Batch 7 focused command:
  `python -m pytest -q tests/test_live_batch7_file_results.py tests/test_live_batch6_files.py --maxfail=1 -o faulthandler_timeout=20`
  — **5 passed**.
- Batch 8 focused command:
  `python -m pytest -q tests/test_live_batch8_readonly_lists.py tests/test_live_batch7_file_results.py --maxfail=1 -o faulthandler_timeout=20`
  — **5 passed, 1 warning**.
- Batch 9 focused command:
  `python -m pytest -q tests/test_live_batch9_persistence_results.py tests/test_scheduling_upgrade.py --maxfail=1 -o faulthandler_timeout=20`
  — **7 passed, 2 warnings**.
- Batch 10 focused command:
  `python -m pytest -q tests/test_live_batch10_spotify_contracts.py tests/test_live_batch9_persistence_results.py --maxfail=1 -o faulthandler_timeout=20`
  — **4 passed**.
- Batch 11 focused command:
  `python -m pytest -q tests/test_live_batch11_result_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **8 passed**.
- Batch 12 focused command:
  `python -m pytest -q tests/test_live_batch12_browser_local_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **5 passed**.
- Batch 13 focused command:
  `python -m pytest -q tests/test_live_batch13_provider_results.py tests/test_weather_async.py --maxfail=1 -o faulthandler_timeout=20`
  — **10 passed**.
- Batch 14 focused command:
  `python -m pytest -q tests/test_live_batch14_safe_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **7 passed**.
- Batch 15 focused command:
  `python -m pytest -q tests/test_live_batch15_browser_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **7 passed, 1 warning**.
- Batch 16 focused command:
  `python -m pytest -q tests/test_live_batch16_persistence_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **5 passed, 1 warning**.
- Batch 16 safe-suite rerun: **359 passed, 4 skipped, 13 warnings, 31
  subtests passed**. The first run caught a legacy WhatsApp boolean-contract
  regression; the implementation was corrected before this passing rerun.
- Batch 17 focused command:
  `python -m pytest -q tests/test_live_batch17_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **4 passed, 1 warning**.
- Batch 17 safe-suite rerun: **363 passed, 4 skipped, 13 warnings, 31
  subtests passed**.
- Batch 18 focused command:
  `python -m pytest -q tests/test_live_batch18_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **3 passed**.
- Batch 18 safe-suite rerun: **366 passed, 4 skipped, 13 warnings, 31
  subtests passed**.
- Batch 19 focused command:
  `python -m pytest -q tests/test_live_batch19_media_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **2 passed**.
- Batch 19 safe-suite rerun: **368 passed, 4 skipped, 13 warnings, 31
  subtests passed**.
- Batch 20 focused command:
  `python -m pytest -q tests/test_live_batch20_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **1 passed**.
- Batch 20 safe regression verification: **364 passed** in the safe subset
  excluding the two inventory scans, plus **5 passed** in the inventory tests
  with `faulthandler_timeout=60`; combined evidence is **369 passed, 4
  skipped, 13 warnings, 31 subtests passed**.
- Batch 21 focused regression command:
  `python -m pytest -q tests/test_live_batch19_media_contracts.py tests/test_live_batch20_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **3 passed**.
- Batch 21 safe regression verification: **364 passed, 4 skipped, 13
  warnings, 31 subtests** in the non-inventory subset; inventory tests passed
  **5 tests in 35.58s** with `faulthandler_timeout=60`.
- The attempted camera-vision test was stopped after the configured timeout
  while importing optional Ultralytics/AV/Torch dependencies; no camera test
  or camera code change was retained.
- Batch 3 focused command:
  `python -m pytest -q tests/test_live_batch3_contracts.py tests/test_live_non_android_repairs.py tests/test_live_non_android_inventory.py --maxfail=1 -o faulthandler_timeout=20`
  — **9 passed**.
- Batch 4 focused command:
  `python -m pytest -q tests/test_live_batch4_greetings.py tests/test_live_batch3_contracts.py tests/test_live_non_android_repairs.py --maxfail=1 -o faulthandler_timeout=20`
  — **7 passed**.
- First repair-batch focused command:
  `python -m pytest -q tests/test_live_non_android_repairs.py tests/test_live_non_android_inventory.py tests/test_live_agent.py --maxfail=1 -o faulthandler_timeout=20`
  — **53 passed** after the second repair batch.
- The full suite was not rerun in this continuation because it includes tests
  explicitly excluded by the user. The previous 352-test result is historical.
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
