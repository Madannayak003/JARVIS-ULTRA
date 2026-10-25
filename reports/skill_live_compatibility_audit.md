# JARVIS ULTRA — Gemini Live Skill Compatibility Audit

Audit date: 2026-10-25 (Asia/Calcutta)

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
- Public registered actions identified: 178.
- Structured Live actions identified: 129.
- Duplicate action names: 0.
- Static inspection: 178 actions have implementation definitions.
- Non-Android scope: 149 actions and 111 structured Live actions; 28
  `PASS_STATIC`, 116 `PASS_UNIT`, 3 `PASS_LIVE_RUNTIME` owner-reported entries,
  and 13 `NOT_TESTED` entries.
- Action classification for the in-scope matrix: **116 PASS, 20 PARTIAL, 0
  FAIL, and 13 UNTESTED**. `PASS` means focused safe tests passed; it does not
  imply a real credentialed Live session.
- Safe non-Android repository subset: **369 passed, 4 skipped, 13 warnings,
  and 31 subtests passed**.
- Nine additional Spotify actions now have explicit mocked Live-boundary
  evidence in the inventory; this verifies declaration/validation/dispatch/
  result handling only, not real-world execution.
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

## Actual repair batch 1

Ten previously partial, non-Android actions were repaired and verified at the
Live boundary: `assistant_name`, `back`, `forward`, `close_tab`, `refresh`,
`bluetooth_devices`, `bluetooth_status`, `camera_close`, `camera_preview`, and
`camera_status`.

The root causes were missing structured Live declarations for these registered
actions and a Bluetooth handler contract mismatch: the shared Bluetooth
handler requires the action name in its payload, while structured dispatch
provided an empty object. The new schemas expose the actions safely, and the
Bluetooth schemas inject the exact registered action. Evidence is
mocked/boundary-based; no browser navigation, camera access, or Windows
Bluetooth settings mutation was performed.

## Actual repair batch 2

Five additional read-only, non-Android actions were repaired and verified at
the Live boundary: `list_notes`, `clipboard`, `new_tab`, `scroll_down`, and
`scroll_up`. The repairs add reviewed structured declarations, including an
explicit enum for clipboard modes so unsupported operations are rejected
before execution. Evidence is mocked/boundary-based; no user notes were
modified and no browser side effect was performed.

## Batch 3 verification

Ten existing structured capabilities were traced through schema validation,
executor dispatch, result normalization, and required-argument rejection:
`battery`, `browser_open_result`, `browser_read_page`, `cancel_reminder`,
`cancel_schedule`, `cancel_scheduled_whatsapp`, `capture`, `create_reminder`,
`create_schedule`, and `github_search`.

No reproducible implementation defect was found in this batch. The missing
evidence was a safe Live-boundary contract test, so these actions were promoted
to `PASS` based on mocked executor evidence only. The test verifies invocation
metadata for reminders and rejects malformed required arguments before the
executor. No external service, browser, camera, messaging, or scheduler side
effect was performed.

## Batch 4 repair

Three local greeting actions were repaired and verified: `greet`,
`how_are_you`, and `goodbye`. Their handlers and text routes were already
correct, but they had no reviewed structured Live declarations. The new
schemas preserve the optional greeting command only for `greet`; the other
actions accept no parameters. Tests verify declarations, structured dispatch,
and the actual local handlers with mocked speech only.

## Batch 5 repair

Three result-path defects were repaired: `recent_files` now handles an
unavailable Downloads folder and returns an explicit `unavailable` result;
`list_reminders` now returns active reminder records and a count; and
`list_scheduled_whatsapp` now returns active scheduled-message records and a
count. Previously the two list handlers returned only `True`, so Gemini Live
could not receive the actual list. Tests use temporary data and mocked speech;
no user data, messages, or external services were accessed.

## Batch 6 repair

The non-Android file skill had a concrete import defect: its handlers called
`os.path`, `os.startfile`, `os.makedirs`, and related APIs without importing
`os`. Eight registered file actions were affected: `open_file`, `open_folder`,
`create_folder`, `create_file`, `copy`, `move`, `delete`, and `rename`. The
missing import was restored, and safe missing-path/error-branch tests exercise
the actual handler boundary without creating, moving, or deleting real user
files.

## Batch 7 repair

Five read-only file capabilities were repaired and verified: `file_info` now
returns structured metadata instead of only `True`; `search_file` now returns
matching paths and count; and `file_intelligence_request`,
`file_question_request`, and `file_search_request` now have reviewed
structured Live schemas with required-argument validation and action injection.
Tests use temporary files and mocked storage/search boundaries; no external AI,
browser, or user file mutation was performed.

