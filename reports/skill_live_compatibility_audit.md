# JARVIS ULTRA — Gemini Live Skill Compatibility Audit

Audit date: 2026-10-10 (Asia/Calcutta)

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
- Public registered actions identified: 145.
- Structured Live actions identified: 27.
- Duplicate action names: 0.
- Static inspection: 145 actions have implementation definitions.
- Focused unit evidence: 7 actions directly covered by the audit regression tests;
  the focused suite passed with 33 tests and 15 subtests.
- Additional schema/inventory/reminder/scheduling run: 54 tests passed before
  one scheduling test was blocked by a Windows sandbox `WinError 5` during the
  atomic temporary-file rename; this was an environment write/lock failure,
  not a failed scheduling assertion.
- Independently verified runtime actions: 0 in this environment.
- Owner-reported runtime actions: `capture`, `screenshot`, and `create_reminder`.
- Confirmed repair set already present in the worktree: Live delayed-result
  propagation, screen image correlation, reminder time/idempotency handling,
  and camera/screenshot routing corrections.
- New code changes made during this audit: none. Existing worktree changes were
  not overwritten.
- Known blocker: the complete `tests/` collection is blocked by an SSL proxy
  permission error while importing the external reference project's
  `tests/test_configuration.py`; the traceback names
  `\\.\aswMonFltProxy\...` and was not worked around by weakening TLS or
  security settings.

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
| system.brightness | brightness | Generic dispatch; hardware mutation excluded | PASS_STATIC |
| system.process | close_process, running_apps | Generic dispatch; running-apps unit evidence; termination excluded | PASS_UNIT |
| system.system | lock, restart, shutdown, sleep, terminate_jarvis | Generic dispatch; consequential operations excluded | PASS_STATIC |
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

These changes were present in the worktree at audit start. No new repair was
made here because changing them without a reproducible new failure would
violate the minimal-change requirement.

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
- `python -m pytest -q test_action_edges.py test_browser_vision_regressions.py test_live_routing.py skills/assistant/test_greetings.py --maxfail=1 -o faulthandler_timeout=20`
  — **33 passed, 15 subtests passed**.
- `python -m pytest -q tests --maxfail=1 -o faulthandler_timeout=20`
  — **blocked during collection** by the SSL proxy permission error described
  above; no tests were labeled passing from that run.
- `python -m pytest -q tests/test_live_agent.py tests/test_live_capability_inventory.py tests/test_reminder_regressions.py tests/test_weather_async.py tests/test_schedule_router_natural.py tests/test_scheduling_upgrade.py --maxfail=1 -o faulthandler_timeout=20`
  — **blocked during weather collection** by the same SSL proxy permission
  error.
- The same command without `tests/test_weather_async.py` — **54 passed, one
  environment-blocked scheduling test** (`WinError 5` renaming the isolated
  temporary schedules file).
- `git diff --stat` and protected-path diff inspection.
- `rg` verification of the configured Live model.

Remaining manual/runtime work: run the supported Windows application with real
Gemini Live credentials and hardware/browser integrations, then exercise each
consequential skill under user confirmation. Those checks were not performed
by this audit and should not be inferred from static or mocked evidence.
