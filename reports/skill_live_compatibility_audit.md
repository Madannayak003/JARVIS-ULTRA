# JARVIS ULTRA — Gemini Live Skill Compatibility Audit

Audit date: 2026-10-22 (Asia/Calcutta)

## Executive summary

This was an audit-first review of the current worktree. Existing uncommitted
changes were present before this audit and were preserved. No commit, reset,
push, destructive test, real external action, or credential inspection was
performed.

Definitions: `PASS_STATIC` means AST/inventory evidence only; `PASS_UNIT`
means a focused automated test passed; `PASS_RUNTIME` means a real runtime
exercise was independently executed in this environment. Owner-reported
runtime evidence is recorded separately and is not counted as independently
verified runtime evidence. `BLOCKED` means the requested evidence could not be
obtained because of an environment or safety constraint.

- Modules inspected: 48 configured skill modules.
- Public registered actions identified: 160.
- Structured Live actions identified: 76.
- Duplicate action names: 0.
- Static inspection: 160 actions have implementation definitions.
- Current inventory status: 145 `PASS_STATIC`, 11 `PASS_UNIT`, 3
  `PASS_LIVE_RUNTIME` evidence entries, and 1 `NOT_TESTED` entry.
- Focused Live capability matrix: 70 passed.
- Repository `tests/` suite: **352 passed, 4 skipped, 4 warnings, and 44
  subtests passed**.
- Seven high-impact actions now have explicit mocked Live-boundary evidence in
  the inventory; this verifies declaration/validation/dispatch/result
  handling only, not real-world execution.
- Independently verified runtime actions: 0 in this environment.
- Owner-reported runtime actions: `capture`, `screenshot`, and `create_reminder`.
- Confirmed repair set already present in the worktree: Live delayed-result
  propagation, screen image correlation, reminder time/idempotency handling,
  and camera/screenshot routing corrections.
- New repairs made during this audit: deferred Gemini/dispatcher/Edge-TTS
  imports so routing helpers do not initialize optional network clients; added
  an import-boundary regression test; aligned retired-provider and stale
  architecture tests; added safe Windows persistence fallbacks for file
  intelligence and scheduling.
- Known environment issue: eager optional network imports previously triggered
  a Windows SSL proxy `PermissionError`. The Live boundary is now lazy and the
  focused suite passes; a credentialed real Live session remains unrun.

The configured conversational model remains `gemini-3.8-live` in
`config/settings.py`, with `voice/agent.py` obtaining it through the existing
configuration helper. No second conversational controller or fallback model
was introduced by this audit.

## Per-skill audit matrix

All actions below were found in the current registry/AST inventory. `PASS_STATIC`
is intentionally used where no focused unit or independent runtime evidence
exists. Protected skills are included for traceability and were read-only in
this audit.

