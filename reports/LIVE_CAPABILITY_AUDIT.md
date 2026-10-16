# JARVIS ULTRA Live Capability Audit

Generated from the safe AST inventory in `tools/live_capability_audit.py`.

## Current inventory

- Configured skill modules: 48
- Existing skill source modules: 48
- Registered callable actions: 145
- Structured Live capability schemas: 21
- Generic dispatcher Live exposure: 145
- Static implementation failures: 0
- Actions with an existing test-file reference: 53

The inventory command is intentionally side-effect free:

```powershell
python tools/live_capability_audit.py > data/live_capability_inventory.json
```

It parses the loader, skill registrations, function definitions, Live schema
catalog, and test references without importing skills or starting hardware,
Torch, MediaPipe, schedulers, audio, or external services.

## Status policy

Every action is marked `PASS` only for static implementation discovery. The
execution and conversational-integration fields remain `NOT TESTED` unless a
specific isolated or real integration test provides evidence. A test-file
reference alone is evidence metadata, not an execution pass.

The generic `jarvis_command` route exposes all registered actions through the
existing dispatcher. Twenty-one reviewed actions additionally have structured
schemas and local argument validation. Actions that require credentials,
network services, hardware, or consequential external effects require isolated
mocks or controlled integration tests before they can be marked `PASS`.

## Verified in this phase

- Static inventory is safe and repeatable.
- 58 focused startup, Live inventory/lifecycle/dispatcher tests pass.
- Python compilation passes for the modified runtime packages.
- TypeScript checking passes for the HUD.

## Not verified here

- Real Gemini Live network/audio recovery.
- Real microphone, camera, MediaPipe, Torch, and desktop capture.
- External news, weather, browser, communication, payment, Android, and home
  automation integrations.
- Full per-action execution and natural-language conversational verification.
- Production HUD build on the Windows SWC/UNC-restricted environment.
