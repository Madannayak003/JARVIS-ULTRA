# Unverified or blocked items

- The 160-action manifest is statically routed, but most actions remain `NOT_TESTED` at runtime. The CSV records the exact status per action.
- External integrations (Android/ADB, browser services, email, GitHub, WhatsApp, weather/news, Spotify, home automation, payments, phone calls) require credentials, devices, or user confirmation and were not exercised automatically.
- Camera, face recognition, screen capture, microphone, speaker, and other hardware paths were not run unattended.
- A real authenticated Gemini Live session was not run; therefore end-to-end provider behavior, model tool selection, and final generated wording remain unverified.
- The JARVIS `tests/` suite passes; recursive repository collection still reaches the embedded FaceRecognition project, whose `src` import assumes that project is the working directory. No SSL verification weakening was attempted.
- Brightness remains environment-dependent: this host denies importing the display backend, so the capability now loads and returns `unavailable` honestly; a real display-control test still requires a permitted Windows display backend.
- Owner-reported runtime notes present in the generated inventory remain explicitly labeled owner-reported; they are not independent evidence from this run.