## Batch 8 repair

Three read-only directory actions were repaired: `show_contacts` and
`show_email_contacts` now return their actual contact mappings and counts
instead of only `True`; `show_personal_links` received a reviewed structured
Live declaration. Tests mock contact storage and HUD publication, and do not
mutate contacts or open any link.

## Batch 9 repair

Two local persistence result gaps were repaired: `create_note` now returns a
structured saved-note result and count; `list_schedules` preserves its legacy
list return for existing callers while the Live adapter converts it to a
structured `{items, count, status}` response. Tests cover populated and empty
states with mocked/temporary storage only.

Android control, Android-dependent payments, and ADB-dependent phone-call
actions are explicitly excluded by the user from this continuation. They are
retained in the all-repository inventory (29 actions) and labeled
`EXCLUDED_BY_USER`; no Android/ADB source, operation, or test was modified or
run for this continuation.

## Batch 10 verification

Nine Spotify actions were selected because they were registered and exposed
through the generic Live dispatcher but lacked focused contract evidence:
`spotify_open`, `spotify_close`, `spotify_next`, `spotify_previous`,
`spotify_pause`, `spotify_play`, `spotify_volume_up`, `spotify_volume_down`,
and `spotify_play_song`. Tracing reproduced no implementation defect. The
focused tests validate action-specific argument handling, executor routing,
call order, and the required `song` argument; malformed input is rejected
without invoking the executor. The actions are promoted to `PASS` on mocked
Live-boundary evidence only. No Spotify process, playback, API, credential,
or external side effect was used.

## Batch 11 repair

Seven non-Android actions were repaired and verified at the structured Live
boundary: `time`, `taskmanager`, `wifi_on`, `wifi_off`, `wifi_status`,
`wifi_list`, and `translate_text`. The handlers previously returned only
boolean success after doing useful work, so Live could not receive the actual
time, usage metrics, Wi-Fi state/network names, or translated text. They now
return structured results while remaining truthy for legacy callers. Wi-Fi
listing and translation also received reviewed structured schemas; malformed
translation arguments are rejected before execution. Tests mock speech,
psutil, netsh, and the translation service. No real network mutation,
external service, or credentialed request was performed.

## Batch 13 repair

Two non-Android provider actions were repaired and verified at the structured
Live boundary: `weather` and `get_news`. Weather's sync and async handlers
previously spoke a complete forecast but returned only `True`, preventing Live
from receiving measured fields. They now return structured weather data while
preserving the spoken response. News previously returned a truthy fallback
string when headlines were unavailable or fetching raised, which could be
reported as success; those paths now return a truthful failure while successful
news text remains compatible. Tests mock the providers and speech only; no
network request or external credential was used.

## Batch 14 repair

Seven non-Android actions were repaired and verified at the structured Live
boundary: `clear_notes`, `close_process`, `zip`, `extract`, `recycle`,
`remember_contact`, and `forget_contact`. The handlers now return meaningful
operation details instead of bare booleans; missing paths, missing process
names, contact save/remove failures, and no-match process results are reported
truthfully. Reviewed schemas now validate required arguments and inject the
shared action where legacy handlers require it. Tests mock note persistence,
process enumeration/termination, archive operations, recycle-bin handling,
and contact storage; no user data, process, file, or contact was changed.

## Batch 15 repair

Seven non-Android browser actions were repaired and verified: `google_search`,
`open`, `youtube_play_first`, `youtube_pause`, `youtube_resume`,
`youtube_next`, and `youtube_previous`. Google search now returns the actual
browser-context result list and count instead of only `True`; website opening
returns the opened target details. The YouTube actions received reviewed
structured Live schemas and boundary tests for queue navigation, playback
success/failure, and empty queues. Tests mock browser navigation and YouTube
playback only; no browser or external service was opened.

## Batch 16 repair

Five non-Android actions were repaired and verified at the mocked structured
Live boundary: `remember_email_contact`, `forget_email_contact`,
`schedule_whatsapp_message`, `reschedule_scheduled_whatsapp`, and
`youtube_search`. The email contact handlers now expose reviewed required
schemas and structured success/failure results. WhatsApp scheduling and
rescheduling return the persisted item to Live callers while preserving the
legacy literal-`True` contract for non-Live callers. YouTube search has a
focused boundary test proving that its actual result list and count propagate.
No email, WhatsApp, browser, or external service was called; all boundaries
were mocked.

## Batch 17 repair

