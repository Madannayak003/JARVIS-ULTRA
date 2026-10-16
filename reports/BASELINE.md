# JARVIS-ULTRA Gemini Live baseline

Date: 2026-10-11 (Asia/Calcutta)

## Repository state

- Root: `D:/MY FILES/MY-VSCODE/MY-ASSISTANT/JARVIS-ULTRA`
- Branch: `main`
- Worktree was already dirty before this audit. Existing modified files include the Live controller, dispatcher, registry, routers, selected skills, and voice agent. Existing untracked work includes `LIVE_ROUTING_AUDIT.md`, `core/reminder_time.py`, `reports/`, `skill-check-list.txt`, and focused regression tests.
- No reset, checkout, stash, commit, push, dependency installation, or secret/config overwrite was performed.
- No merge-conflict markers were found in the audited source files.

## Configuration

- Required Live model remains `gemini-3.8-live`; configuration is centralized through `get_primary_gemini_live_model()` and `voice/agent.py`.
- Installed SDK: `google-genai 1.75.0`.
- The SDK source confirms `FunctionResponse.parts` accepts `FunctionResponsePart`; `FunctionResponsePart.from_bytes(data=..., mime_type=...)` is available.

## Inventory baseline

The side-effect-free AST audit found 48 configured and existing skill modules, 145 registered callable actions, 27 structured Live schemas, and zero duplicate action names. The complete machine-generated records are in `action_inventory.json` and `SKILL_ACTION_INVENTORY.csv`.

## Test baseline

- Focused Live/edge/browser-vision suite: 36 passed, 15 subtests passed.
- Full repository collection was blocked before project tests ran by a Windows security filter permission error from `ssl.create_default_context()` while importing `aiohttp` through `google-genai`: `PermissionError: [Errno 13] Permission denied: \\\\.\\aswMonFltProxy\\...`.
- No external side-effecting runtime tests were run.
