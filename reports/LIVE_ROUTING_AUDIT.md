# Gemini Live routing audit

## Architecture

`voice.agent` owns the single Gemini Live session and declares `jarvis_command`,
reviewed structured capability tools, and browser tools. Tool calls execute
inside `core.live_execution`, then `core.live_agent` validates and invokes the
existing `core.registry` handler. Natural-language `jarvis_command` calls enter
`core.dispatcher`, which uses `core.fast_router` and the domain routers in
`core/routers/`; the dispatcher captures skill speech/results and sends the
authoritative result back to Live.

## Confirmed defects and repairs

| Defect | Evidence/root cause | Repair |
|---|---|---|
| “Take photo” could become a screenshot | `screenshot` was a reviewed Live capability while physical camera `capture` was not; Live instructions lacked an explicit photo tool choice | Exposed `capture`, `camera_preview`, and `camera_status` with unambiguous descriptions and added camera-first prompt examples. Added camera-specific router aliases. |
| Reminder requests could be reported as unavailable | `create_reminder`, `list_reminders`, and `cancel_reminder` were registered and routed by the dispatcher but absent from `LIVE_CAPABILITY_SCHEMAS` | Added reviewed Live schemas and validation for reminder text, ISO time, and numeric ID. |
| Camera save result was optimistic | `capture()` always returned `True` without checking `cv2.imwrite()` | Check the write result, return an honest structured result, and report failure when saving fails. |
| “what is my name” was not a deterministic personal-context command | Dispatcher only recognized full-profile phrases; the Live prompt did not direct personal-context queries to the dispatcher | Added narrow stored-name lookup, including the observed `mybname` typo, without exposing the full profile. |
| Registry import was coupled to optional provider startup | `core.registry` imported the AI fallback at module import time; the fallback eagerly imported Google GenAI/aiohttp and failed in this host’s SSL security-proxy environment before skill loading | Made the fallback import lazy; known registered actions and registry inspection no longer require provider initialization. |
| Delayed Live action failures could be reported as success | `drain_live_tasks()` gathered with `return_exceptions=True` and discarded outcomes; Live then trusted the initial pending result | Return delayed task outcomes and make all three Live tool branches report failed/exceptional asynchronous work honestly. |

## Router audit

All 22 files in the actual `core/routers/` directory were inspected. They are
assembled by `core.fast_router.ROUTERS` and called by `core.dispatcher.dispatch`;
`core.assistant` also precomputes fast routes for the microphone path. The
routers produce action plans only; registry execution and Live response capture
remain centralized in the dispatcher/Live bridge. Static comparison found 134
registered action names referenced by routers and 11 registered actions without
router literals: browser follow-up tools, AI/planner actions, phone-call
confirmation, process status, and WhatsApp wait-contact. Those are not
automatically defects because they have dedicated Live, planner, or
state-machine callers. The seven specifically requested gaps now have safe
mocked unit evidence; that evidence is distinct from real external-service
runtime verification.

## Offline/Ollama assessment

The follow-up dependency audit removed the exclusive offline voice package,
Piper fallback/model, standalone Ollama provider, Ollama registry entries, and
Ollama-specific configuration. Developer Generator and Editor now call the
central AI service with the explicitly permitted `gemini-3.5-flash-lite` model.
Shared Live audio, Edge TTS, player, queue, state, interruption, and HUD/remote
output paths were retained.

## Verification status

The machine-readable source inventory is produced safely by:

```text
python tools/live_capability_audit.py
```

That inventory records every configured skill module and AST-discovered
registration, including implementation, structured Live exposure, dependency
class, and test references. Action-level runtime tests remain prerequisite-
dependent for camera, desktop, network, and consequential integrations.

Current evidence: 48 configured modules, 48 existing modules, 145 registered
callable actions, and 27 reviewed structured Live actions from the static
inventory. `PASS_STATIC` means the implementation, registration, schema, and
route were statically reconciled; it is not a claim that the action ran. The
owner also supplied a normal Windows CMD log
confirming real Gemini Live connection, all 48 modules loading, camera JPG
capture, desktop PNG screenshot, and persisted/triggered reminder delivery;
the machine-readable inventory records those three action results as
`PASS_LIVE_RUNTIME` with owner-reported evidence. The raw log was not present
in this workspace, so those results were not independently replayed here.
The available frontend build is blocked in this host by Next/SWC failing to
canonicalize the Windows workspace path with `Access is denied` (os error 5).

Executed verification commands and results:

```text
python -m unittest test_live_routing test_action_edges -v  -> 13/13 passed
python -m unittest brain.tests.test_clarification_flow -v  -> 9 passed, 7 environment errors
npx tsc --noEmit                                      -> passed
python -m compileall -q core voice skills test_live_routing.py test_action_edges.py tools/live_capability_audit.py
                                                       -> passed
git diff --check                                      -> passed
```

The seven clarification-flow errors occurred during eager `google.genai` or
`edge_tts`/`aiohttp` initialization when the host SSL security proxy denied
access (`PermissionError` on `\\.\\aswMonFltProxy\\...`); application assertions
were not reached. Security settings and the configured provider were not
changed.

The delayed-task repair is source- and compile-verified, with deterministic
result-semantics tests covering delayed success, structured success, failure,
exception, and pending outcomes. An isolated real event-loop regression test
could not run because this host hangs even on
`asyncio.run(asyncio.sleep(0))`; that is recorded as an environment blocker,
not a passing runtime result. The inventory now reports 135 `PASS_STATIC`, 7
`PASS_UNIT`, and 3 owner-reported `PASS_LIVE_RUNTIME` actions. The seven unit
checks cover YouTube result validation, clarification state, phone confirmation
rejection, media delegation, process listing, WhatsApp waiting state, and
ChatGPT delegation; these are mocked/safe unit checks, not real external
service verification.

## Reminder and scheduler regression pass

The reminder path had three confirmed defects: the router sampled `datetime.now()`
while building a plan and the skill parsed the result as a naive datetime; the
worker compared that naive value with another naive local clock; and the worker
called `voice.manager.speak`, which can enter the Edge TTS path while no Live
turn is active. These defects explain future reminders being interpreted as
already due and the observed `[EDGE TTS]` delivery logs.

The repair adds `core/reminder_time.py` as the authoritative resolver. It captures
one local timezone-aware reference, supports relative seconds/minutes/hours,
12-hour and 24-hour clocks, tomorrow/today, noon, midnight, ISO timestamps,
rollover, and rejects malformed, ambiguous, or past absolute times. Legacy naive
stored timestamps are treated as local time and are not discarded.

Reminder creation now persists normalized aware timestamps and accepts the Live
function-call ID for idempotency. A repeated completion with the same ID returns
the existing reminder instead of creating another one. The scheduler marks a
due reminder completed and persists that state before delivery, preventing
restart/retry duplicates. Background delivery uses HUD notification plus the
existing Windows toast helper; it no longer calls TTS. Foreground legacy skill
confirmations still use the existing voice manager when invoked outside Live.

Focused reminder and routing tests pass 24/24, including deterministic relative,
rollover, AM/PM, 24-hour, tomorrow, invalid/past, persistence, idempotency,
future-not-due, exactly-once, HUD/toast-only delivery, and prior Live
async-result regressions.

The full `tests` collection was attempted: 6 collection errors were caused by
the host SSL security proxy denying `google.genai`, `edge_tts`, or `aiohttp`
initialization with `PermissionError` on `\\.\\aswMonFltProxy\\...`. No security
control, certificate setting, provider, or model was changed.

The separately collected legacy `test_scheduling_upgrade.py` suite ran 1 test
successfully and had 2 failures because its external `JARVIS-PRO` test import
could not replace a temporary Windows schedule file (`WinError 5: Access is
denied`); those failures were not caused by the reminder store or the new
reminder scheduler path.

## Screen vision and YouTube regression pass

The first-request defect was a Live message-ordering/lifecycle issue. The skill
was sending the captured PNG as a separate `send_realtime_input(video=...)`
message while the tool handler immediately sent a function response. The SDK
documents realtime media as nondeterministically ordered, so Gemini could finish
the tool turn before the image was incorporated and return only “I'm analyzing.”
The repair keeps one capture and places the PNG in the correlated
`FunctionResponse.parts` media field sent with the tool response. Internal image
bytes are removed from JSON output, duplicate correlation IDs reuse the cached
frame, and duplicate Live responses are suppressed. This is supported by the
installed Gemini Live SDK; real network/runtime confirmation remains pending
because the host security proxy blocks SDK initialization. No second
conversational provider was introduced.

YouTube search previously returned only `True` after populating `BrowserContext`,
so the Live tool response contained no results and could be described as empty.
It now returns structured result records, count, query, platform, title, URL,
channel/video metadata where available, and an explicit empty-results status.
Non-YouTube searches clear stale YouTube queue state. Pause/resume no longer
captures a pre-emptive speech string as a false success during Live execution;
browser failures propagate. Playback navigation results explicitly state that
navigation was sent while playback state could not be verified by the existing
browser controller.

The focused screen, browser, YouTube, reminder, Live, and action-edge suite now
passes **32 tests plus 7 subtests**. The broader suite limitations above remain
unchanged.
