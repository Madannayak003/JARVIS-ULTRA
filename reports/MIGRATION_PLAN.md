# JARVIS ULTRA migration plan

## Audit baseline

- Working project root: `JARVIS-PRO (2)\JARVIS-PRO`.
- It is the complete Git repository containing `main.py`, `voice/`, `core/`, `ai/`, `skills/`, `dashboard/`, `hud/`, and `tests/`.
- The original `JARVIS-PRO` and manually renamed `Mark` directories were inspected read-only.
- `Mark` is an action-oriented PyQt/Gemini Live reference (`main.py`, `ui.py`, `actions/`, `memory/`, `dashboard/`). Its local Ollama/OpenAI client in `core/llm_client.py` is not suitable for the Ultra primary runtime.

## Foundation decisions

1. Use the existing `voice.Agent` Live session and `core.live_agent` execution bridge; do not add a competing dispatcher.
2. Centralize the fixed primary model as `config.settings.PRIMARY_GEMINI_LIVE_MODEL`.
3. Use the verified SDK/API model identifier `gemini-3.8-live` for the primary Live session. The installed `google-genai` package is 1.75.0 and exposes `client.aio.live.connect(model=..., config=...)`.
4. Do not pass the obsolete `thinking_config` to the 3.8 Live session; the current Live capability guidance says it is unsupported for that model.
5. Advertise only registered capabilities with reviewed structured schemas. Unknown or unschematized actions are rejected before handlers run.
6. Remove the obsolete offline assistant selection and its exclusive implementation. `main.py` starts Gemini Live directly and does not provide a hidden conversation fallback.

## MARK decisions

- Reuse/adapt: Live connection shape, explicit tool-call response delivery, session memory concepts, and system-monitor/reminder ideas after they are mapped to existing JARVIS handlers.
- Keep existing JARVIS implementation: registry, dispatcher, confirmation flow, browser context, File Intelligence, HUD, memory, and Windows skills.
- Defer: wholesale PyQt HUD replacement, Mark's independent action registry, and Mark's local LLM provider routing.
- Exclude from the primary runtime: automatic Ollama/OpenAI fallback and arbitrary model rotation.

## Next validation order

1. Schema and structured handler unit tests.
2. Python compilation and `git diff --check`.
3. Full offline test suite without credentials.
4. Deliberate real Gemini Live connection and harmless capability call when credentials and audio devices are available.