| Skill module | Registered actions | Live/schema and execution evidence | Status |
|---|---|---|---|
| ai.clarify | clarify | Generic Live dispatch; focused unit evidence | PASS_UNIT |
| android_control.android_control | android_check_adb, android_check_device, android_device_info, android_launch_app, android_open_app | Generic dispatch; protected/read-only review | PASS_STATIC |
| assistant.greetings | assistant_name, goodbye, greet, how_are_you, welcome | Generic dispatch; greeting tests available | PASS_UNIT |
| automation.home_automation | home_automation | Generic dispatch; no safe runtime exercise | PASS_STATIC |
| automation.scheduling | cancel_schedule, create_schedule, list_schedules | Generic dispatch; scheduling tests available | PASS_UNIT |
| browser.browser_ai | browser_open_result, browser_read_page, google_search, open | Generic dispatch and browser router | PASS_STATIC |
| browser.youtube | youtube_next, youtube_pause, youtube_play_first, youtube_play_result, youtube_previous, youtube_resume, youtube_search | Protected baseline; existing diff preserved; no audit edits | PASS_STATIC |
| browser_control.browser_controls | back, close, close_tab, forward, new_tab, refresh, scroll_down, scroll_up | Generic dispatch; no real browser side effects | PASS_STATIC |
| camera.camera | camera_close, camera_preview, camera_status, capture, start_recording, stop_recording | Generic dispatch; owner-reported capture runtime only | PASS_STATIC |
| camera.vision_skill | cancel_face_registration, delete_face, register_face, vision_check, vision_count, vision_describe, vision_locate, vision_position, vision_start, vision_stop, vision_target | Generic dispatch; hardware and face data excluded from tests | PASS_STATIC |
| communication.chatgpt | chatgpt_search | Generic dispatch; focused delegation unit evidence | PASS_UNIT |
| communication.contact | forget_contact, remember_contact, show_contacts | Generic dispatch; no real contact mutation | PASS_STATIC |
| communication.email | forget_email_contact, remember_email_contact, send_email, show_email_contacts | Generic dispatch; send path not executed | PASS_STATIC |
| communication.github | github_search | Generic dispatch; no external request | PASS_STATIC |
| communication.whatsapp | cancel_scheduled_whatsapp, list_scheduled_whatsapp, reschedule_scheduled_whatsapp, schedule_whatsapp_message, whatsapp_call, whatsapp_close, whatsapp_open, whatsapp_send_file, whatsapp_send_latest_photo, whatsapp_send_latest_screenshot, whatsapp_send_message, whatsapp_send_selected_file, whatsapp_video_call, whatsapp_wait_contact, whatsapp_wait_message | Generic dispatch; wait-contact unit evidence; consequential sends/calls excluded | PASS_UNIT |
| files.file_info | file_info | Generic dispatch; local inspection only | PASS_STATIC |
| files.files | copy, create_file, create_folder, delete, move, open_file, open_folder, rename | Generic dispatch; destructive operations excluded | PASS_STATIC |
| files.recent | recent_files | Generic dispatch; static review | PASS_STATIC |
| files.recycle | recycle | Generic dispatch; destructive operation excluded | PASS_STATIC |
| files.zip_manager | extract, zip | Generic dispatch; static review | PASS_STATIC |
| media.image_generation | create_image | Generic dispatch; no external generation call | PASS_STATIC |
| media.media | play | Generic dispatch; focused delegation unit evidence | PASS_UNIT |
| media.spotify | spotify_close, spotify_next, spotify_open, spotify_pause, spotify_play, spotify_play_song, spotify_previous, spotify_volume_down, spotify_volume_up | Generic dispatch and router; no real playback | PASS_STATIC |
| memory.notes | clear_notes, create_note, list_notes | Generic dispatch; static review | PASS_STATIC |
| memory.reminders | cancel_reminder, create_reminder, list_reminders | Structured schemas; focused reminder regressions; owner-reported runtime | PASS_UNIT |
| navigation.maps | maps_directions, maps_open | Generic dispatch; no external navigation | PASS_STATIC |
| navigation.translate | translate_open, translate_text | Generic dispatch; static review | PASS_STATIC |
| network.bluetooth | bluetooth_devices, bluetooth_status | Generic dispatch; hardware side effects excluded | PASS_STATIC |
| network.weather | weather | Structured Live path; delayed-result repair covered by focused tests | PASS_UNIT |
| network.wifi | wifi_list, wifi_off, wifi_on, wifi_status | Generic dispatch; network mutation excluded | PASS_STATIC |
| news.news | get_news | Generic dispatch; no external request | PASS_STATIC |
| payments.payments | make_payment | Generic dispatch; real payment excluded | PASS_STATIC |
| phone_call.phone_call | answer_call, call_status, end_call, missed_calls, phone_call_confirmed, phone_call_contact, phone_call_number, reject_call | Protected/read-only review; confirmation unit evidence | PASS_UNIT |
| screen.clipboard | clipboard | Generic dispatch; static review | PASS_STATIC |
| screen.screen_vision_skill | screen_vision_analyze | Structured Live image response and correlation repair; no independent runtime | PASS_STATIC |
| screen.screenshot | screenshot | Structured Live capture; owner-reported runtime only | PASS_STATIC |
| screen.screenshot_ai | screenshot_ai | Generic dispatch; no image-service call | PASS_STATIC |
| system.battery | battery | Generic dispatch; static review | PASS_STATIC |
| system.brightness | brightness | Structured Live path; backend import/unavailable behavior covered with mocks; real display control excluded | PASS_UNIT |
| system.process | close_process, running_apps | Generic dispatch; running-apps unit evidence; termination excluded | PASS_UNIT |
| system.system | lock, restart, shutdown, sleep, terminate_jarvis | Dedicated Live schemas; lock/shutdown/application shutdown routing and confirmation unit evidence; real OS effects excluded | PASS_UNIT |
| system.taskmanager | taskmanager | Generic dispatch; static review | PASS_STATIC |
| system.volume | volume | Generic dispatch; hardware mutation excluded | PASS_STATIC |
| utilities.search | search_file | Generic dispatch; local review only | PASS_STATIC |
| utilities.time_skill | time | Generic dispatch; deterministic path | PASS_STATIC |
| web.personal_links | open_personal_link, show_personal_links | Generic dispatch; local configuration only | PASS_STATIC |

## Findings and repairs

The worktree already contains focused repairs for the following confirmed
compatibility findings:

1. Delayed Live tasks previously had their outcomes discarded. The Live drain
   path now returns task outcomes and the response path can report delayed
   failures honestly. Regression coverage includes weather and Live routing.
2. Screen vision previously sent a separately scheduled image frame and could
   return before the original tool response was correlated. The current path
   attaches the captured PNG to the correlated Live function response and
   preserves failure status. No second model was added.
3. Reminder parsing and persistence previously used inconsistent clocks and
   could duplicate a retried Live invocation. The current path resolves time
   once, uses timezone-aware normalization, persists invocation identity, and
   serializes updates. Reminder regression tests pass.
