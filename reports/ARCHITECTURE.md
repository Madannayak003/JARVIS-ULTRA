# Verified Gemini Live execution flow

Both microphone input and typed HUD input use the one persistent Gemini Live session in `voice/agent.py`. Typed input calls `send_agent_text()` and does not create a second conversational controller.

The supported execution paths are:

```text
voice or HUD text
  -> persistent Gemini Live session
  -> jarvis_command (natural language) or jarvis_capability__<action> (structured)
  -> argument validation in core/live_agent.py
  -> existing registry/dispatcher/router
  -> existing skill handler
  -> delayed Live task drain, if scheduled
  -> result normalization and truthful error status
  -> correlated FunctionResponse to Gemini Live
  -> Gemini user-facing response
```

All 145 registered actions have the generic `jarvis_command` route. The 27 actions with literal schemas additionally have dedicated structured declarations. Screen analysis removes private transport fields from JSON and sends the captured PNG through the installed SDK's `FunctionResponsePart.from_bytes`, retaining the function-call/correlation ID.

The registry, dispatcher, routers, skill loader, confirmation checks, and permission boundaries remain internal execution infrastructure. No alternate provider or conversational controller is introduced by the Live path.