Five non-Android actions were repaired and verified at the mocked structured
Live boundary: `close`, `create_image`, `create_reminder`,
`screen_vision_analyze`, and `send_email`. Browser close, image generation,
and email sending now have reviewed structured schemas with argument
validation. Reminder creation now returns the persisted reminder item to Live
callers while preserving the legacy boolean return for non-Live callers.
Screen vision success and capture-failure result paths are covered with a
mocked image boundary. No browser was closed, image service was contacted,
screen was captured, or email was sent.

## Batch 18 repair

Five non-Android actions were repaired and verified at the mocked structured
Live boundary: `screenshot_ai`, `home_automation`, `whatsapp_open`,
`whatsapp_close`, and `whatsapp_send_message`. Screenshot-file analysis now
has an explicit Live schema that reports the existing unsupported behavior
truthfully. Home automation now has validated command/device parameters.
WhatsApp send results now distinguish missing input, send failure, and send
success for Live callers while preserving legacy boolean behavior. Open/close
paths received focused success/failure boundary coverage. No screenshot was
read, ESP32 command sent, WhatsApp application opened/closed, or message sent.

## Batch 19 repair

Four non-Android WhatsApp media actions were repaired and verified at the
mocked structured Live boundary: `whatsapp_send_file`,
`whatsapp_send_latest_photo`, `whatsapp_send_latest_screenshot`, and
`whatsapp_send_selected_file`. Their Live results now distinguish unavailable
assets, invalid selection state, failed sends, selection requests, and actual
mocked success while preserving legacy boolean returns. An attempted read-only
vision-schema batch was abandoned because importing the camera vision handler
initialized Ultralytics/AV/Torch dependencies and exceeded the safe timeout;
no camera behavior or shared camera code was changed.

## Batch 20 repair

One remaining safe non-Android action was repaired: `whatsapp_wait_message`.
The handler now returns a structured Live `needs_input` result after storing
the recipient, while preserving the legacy boolean return for non-Live
callers. Required-contact validation and mocked follow-up state were tested.
No WhatsApp application was opened and no message was sent. The remaining
PARTIAL actions were deliberately deferred because they are camera/hardware
paths with unsafe optional imports, consequential restart/sleep/volume
controls, or excluded phone-call functionality.

## Batch 21 audit

No additional safe repair was justified. The remaining 20 PARTIAL actions are
camera/vision hardware paths, consequential restart/sleep/volume controls, or
excluded WhatsApp phone-call actions. Camera imports were not retried, no
system-control action was executed, and no excluded path was inspected or
modified. Existing Batch 19/20 mocked contracts were rerun successfully.

## Batch 12 repair

Five non-Android actions were repaired and verified at the structured Live
boundary: `maps_open`, `maps_directions`, `translate_open`,
`open_personal_link`, and `welcome`. Maps already had reviewed schemas, but
their successful browser-open path lacked a Live result contract test. The
other three actions were only generic-dispatch capabilities, so they now have
reviewed schemas and structured routing; personal-link names are required and
validated before execution. Tests mock browser opening and local speech, and
exercise browser failure and missing-destination/argument paths. No real
browser navigation or external request was performed.

## Per-skill audit matrix

All actions below were found in the current registry/AST inventory. `PASS_STATIC`
is intentionally used where no focused unit or independent runtime evidence
exists. Protected skills are included for traceability and were read-only in
this audit.

