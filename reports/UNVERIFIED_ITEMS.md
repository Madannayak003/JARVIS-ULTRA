# Unverified or blocked items

- The 145-action manifest is statically routed, but most actions remain `NOT_TESTED` at runtime. The CSV records the exact status per action.
- External integrations (Android/ADB, browser services, email, GitHub, WhatsApp, weather/news, Spotify, home automation, payments, phone calls) require credentials, devices, or user confirmation and were not exercised automatically.
- Camera, face recognition, screen capture, microphone, speaker, and other hardware paths were not run unattended.
- A real authenticated Gemini Live session was not run; therefore end-to-end provider behavior, model tool selection, and final generated wording remain unverified.
- Full-suite collection is blocked by the host security filter's SSL keylog permission error. No SSL verification weakening was attempted.
- Owner-reported runtime notes present in the generated inventory remain explicitly labeled owner-reported; they are not independent evidence from this run.
