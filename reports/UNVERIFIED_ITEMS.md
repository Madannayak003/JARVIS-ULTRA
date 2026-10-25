# Unverified or blocked items

- The all-repository manifest contains 178 actions; 149 non-Android actions are
  in scope: 116 `PASS`, 20 `PARTIAL`, 0 `FAIL`, and 13 `UNTESTED`. The CSV
  records exact per-action status, classification, and scope.
- Android control, Android-dependent payments, and ADB-dependent phone calls
  are `EXCLUDED_BY_USER — NOT MODIFIED OR TESTED` in this continuation.
- External integrations (browser services, email, GitHub, WhatsApp,
  weather/news, Spotify, home automation) require credentials, devices, or
  user confirmation and were not exercised automatically. Spotify's nine
  Batch 10 actions have mocked Live-boundary contract evidence, but real
  launch/playback remains unverified.
- Camera, face recognition, screen capture, microphone, speaker, and other hardware paths were not run unattended.
- A real authenticated Gemini Live session was not run; therefore end-to-end
  provider behavior, model tool selection, and final generated wording remain
  unverified. The three runtime entries are owner-reported, not independently
  reproduced.
- The safe non-Android test subset passes; the full JARVIS test suite was not
  rerun because it includes user-excluded Android/ADB tests.
- Brightness remains environment-dependent: this host denies importing the display backend, so the capability now loads and returns `unavailable` honestly; a real display-control test still requires a permitted Windows display backend.
- Owner-reported runtime notes present in the generated inventory remain explicitly labeled owner-reported; they are not independent evidence from this run.
- Batch 11's time, task-manager, Wi-Fi, and translation results were verified
  with mocks only. Real Wi-Fi state changes/scans and authenticated
  translation-service behavior remain unverified.
- Batch 12's Maps, Google Translate, personal-link, and welcome paths were
  verified with mocked browser/speech boundaries only. Real browser navigation
  and configured external destinations remain unverified.
- Batch 13's weather and news paths were verified with mocked provider results
  only. Real network availability and current external content remain
  unverified.
- Batch 14's note, process, archive, recycle-bin, and contact paths were
  verified with mocks only. Real user-data mutations remain unverified and
  require explicit confirmation in a live session.
- Batch 15's Google and YouTube paths were verified with mocked browser
  boundaries only. Real browser navigation, playback, and external results
  remain unverified.
- Batch 16's email-contact, WhatsApp-scheduling, and YouTube-search paths were
  verified with mocked Live boundaries only. Real email persistence, WhatsApp
  scheduling/sending, browser search, and Gemini model tool selection remain
  unverified.
- Batch 17's browser-close, image-generation, reminder, screen-vision, and
  email-send paths were verified with mocks only. Real browser, image-service,
  screen hardware, reminder notification, email service, and Gemini model tool
  selection remain unverified.
- Batch 18's screenshot-file, home-automation, and WhatsApp open/close/send
  paths were verified with mocks only. Real screenshot files, ESP32 hardware,
  WhatsApp application state, message delivery, and Gemini model tool selection
  remain unverified.
- Batch 19's WhatsApp media paths were verified with mocks only; no media was
  sent. Camera vision actions remain unverified because their optional
  Ultralytics/AV/Torch import exceeded the safe test timeout, and no shared
  camera code was changed.
- Batch 20's WhatsApp follow-up path was verified with mocks only. Restart,
  sleep, volume, camera/vision, and phone-call actions remain unverified or
  intentionally deferred because they are consequential, hardware-dependent,
  unsafe to import in this environment, or excluded by the user.
- Batch 21 made no additional classifications PASS. The remaining 20 PARTIAL
  actions are intentionally deferred under the safety boundary; real Gemini
  Live, hardware, system-control, and phone-call verification remains absent.