| Skill module | Registered actions | Live/schema and execution evidence | Status |
|---|---|---|---|
| ai.clarify | clarify | Generic Live dispatch; focused unit evidence | PASS_UNIT |
| android_control.android_control | 20 Android actions | EXCLUDED BY USER — NOT MODIFIED OR TESTED | EXCLUDED |
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
| media.spotify | spotify_close, spotify_next, spotify_open, spotify_pause, spotify_play, spotify_play_song, spotify_previous, spotify_volume_down, spotify_volume_up | Generic dispatch; focused argument/dispatch contract evidence; no real playback | PASS_UNIT |
| memory.notes | clear_notes, create_note, list_notes | Generic dispatch; static review | PASS_STATIC |
| memory.reminders | cancel_reminder, create_reminder, list_reminders | Structured schemas; focused reminder regressions; owner-reported runtime | PASS_UNIT |
| navigation.maps | maps_directions, maps_open | Structured Live success/failure contracts with mocked browser opening; no external navigation | PASS_UNIT |
| navigation.translate | translate_open, translate_text | `translate_text` structured schema and mocked service-result contract; browser opening remains untested | PASS_UNIT |
| network.bluetooth | bluetooth_devices, bluetooth_status | Generic dispatch; hardware side effects excluded | PASS_STATIC |
| network.weather | weather | Structured Live path; delayed-result repair covered by focused tests | PASS_UNIT |
| network.wifi | wifi_list, wifi_off, wifi_on, wifi_status | Structured schemas and mocked command/result contracts; no real Wi-Fi mutation or scan | PASS_UNIT |
| news.news | get_news | Generic dispatch; no external request | PASS_STATIC |
| payments.payments | make_payment | EXCLUDED BY USER — Android-dependent payment path | EXCLUDED |
| phone_call.phone_call | 8 ADB/Android-dependent actions | EXCLUDED BY USER — NOT MODIFIED OR TESTED | EXCLUDED |
| screen.clipboard | clipboard | Generic dispatch; static review | PASS_STATIC |
| screen.screen_vision_skill | screen_vision_analyze | Structured Live image response and correlation repair; no independent runtime | PASS_STATIC |
| screen.screenshot | screenshot | Structured Live capture; owner-reported runtime only | PASS_STATIC |
| screen.screenshot_ai | screenshot_ai | Generic dispatch; no image-service call | PASS_STATIC |
| system.battery | battery | Generic dispatch; static review | PASS_STATIC |
| system.brightness | brightness | Structured Live path; backend import/unavailable behavior covered with mocks; real display control excluded | PASS_UNIT |
| system.process | close_process, running_apps | Generic dispatch; running-apps unit evidence; termination excluded | PASS_UNIT |
| system.system | lock, restart, shutdown, sleep, terminate_jarvis | Dedicated Live schemas; lock/shutdown/application shutdown routing and confirmation unit evidence; real OS effects excluded | PASS_UNIT |
| system.taskmanager | taskmanager | Structured Live result contract with mocked psutil metrics | PASS_UNIT |
| system.volume | volume | Generic dispatch; hardware mutation excluded | PASS_STATIC |
| utilities.search | search_file | Generic dispatch; local review only | PASS_STATIC |
| utilities.time_skill | time | Structured Live result contract with deterministic clock mock | PASS_UNIT |
| web.personal_links | open_personal_link, show_personal_links | Structured personal-link schema and mocked browser-open contract; no configured link was opened | PASS_UNIT |

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

10. The original static inventory undercounted file-intelligence actions
    registered inside literal loops and memory actions registered through the
    aliased `ai_register` decorator. The audit tool now expands those safe
    literal registrations, so the generated manifest reflects 178 actions and
    includes explicit in-scope/excluded labels. This was an audit defect, not a
    Live execution defect.

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
- Safe non-Android test subset (Android/ADB and Android-dependent tests
  excluded): **369 passed, 4 skipped, 13 warnings, 31 subtests passed**.
- Batch 3 focused tests: **9 passed**.
- Batch 4 focused tests: **7 passed**.
- Batch 5 focused tests: **6 passed**; the safe suite also caught and verified
  correction of two accidental return-contract regressions before completion.
- Batch 6 focused tests: **5 passed**.
- Batch 7 focused tests: **5 passed**.
- Batch 8 focused tests: **5 passed, 1 warning**.
- Batch 9 focused tests: **7 passed, 2 warnings**.
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
- Batch 16 initially exposed a legacy regression because scheduling returned a
  Live-shaped dictionary to callers requiring `is True`; the implementation
  was corrected to return structured results only inside Live execution and
  retain the legacy boolean contract elsewhere. The rerun passed the complete
  safe subset above.
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
- Batch 20 safe regression verification: the non-inventory safe subset passed
  **364 tests**, and the two inventory tests passed **5 tests in 39.43s** with
  `faulthandler_timeout=60`; combined evidence is **369 passed, 4 skipped,
  13 warnings, 31 subtests passed**. The initial all-in-one run emitted a
  20-second diagnostic during the known slow inventory scan and was stopped;
  it did not report a test failure.
- Batch 21 focused regression command:
  `python -m pytest -q tests/test_live_batch19_media_contracts.py tests/test_live_batch20_contracts.py --maxfail=1 -o faulthandler_timeout=20`
  — **3 passed**.
- Batch 21 safe regression verification: **364 passed, 4 skipped, 13
  warnings, 31 subtests** in the non-inventory subset; inventory tests passed
  **5 tests in 35.58s** with `faulthandler_timeout=60`.
- The earlier 352-test result is historical pre-exclusion evidence; the full
  suite was not rerun in this continuation because it includes user-excluded
  Android/ADB tests.
- A prior dynamic loader check reported **48/48 configured modules loaded, 0
  failures**. It is retained as historical evidence and was not repeated after
  the user’s strict Android/ADB exclusion.
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