4. Camera requests could be confused with desktop screenshots. The current
   router and Live capability descriptions distinguish physical camera capture,
   camera preview/status, and desktop screenshot operations.

5. Optional Gemini, normal-provider, legacy-dispatcher, and Edge-TTS imports
   could initialize network clients during module import and fail before Live
   routing was reachable on this Windows environment. `voice/agent.py`,
   `voice/online_edge.py`, and `ai/providers/gemini.py` now load those clients
   only at their actual execution boundaries. `chatbot/ai_chat_bot.py` uses the
   same lazy boundary. A subprocess regression covers the Live import
   boundary; the configured provider and model are unchanged.

6. File-intelligence and scheduling persistence now retain truthful success in
   managed Windows directories that deny atomic replace/rename: the bounded
   direct-write fallback is covered by tests and does not change the storage
   format.

7. Windows lock, Windows shutdown, and JARVIS application shutdown previously
   had registry entries but no dedicated structured Live declarations. The Live
   model could therefore fall into conversational refusal or the ambiguous
   legacy `shutdown` route. Dedicated schemas now distinguish the operations,
   spoken variants route to the existing handlers, Windows shutdown requires
   the existing confirmation state, and JARVIS termination uses the same full
   application lifecycle callback installed for the HUD. Tests use mocks for
   OS/app side effects; no real lock or shutdown was performed.

8. Generic "running apps" requests previously had no structured Windows Live
   capability, while the Android foreground-app declaration was broad enough
   to be selected for a Windows request. The existing Windows `running_apps`
   handler is now directly exposed with platform-specific descriptions and
   exact router aliases; Android foreground routing remains available only for
   explicit phone/Android wording.

9. Dynamic skill loading showed `system.brightness` could fail at import with
   Windows access denied from the display backend, removing the registered
   action despite its static declaration. The import is now guarded and Live
   returns `unavailable` honestly when the backend cannot be used. A dynamic
   loader check now loads all 48 configured modules with zero failures in this
   environment.

The current worktree also retains the earlier repairs for delayed Live result
propagation, correlated screen media, reminder time/idempotency handling, and
camera/screenshot routing. Those paths were regression-tested and not
rewritten.

## Protected-feature verification

At audit start, `git status --short` already listed a modified
`skills/browser/youtube.py`, while `skills/phone_call/` and
`skills/android_control/` were not listed as modified paths. The YouTube diff
was preserved verbatim; no protected file was edited during this audit. No
real YouTube playback, phone call, Android device action, payment, message, or
file deletion was performed.

The current model configuration was checked before reporting and remains
`gemini-3.8-live`. No provider/model-selection change was made.

## Final verification

Commands run:

- `git status --short; git branch --show-current`
- `python tools/live_capability_audit.py --output reports/action_inventory.json`
- `python tools/live_capability_audit.py --output reports/action_inventory.json --csv-output reports/SKILL_ACTION_INVENTORY.csv`
- `python -m pytest -q tests/test_action_edges.py tests/test_browser_vision_regressions.py tests/test_live_routing.py tests/test_live_agent.py tests/test_live_capability_inventory.py tests/test_live_memory_integration.py tests/test_live_voice_regressions.py --maxfail=1 -o faulthandler_timeout=20`
- `python -m pytest -q tests/test_live_capability_matrix.py tests/test_live_agent.py tests/test_live_routing.py tests/test_live_memory_integration.py tests/test_live_voice_regressions.py --maxfail=1 -o faulthandler_timeout=20`
  — **70 passed**.
- `python -m pytest -q tests/test_system_live_controls.py tests/test_live_routing.py --maxfail=1 -o faulthandler_timeout=20`
  — **18 passed**.
- The combined focused Live/system-control rerun passed **76 tests**.
- `python -m pytest -q tests --maxfail=1 -o faulthandler_timeout=20`
  — **350 passed, 4 skipped, 4 warnings, 44 subtests passed**.
- Final rerun after the brightness import repair:
  **352 passed, 4 skipped, 4 warnings, 44 subtests passed**.
- Dynamic loader check: **48/48 configured modules loaded, 0 failures**, with
  every structured Live action present in the runtime registry.
- `python -m pytest -q tests/test_live_voice_regressions.py tests/test_live_capability_inventory.py --maxfail=1 -o faulthandler_timeout=20`
  — **5 passed**.
- A recursive `python -m pytest -q --maxfail=1 -o faulthandler_timeout=20`
  still reaches the embedded `workspace/Python/FaceRecognition/tests` project,
  whose `src` import assumes that project is the working directory. That is an
  unrelated nested-project test-layout failure; the JARVIS `tests/` suite is
  the valid project-level result above.
- `git diff --stat` and protected-path diff inspection.
- `rg` verification of the configured Live model.

Remaining manual/runtime work: run the supported Windows application with real
Gemini Live credentials and hardware/browser integrations, then exercise each
consequential skill under user confirmation. Those checks were not performed
by this audit and should not be inferred from static or mocked evidence.
