<p align="center">
  <img
    src="https://readme-typing-svg.herokuapp.com?font=Poppins&weight=600&size=24&pause=1000&color=00C2FF&center=true&vCenter=true&width=850&lines=🤖+JARVIS PRO+Desktop+Voice+Assistant;🎙️+Hey+JARVIS PRO+%7C+Wake+Word+Activated;🖥️+Windows+Desktop+Automation;⚡+Python+%7C+Voice+Control+%7C+AI;🚀+Iron-Man+Style+Desktop+Assistant"
    alt="Typing Header"
  />
</p>

<p align="center">
  <img src="https://giffiles.alphacoders.com/212/212508.gif" alt="JARVIS PRO HUD" width="100%">
</p>

<p align="center">
  <strong>ASSISTANT – JARVIS PRO Desktop Voice Assistant</strong>
</p>

<p align="center">
  A powerful Windows voice-controlled desktop assistant built with Python,
  featuring wake-word detection, real-time animated HUD, application control,
  system automation, and voice feedback — all packed into a single EXE.
</p>

---

# JARVIS PRO Desktop Voice Assistant

## ✨ Overview

JARVIS PRO is a Windows-focused desktop voice assistant built around a Python
automation runtime, deterministic command routing, AI providers, and a
real-time desktop HUD.

JARVIS PRO combines:

- Voice interaction and wake-word invocation
- Online and optional offline voice modes
- AI routing, conversation context, and clarification handling
- Windows desktop automation
- Browser control through a dedicated Chromium/CDP runtime
- Android control through a shared ADB bridge
- Communication, media, navigation, and personal-link skills
- Local memory, notes, reminders, and profile context
- Camera, object-detection, face-registration, and screen-vision features
- A native Next.js/React HUD and an optional remote dashboard

## 🚀 Features

### Voice and AI

- Deterministic wake-word handling for the configured assistant name and
  explicit JARVIS PRO/JARVIS aliases.
- Online voice mode using SpeechRecognition and Edge TTS.
- Offline voice mode using Faster-Whisper, local Ollama, and Piper TTS.
- Ollama, Gemini, and OpenAI provider implementations.
- Model selection, streaming contracts, provider fallback, and temporary
  quota/rate-limit cooldowns.
- Conversation context, natural follow-ups, clarification state, and live
  Gemini conversation mode.
- Developer/coding request detection and routing.

### Desktop Automation

- Application and browser launching/navigation
- File and folder operations
- Volume, brightness, battery, and process controls
- Wi-Fi and Bluetooth status/actions
- Screenshots, clipboard access, and screen analysis
- Task Manager and Windows power actions such as lock, sleep, restart, and
  shutdown

### Browser and Web

- Dedicated persistent Chromium profile
- Chrome, Edge, and Chromium executable discovery
- Local CDP ownership and Playwright browser control
- Google search, page navigation, tabs, scrolling, and result references
- YouTube search and playback controls
- Spotify, Maps, translation, weather, news, and personal-link integrations

### Vision

- Camera preview, capture, and recording
- YOLO-based person/object detection
- Temporal scene stabilization and scene descriptions
- Local face registration, recognition, and deletion
- Screen screenshots and screen-vision analysis

### Communication and Media

- WhatsApp desktop automation, messaging, scheduling, files, photos, and
  call/video-call actions
- Gmail sending and email-contact management
- Local contacts and GitHub/ChatGPT search actions
- Spotify playback controls
- Notes, reminders, memory, and profile-backed context

### Android

- Shared Android/ADB transport under <code>services/android/</code>
- USB and wireless ADB device discovery/connection
- Device status and device information
- Phone-scoped app launching
- Phone-call monitoring and outgoing call actions
- User-driven payment-app launching

### HUD and Remote Dashboard

- Native <code>pywebview</code> desktop window
- Next.js, React, and Three.js HUD frontend
- Python-to-web HUD event bridge
- Live assistant state, activity, system telemetry, call state, and notifications
- Mobile-friendly dashboard with pairing, command submission, history, settings,
  Android controls, uploads, and Agent controls

Feature availability depends on Windows permissions, installed applications,
hardware, model files, network access, and configured credentials.

## 🧠 How JARVIS PRO Works

~~~text
User
  |
  +--> Voice input
  +--> HUD text
  +--> Remote dashboard text
  |
  v
Input listener / dashboard endpoint
  |
  v
core.dispatcher.dispatch()
  |
  +--> Assistant-name normalization
  +--> Pending clarification / follow-up handling
  +--> core.fast_router.fast_route()
  |      |
  |      +--> Deterministic domain router
  |      +--> core.registry.execute(action)
  |
  +--> Brain / intent / developer routing
  +--> Conversation and planner path
  +--> AI-generated action plan
  |
  v
Registered skill
  |
  v
Service / Windows API / browser / Android / external API
  |
  +--> Voice response
  +--> HUD event
  +--> Remote dashboard event
~~~

| Component | Responsibility |
| --- | --- |
| <code>core.dispatcher</code> | Shared command entry point and priority ordering for voice, HUD, and remote text. |
| <code>core.fast_router</code> | Tries deterministic domain routers before the general AI/planner path. |
| <code>core/routers/</code> | Converts command patterns into action plans for browser, files, vision, Android, payments, calls, and other domains. |
| <code>core.registry</code> | Stores registered action handlers and executes them by action name. |
| <code>brain/</code> | Conversation context, intent understanding, clarification, developer routing, planning, and follow-up resolution. |
| <code>skills/</code> | Capability modules that register executable actions. |
| <code>services/</code> | Shared adapters for Android, Windows, communication, media, external APIs, and related integrations. |
| <code>voice/</code> | Speech input, TTS, offline mode, voice state, queues, interruption, and Agent. |
| <code>hud/</code> | Python HUD state/events, telemetry, native window, and web bridge. |
| <code>dashboard/server.py</code> | FastAPI dashboard/API layer that forwards commands into the existing dispatcher. |

### Startup flow

<code>main.py</code> is the application entry point:

1. Load environment values and configuration.
2. Select online or offline voice mode from network availability.
3. Load configured skill modules with <code>skills/loader.py</code>.
4. Initialize memory and start supporting services, including the phone-call
   monitor when available.
5. Start the Python HUD runtime and web bridge.
6. Start the Next.js HUD from <code>hud/web</code>.
7. Start the dashboard and voice runtime.
8. Open the native <code>pywebview</code> HUD.
9. On window close, Ctrl+C, or runtime failure, stop the listener, services,
   HUD bridge, and web process.

The web HUD is started by the Python application; it is not a second command
brain.

## 🎙️ Voice and Conversation

### Voice modes

| Mode | Runtime | Requirements |
| --- | --- | --- |
| Online | SpeechRecognition input, shared assistant runtime, and Edge TTS | Microphone, audio dependencies, and network/service availability |
| Offline | Faster-Whisper STT, shared local action layer, Ollama, and Piper | Local models, audio dependencies, and a reachable Ollama instance |

Offline mode reuses the shared core, registry, skills, HUD, and dashboard
architecture. It changes the voice and AI providers rather than creating a
separate action system.

### Invocation and follow-ups

The name system builds deterministic wake-word phrases from the configured
assistant name and explicit aliases, including forms such as:

- <code>jarvis</code>, <code>hey jarvis</code>, <code>hello jarvis</code>

The dispatcher strips a recognized invocation before routing the remaining
command. Pending clarification, email composition, face registration, browser
references, and other follow-up state are handled before a reply is treated as
a new command.

Agent is registered after core initialization through:

- <code>start_agent</code>
- <code>stop_agent</code>
- <code>agent_status</code>

## 🖥️ Desktop Automation

| Area | Examples |
| --- | --- |
| Applications | Open and close applications through the Windows/service layer |
| Files | Create, open, copy, move, rename, delete, archive, and inspect files/folders |
| Browser | Open, search, navigate, scroll, refresh, and manage tabs |
| System | Lock, sleep, restart, shutdown, and Task Manager actions |
| Audio | Volume and playback controls |
| Display | Brightness controls |
| Network | Wi-Fi and Bluetooth status/actions |
| Processes | List running apps and close selected processes |
| Screen | Screenshots, clipboard operations, and screen-vision analysis |

Some actions use optional Windows-only libraries or require user permissions.

## 🌐 Browser System

JARVIS PRO owns a dedicated Chromium browser runtime instead of attaching to an
arbitrary browser debugging endpoint.

The browser system:

- Detects Chrome, Edge, or Chromium.
- Creates or reuses a persistent per-user browser profile.
- Uses a local CDP endpoint and Playwright.
- Records ownership/session information so only a verified JARVIS PRO-launched
  browser session is reused.
- Supports tabs, navigation, scrolling, Google search, YouTube, and sequential
  result references.

Default profile location:

~~~text
%LOCALAPPDATA%\JARVIS\ChromeProfile
~~~

This profile may contain browser sessions and cookies. It is machine-local and
must not be committed.

Browser configuration variables:

| Variable | Purpose |
| --- | --- |
| <code>JARVIS_BROWSER_CDP_HOST</code> | Local CDP host; the implementation requires a local-only host. |
| <code>JARVIS_BROWSER_CDP_PORT</code> | Preferred CDP port; default is <code>9223</code>, with a fallback port if occupied. |
| <code>JARVIS_BROWSER_EXECUTABLE</code> | Optional explicit Chrome/Edge/Chromium executable. |
| <code>JARVIS_BROWSER_PROFILE_DIR</code> | Optional persistent profile directory. |

## 📱 Android Control

JARVIS PRO uses one shared Android/ADB bridge:

~~~text
Android Control / Phone Calls / Payment
              |
              v
       services/android/
              |
              v
             ADB
              |
              v
       Connected Android device
~~~

The bridge:

- Resolves ADB from <code>ANDROID_ADB_PATH</code>, the system <code>PATH</code>,
  or the standard Windows platform-tools location.
- Uses safe argument-list subprocess calls rather than shell command strings.
- Supports USB-connected devices and validated wireless ADB endpoints.
- Can list/check devices, inspect device information, and launch named apps.
- Is exposed in the HUD through Android status/connect/disconnect controls.

Wireless ADB uses an address and port supplied through the Android connection
UI or service call. The default ADB TCP port is <code>5555</code>; no device
address is embedded in this README.

Desktop and phone commands remain separate:

| Command type | Routing |
| --- | --- |
| <code>open camera</code> | Desktop camera skill |
| <code>open Chrome</code> | Desktop browser skill |
| <code>open phone camera</code> | Android/ADB phone skill |
| <code>open phone Chrome</code> | Android/ADB phone skill |

Generic desktop commands do not silently redirect to the phone. Android ADB is
optional and independent from the remote dashboard.

Configuration variables:

- <code>ANDROID_ADB_PATH</code>
- <code>ANDROID_DEVICE_ID</code>
- <code>ANDROID_DEFAULT_PAYMENT_APP</code>

## 💳 Payment

Payment is intentionally user-driven.

The payment skill can:

- Open the configured/default Android payment application.
- Open the Android <code>upi://pay</code> app chooser when no app is selected.
- Provide spoken instructions for the user to continue in the official app.

Examples include PhonePe, Google Pay, or Paytm when installed and selected by
the user or configuration.

The official payment application remains responsible for:

- QR scanning
- Recipient selection
- Amount review
- PIN, OTP, CVV, biometric, or other security checks
- Final authorization and payment confirmation

JARVIS PRO does not scan payment QR codes with its own camera, enter payment
credentials, simulate authorization taps, or claim that a transfer succeeded.

Payment-app launching uses the Android/ADB bridge. It does not require the
remote dashboard.

## 📞 Phone Calls

The Phone Call skill is implemented under <code>skills/phone_call/</code> and
uses the Android/ADB bridge.

It supports:

- Outgoing calls by phone number or remembered contact
- Caller-name lookup from phone contacts when available
- Read-only incoming-call monitoring
- HUD/voice notifications for ringing, active, outgoing, disconnected, and
  missed-call states
- Recent missed-call lookup when the device exposes the call log

Outgoing call requests and the device's own phone UI determine exact on-device
behavior. Opening a dialer screen and completing a call are not the same
operation; device permissions and Android behavior still apply.

Answer, reject, and end actions are registered, but the current implementation
explicitly reports that safe ADB control is unavailable on the audited Android
device and asks the user to operate the phone manually. JARVIS PRO should not be
treated as providing automatic telecom control.

## 👁️ Vision

The vision system separates camera capture, object detection, face recognition,
and screen analysis:

~~~text
Camera
  |
  v
CameraManager / VisionEngine
  |
  v
YOLO person/object detection
  |
  +--> Scene analysis and temporal stabilization
  +--> Face crop -> local OpenCV LBPH recognition
~~~

Supported areas include:

- Camera status, preview, capture, and recording
- YOLO scene descriptions, counts, positions, and target/locate actions
- Face registration, cancellation, recognition, and deletion
- Screen screenshots and screen-vision analysis

Face samples are stored locally under <code>data/faces/</code>. Availability
depends on OpenCV, Ultralytics, model assets, hardware, and Windows permissions.

## 🖥️ HUD

The HUD has two cooperating layers:

1. Python publishes state and events through <code>hud/bus.py</code>,
   <code>hud/manager.py</code>, <code>hud/integration.py</code>, and the passive
   web bridge.
2. The Next.js/React client consumes those events and renders the interface.

The frontend includes:

- Assistant orb/cockpit views
- Activity and response history
- Listening, thinking, speaking, executing, and error states
- CPU, RAM, battery, system status, and uptime telemetry
- Phone-call status display
- Android connection controls
- Personal-link and customization controls
- Independent AI chat
- Three.js/GLB visual assets and optional hand-tracking helpers

The native window is provided by <code>pywebview</code>. The Python runtime
starts the Next.js development server and opens the local HUD in that native
window.

## 📡 Remote Dashboard

The remote dashboard is a separate FastAPI/Uvicorn transport and web UI. It
does not create another assistant brain.

It provides, where configured:

- Short-lived pairing PIN generation
- Authenticated sessions
- Mobile-friendly command submission
- Command/event history
- WebSocket events and phone microphone/audio paths
- Voice and listener controls
- AI chat endpoints
- Settings/customization
- Android status and connection controls
- Upload/download and desktop integration endpoints
- Direct Agent stop control

The active application path constructs <code>DashboardServer</code> in
<code>dashboard/server.py</code> and passes the existing
<code>core.dispatcher.dispatch</code> function as its command handler.

Remote Control and Android ADB are different systems:

| System | Purpose |
| --- | --- |
| Remote dashboard | Sends commands/events between a browser or phone UI and the JARVIS PRO runtime. |
| Android/ADB bridge | Communicates directly with a connected Android device. |

The dashboard is optional. Android ADB and payment-app launching do not depend
on the dashboard.

## 🧩 Skills

Skills are Python modules that register named actions with
<code>core.registry</code>. <code>skills/loader.py</code> imports the configured
skill list during startup and records successful and failed imports.

| Category | Capability |
| --- | --- |
| Assistant | Greetings, assistant responses, welcome, and goodbye |
| AI | Clarification action and AI-facing helpers |
| Automation | Home automation and ESP32-oriented integration |
| Browser | Browser opening, Google search, YouTube, navigation, and tab controls |
| Camera | Camera capture, recording, object vision, and face operations |
| Android | ADB checks, device information, and phone-scoped app launch |
| Payments | User-driven payment-app/UPI chooser launch |
| Phone calls | Outgoing calls, monitoring, contacts, status, and missed calls |
| Communication | WhatsApp, Gmail, contacts, GitHub, and ChatGPT search |
| Files | File/folder operations, recent files, recycle bin, ZIP/extract |
| Media | General media, Spotify, and image-generation actions |
| Memory | Memory, notes, and reminders |
| Navigation | Maps and translation |
| Network | Weather, Wi-Fi, and Bluetooth |
| News | News retrieval |
| Screen | Screenshot, clipboard, and screen vision |
| System | Power, battery, brightness, volume, processes, and Task Manager |
| Utilities | Time and file search |
| Web | Configured personal links |

Important package paths include <code>skills/browser/</code>,
<code>skills/camera/</code>, <code>skills/android_control/</code>,
<code>skills/communication/</code>, <code>skills/payments/</code>,
<code>skills/phone_call/</code>, <code>skills/system/</code>, and
<code>skills/web/</code>.

## 💻 Developer and Coding Capabilities

The brain contains a developer-oriented subsystem that detects programming and
project requests and routes them separately from ordinary desktop commands.

Examples of request types supported by the source include:

- Creating a Python, JavaScript, C++, Arduino, or ESP32 project
- Fixing or updating code
- Building a React or web project
- Editing files through the developer editor path
- Analyzing a workspace, project, language, framework, or runtime

The developer subsystem includes analysis, planning, prompt construction,
generation, validation, repair, workspace builders, editor/patch tooling,
backup/rollback support, and developer memory. External model availability and
active-project context determine what can be completed.

## 📦 Installation

### Prerequisites

- Windows with Python 3 available.
- Node.js and npm for the HUD.
- A microphone and audio output for voice operation.
- Optional: Ollama and a local model for offline/local AI.
- Optional: Chrome, Edge, or Chromium for browser skills.
- Optional: Android platform-tools/ADB for phone skills.
- Optional: credentials or installed desktop applications for integrations such
  as Gemini, OpenAI, YouTube, Spotify, Gmail, and WhatsApp.

### Install Python dependencies

From the repository root:

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

The current <code>requirements.txt</code> contains the Python dependencies for
the core runtime, voice modes, AI providers, dashboard, browser, Windows
automation, vision, and integrations.

### Install HUD dependencies

~~~powershell
Set-Location hud\web
npm install
Set-Location ..\..
~~~

### Optional Ollama setup

Install Ollama separately, start its local service, and install a model matching
your configuration. The source default is:

~~~text
Model: qwen2.5:3b
Endpoint: http://localhost:11434/api/generate
~~~

<code>OLLAMA_API_URL</code> can override the endpoint. Offline voice AI also
supports an explicit <code>OLLAMA_MODEL</code> environment value.

### Optional Android setup

Install Android platform-tools and ensure <code>adb</code> is available in
<code>PATH</code>, or set:

~~~powershell
$env:ANDROID_ADB_PATH = "C:\path\to\adb.exe"
~~~

For a selected device, set <code>ANDROID_DEVICE_ID</code> or use the Android
connection controls in the HUD. Wireless ADB accepts an address and port through
the connection UI.

## ▶️ Run JARVIS PRO

From the repository root:

~~~powershell
python main.py
~~~

<code>main.py</code> starts the configured core, skills, HUD, dashboard, and
voice mode. The Next.js HUD is started automatically by the Python application.
When the dashboard is available, the runtime prints its URL and pairing PIN.

The shortcut-safe launcher is also available:

~~~powershell
python run_jarvis.py
~~~

It writes startup output to the runtime log path under <code>data/logs/</code>.

### Run the HUD separately

For frontend development:

~~~powershell
Set-Location hud\web
npm run dev
~~~

For a frontend production build:

~~~powershell
npm run build
npm run start
~~~

The Python application normally owns the integrated startup lifecycle; use the
separate HUD commands when working on the frontend independently.

## ⚙️ Configuration

### Environment file

Copy the template and fill only the values for integrations you use:

~~~powershell
Copy-Item .env.example .env
~~~

Never commit <code>.env</code>, OAuth files, tokens, cookies, or browser
profiles.

Important environment variables include:

| Variable | Purpose |
| --- | --- |
| <code>GEMINI_API_KEY</code> | Gemini provider and Agent access |
| <code>OPENAI_API_KEY</code> | OpenAI provider access |
| <code>YOUTUBE_API_KEY</code> | YouTube API integration |
| <code>SPOTIFY_CLIENT_ID</code> / <code>SPOTIFY_CLIENT_SECRET</code> | Spotify integration |
| <code>OLLAMA_API_URL</code> / <code>OLLAMA_MODEL</code> | Local AI endpoint/model |
| <code>ANDROID_ADB_PATH</code> / <code>ANDROID_DEVICE_ID</code> | ADB executable and selected device |
| <code>ANDROID_DEFAULT_PAYMENT_APP</code> | Default payment application |
| <code>JARVIS_BROWSER_CDP_HOST</code> / <code>JARVIS_BROWSER_CDP_PORT</code> | Local browser debugging settings |
| <code>JARVIS_BROWSER_EXECUTABLE</code> / <code>JARVIS_BROWSER_PROFILE_DIR</code> | Browser executable/profile overrides |
| <code>JARVIS_VISION_*</code> | Face-recognition and registration thresholds |
| <code>PERSONAL_*_URL</code> and selected <code>JARVIS_*_URL</code> values | Personal links |

The complete variable-name template is in <code>.env.example</code>. Secret
values and private URLs do not belong in this README.

### Python configuration

- <code>config/settings.py</code>: assistant identity, aliases, AI defaults, and
  vision defaults.
- <code>config/hud_settings.py</code>: HUD-related settings.
- <code>config/personal_links.py</code>: named personal-link slots.
- <code>config/spotify.py</code>, <code>config/youtube.py</code>, and
  <code>config/whatsapp.py</code>: integration configuration helpers.
- <code>data/settings/jarvis_settings.json</code>: persisted assistant/UI
  customization when created by the application.

## 📁 Project Structure

~~~text
JARVIS-PRO/
├── ai
│   ├── core
│   │   ├── commands.py
│   │   ├── model_manager.py
│   │   ├── policy.py
│   │   ├── preference.py
│   │   ├── registry.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── providers
│   │   ├── base.py
│   │   ├── gemini.py
│   │   ├── grok.py
│   │   ├── ollama.py
│   │   └── openai.py
│   ├── __init__.py
│   ├── ai_worker.py
│   ├── chat_prompt.py
│   ├── chat.py
│   ├── conversation.py
│   ├── intent.py
│   ├── llm.py
│   ├── memory_ai.py
│   ├── memory_answer.py
│   ├── memory_confidence.py
│   ├── memory_forget.py
│   ├── memory_intent.py
│   ├── memory_manager.py
│   ├── memory_pipeline.py
│   ├── memory_preference.py
│   ├── memory_profile.py
│   ├── memory_rank.py
│   ├── memory_schema.py
│   ├── memory_search.py
│   ├── memory_semantic.py
│   ├── memory_stats.py
│   ├── memory_store.py
│   ├── memory_view.py
│   ├── memory.py
│   ├── planner_prompt.py
│   ├── planner.py
│   ├── prompt_builder.py
│   ├── query_parser.py
│   └── sentence_buffer.py
├── assets
│   └── icons
│       └── jarvis.ico
├── brain
│   ├── developer
│   │   ├── analyzer
│   │   │   ├── detectors
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_detector.py
│   │   │   │   ├── board_detector.py
│   │   │   │   ├── framework_detector.py
│   │   │   │   ├── intent_detector.py
│   │   │   │   ├── language_detector.py
│   │   │   │   ├── project_detector.py
│   │   │   │   ├── runtime_detector.py
│   │   │   │   └── workspace_detector.py
│   │   │   ├── resolvers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_resolver.py
│   │   │   │   ├── board_resolver.py
│   │   │   │   ├── language_resolver.py
│   │   │   │   └── workspace_resolver.py
│   │   │   ├── rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── board_language_rules.py
│   │   │   │   ├── board_rules.py
│   │   │   │   ├── framework_language_rules.py
│   │   │   │   ├── framework_rules.py
│   │   │   │   ├── intent_rules.py
│   │   │   │   ├── language_rules.py
│   │   │   │   ├── project_rules.py
│   │   │   │   ├── runtime_rules.py
│   │   │   │   └── workspace_rules.py
│   │   │   ├── __init__.py
│   │   │   └── analyzer.py
│   │   ├── api
│   │   │   └── __init__.py
│   │   ├── config
│   │   │   └── config.py
│   │   ├── context
│   │   │   ├── __init__.py
│   │   │   └── developer_context.py
│   │   ├── editor
│   │   │   ├── analyzer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── edit_analyzer.py
│   │   │   │   ├── project_scanner.py
│   │   │   │   └── target_locator.py
│   │   │   ├── models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── edit_context.py
│   │   │   │   ├── edit_plan.py
│   │   │   │   ├── edit_request.py
│   │   │   │   ├── edit_result.py
│   │   │   │   ├── patch.py
│   │   │   │   ├── project_index.py
│   │   │   │   ├── prompt_context.py
│   │   │   │   └── prompt_result.py
│   │   │   ├── parser
│   │   │   │   ├── __init__.py
│   │   │   │   ├── block_parser.py
│   │   │   │   ├── file_parser.py
│   │   │   │   └── response_parser.py
│   │   │   ├── planner
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dependency_analyzer.py
│   │   │   │   ├── edit_planner.py
│   │   │   │   ├── file_selector.py
│   │   │   │   └── instruction_planner.py
│   │   │   ├── prompt_builder
│   │   │   │   ├── __init__.py
│   │   │   │   ├── context_builder.py
│   │   │   │   ├── instruction_builder.py
│   │   │   │   ├── prompt_builder.py
│   │   │   │   └── system_builder.py
│   │   │   ├── provider
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_provider.py
│   │   │   │   └── ollama_provider.py
│   │   │   ├── rules
│   │   │   │   ├── __init__.py
│   │   │   │   └── edit_rules.py
│   │   │   ├── validator
│   │   │   │   ├── __init__.py
│   │   │   │   ├── edit_validator.py
│   │   │   │   └── syntax_validator.py
│   │   │   ├── workspace
│   │   │   │   ├── appliers
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base_applier.py
│   │   │   │   │   ├── python_applier.py
│   │   │   │   │   └── text_applier.py
│   │   │   │   ├── extractors
│   │   │   │   │   ├── arduino_extractor.py
│   │   │   │   │   ├── base_extractor.py
│   │   │   │   │   ├── python_extractor.py
│   │   │   │   │   └── regex_extractor.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── backup_builder.py
│   │   │   │   ├── code_extractor.py
│   │   │   │   ├── file_reader.py
│   │   │   │   ├── patch_applier.py
│   │   │   │   ├── patch_writer.py
│   │   │   │   └── rollback_manager.py
│   │   │   ├── __init__.py
│   │   │   └── editor.py
│   │   ├── enums
│   │   │   ├── __init__.py
│   │   │   ├── board.py
│   │   │   ├── framework.py
│   │   │   ├── intent.py
│   │   │   ├── language.py
│   │   │   ├── project_type.py
│   │   │   ├── runtime.py
│   │   │   └── workspace.py
│   │   ├── generator
│   │   │   ├── metadata
│   │   │   │   ├── __init__.py
│   │   │   │   └── metadata_builder.py
│   │   │   ├── models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── generated_file.py
│   │   │   │   └── generated_project.py
│   │   │   ├── parsers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── markdown_parser.py
│   │   │   │   └── response_parser.py
│   │   │   ├── providers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_provider.py
│   │   │   │   └── ollama_provider.py
│   │   │   ├── rules
│   │   │   │   ├── __init__.py
│   │   │   │   └── generator_rules.py
│   │   │   ├── __init__.py
│   │   │   └── generator.py
│   │   ├── integration
│   │   │   ├── __init__.py
│   │   │   └── active_project.py
│   │   ├── logging
│   │   │   ├── __init__.py
│   │   │   └── logger.py
│   │   ├── memory
│   │   │   ├── models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dependency_record.py
│   │   │   │   ├── edit_record.py
│   │   │   │   ├── file_profile.py
│   │   │   │   ├── memory_record.py
│   │   │   │   ├── project_profile.py
│   │   │   │   ├── session_state.py
│   │   │   │   ├── style_profile.py
│   │   │   │   └── symbol_record.py
│   │   │   ├── rules
│   │   │   │   ├── __init__.py
│   │   │   │   └── memory_rules.py
│   │   │   ├── __init__.py
│   │   │   ├── developer_memory.py
│   │   │   ├── memory_builder.py
│   │   │   ├── memory_context.py
│   │   │   ├── memory_indexer.py
│   │   │   ├── memory_loader.py
│   │   │   ├── memory_manager.py
│   │   │   ├── memory_saver.py
│   │   │   ├── memory_search.py
│   │   │   └── memory_store.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── analysis_context.py
│   │   │   ├── analysis_result.py
│   │   │   ├── developer_request.py
│   │   │   ├── developer_result.py
│   │   │   ├── generation_result.py
│   │   │   ├── project_plan.py
│   │   │   ├── validation_result.py
│   │   │   └── workspace_result.py
│   │   ├── pipeline
│   │   │   ├── __init__.py
│   │   │   └── developer_pipeline.py
│   │   ├── planner
│   │   │   ├── models
│   │   │   │   ├── __init__.py
│   │   │   │   └── execution_plan.py
│   │   │   ├── planners
│   │   │   │   ├── __init__.py
│   │   │   │   ├── arduino_planner.py
│   │   │   │   ├── base_planner.py
│   │   │   │   ├── cpp_planner.py
│   │   │   │   ├── esp32_planner.py
│   │   │   │   ├── general_planner.py
│   │   │   │   ├── javascript_planner.py
│   │   │   │   └── python_planner.py
│   │   │   ├── rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── board_rules.py
│   │   │   │   ├── framework_rules.py
│   │   │   │   ├── language_rules.py
│   │   │   │   └── planner_rules.py
│   │   │   ├── templates
│   │   │   │   └── __init__.py
│   │   │   ├── utils
│   │   │   │   ├── __init__.py
│   │   │   │   └── path_utils.py
│   │   │   ├── __init__.py
│   │   │   └── planner.py
│   │   ├── prompt_builder
│   │   │   ├── builders
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_builder.py
│   │   │   │   ├── context_builder.py
│   │   │   │   ├── instruction_builder.py
│   │   │   │   └── system_builder.py
│   │   │   ├── models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── prompt_context.py
│   │   │   │   └── prompt_result.py
│   │   │   ├── rules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── instruction_rules.py
│   │   │   │   └── system_rules.py
│   │   │   ├── __init__.py
│   │   │   └── prompt_builder.py
│   │   ├── repair
│   │   │   ├── builders
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_builder.py
│   │   │   │   ├── repair_context_builder.py
│   │   │   │   └── repair_instruction_builder.py
│   │   │   ├── models
│   │   │   │   ├── repair_prompt.py
│   │   │   │   ├── repair_request.py
│   │   │   │   └── repair_result.py
│   │   │   ├── __init__.py
│   │   │   ├── local_file_builder.py
│   │   │   ├── merge_builder.py
│   │   │   ├── prompt_builder.py
│   │   │   ├── repair_builder.py
│   │   │   ├── repair_parser.py
│   │   │   ├── repair_provider.py
│   │   │   └── repair.py
│   │   ├── tools
│   │   │   ├── __init__.py
│   │   │   ├── scaffold.py
│   │   │   └── templates.py
│   │   ├── utils
│   │   │   └── __init__.py
│   │   ├── validator
│   │   │   ├── models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── validation_issue.py
│   │   │   │   ├── validation_level.py
│   │   │   │   ├── validation_result.py
│   │   │   │   └── validation_summary.py
│   │   │   ├── rules
│   │   │   │   ├── __init__.py
│   │   │   │   └── validator_rules.py
│   │   │   ├── utils
│   │   │   │   ├── __init__.py
│   │   │   │   └── validation_utils.py
│   │   │   ├── validators
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_validator.py
│   │   │   │   ├── content_validator.py
│   │   │   │   ├── dependency_validator.py
│   │   │   │   ├── file_validator.py
│   │   │   │   ├── framework_validator.py
│   │   │   │   ├── language_validator.py
│   │   │   │   ├── project_validator.py
│   │   │   │   └── structure_validator.py
│   │   │   ├── __init__.py
│   │   │   └── validator.py
│   │   ├── workspace
│   │   │   ├── builders
│   │   │   │   ├── __init__.py
│   │   │   │   ├── file_builder.py
│   │   │   │   ├── folder_builder.py
│   │   │   │   ├── project_builder.py
│   │   │   │   ├── project_name_resolver.py
│   │   │   │   └── workspace_resolver.py
│   │   │   ├── models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── created_file.py
│   │   │   │   ├── created_folder.py
│   │   │   │   └── workspace_result.py
│   │   │   ├── rules
│   │   │   │   ├── __init__.py
│   │   │   │   └── workspace_rules.py
│   │   │   ├── writers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── file_writer.py
│   │   │   │   └── folder_writer.py
│   │   │   ├── __init__.py
│   │   │   └── workspace.py
│   │   ├── __init__.py
│   │   ├── CHANGELOG.md
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── developer.py
│   │   ├── exceptions.py
│   │   ├── README.md
│   │   └── version.py
│   ├── natural
│   │   ├── __init__.py
│   │   ├── conversation_request.py
│   │   ├── interaction_classifier.py
│   │   ├── interaction_decision.py
│   │   ├── interaction_mode.py
│   │   ├── meaning_understanding.py
│   │   ├── natural_bridge.py
│   │   ├── natural_context.py
│   │   ├── natural_pipeline.py
│   │   └── response_strategy.py
│   ├── routing
│   │   └── base_router.py
│   ├── __init__.py
│   ├── ai_pipeline.py
│   ├── brain_controller.py
│   ├── brain_router.py
│   ├── brain.py
│   ├── clarification_manager.py
│   ├── context_builder.py
│   ├── context_types.py
│   ├── conversation_context.py
│   ├── conversation_coordinator.py
│   ├── conversation_manager.py
│   ├── conversation_state.py
│   ├── conversation_understanding.py
│   ├── execution_context.py
│   ├── execution_engine.py
│   ├── followup_execution_bridge.py
│   ├── followup_resolver.py
│   ├── goal_analyzer.py
│   ├── intent_engine.py
│   ├── profile_manager.py
│   ├── prompt_builder.py
│   ├── reasoning_loop.py
│   ├── reference_resolver.py
│   ├── screen_context.py
│   ├── screen_followup.py
│   ├── task_planner.py
│   └── tool_selector.py
├── chatbot
│   ├── __init__.py
│   ├── ai_chat_api.py
│   ├── ai_chat_bot.py
│   ├── ai_chat_clipboard.py
│   └── ai_chat_session.py
├── config
│   ├── __init__.py
│   ├── environment.py
│   ├── hud_settings.py
│   ├── personal_links.py
│   ├── settings.py
│   ├── spotify.py
│   ├── whatsapp.py
│   └── youtube.py
├── core
│   ├── routers
│   │   ├── __init__.py
│   │   ├── android_router.py
│   │   ├── automation_router.py
│   │   ├── browser_router.py
│   │   ├── contact_router.py
│   │   ├── email_router.py
│   │   ├── file_router.py
│   │   ├── file_selection_router.py
│   │   ├── greeting_router.py
│   │   ├── media_router.py
│   │   ├── memory_router.py
│   │   ├── network_router.py
│   │   ├── news_router.py
│   │   ├── payment_router.py
│   │   ├── phone_call_router.py
│   │   ├── schedule_router.py
│   │   ├── spotify_router.py
│   │   ├── system_router.py
│   │   ├── vision_router.py
│   │   ├── weather_router.py
│   │   ├── web_router.py
│   │   └── whatsapp_router.py
│   ├── __init__.py
│   ├── action_memory.py
│   ├── ai.py
│   ├── app_resolver.py
│   ├── assistant_name.py
│   ├── assistant.py
│   ├── browser_context.py
│   ├── browser_reference.py
│   ├── browser_worker.py
│   ├── busy_manager.py
│   ├── camera_manager.py
│   ├── command_queue.py
│   ├── confirmation.py
│   ├── context.py
│   ├── core_state.py
│   ├── diagnostics.py
│   ├── dispatcher.py
│   ├── executor_worker.py
│   ├── executor.py
│   ├── fallback.py
│   ├── fast_router.py
│   ├── file_selection_memory.py
│   ├── hud_bridge.py
│   ├── intent.py
│   ├── interrupt.py
│   ├── listener.py
│   ├── live_execution.py
│   ├── memory.py
│   ├── morning_brief.py
│   ├── notifications.py
│   ├── path_resolver.py
│   ├── paths.py
│   ├── pipeline.py
│   ├── planner_worker.py
│   ├── planner.py
│   ├── plugins.py
│   ├── power.py
│   ├── registry.py
│   ├── router.py
│   ├── runtime.py
│   ├── services.py
│   ├── skill_categories.py
│   ├── speech_queue.py
│   ├── spotify_controller.py
│   ├── startup_brief.py
│   ├── task_manager.py
│   ├── task_queue.py
│   ├── task_worker.py
│   ├── tasks.py
│   ├── voice_queue.py
│   ├── voice_worker.py
│   ├── voice.py
│   ├── wakeword.py
│   ├── whatsapp_memory.py
│   └── workers.py
├── dashboard
│   ├── static
│   │   ├── app.html
│   │   ├── crypto-js.min.js
│   │   └── login.html
│   ├── __init__.py
│   ├── heartbeat.py
│   └── server.py
├── data
│   └── faces
│       └── .gitkeep
├── hud
│   ├── panels
│   │   └── __init__.py
│   ├── web
│   │   ├── app
│   │   │   ├── ai-chat.css
│   │   │   ├── globals.css
│   │   │   ├── globals.css.append
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components
│   │   │   ├── AIChatBot.tsx
│   │   │   ├── HudCockpit.tsx
│   │   │   ├── JarvisOrb.tsx
│   │   │   └── PhoneCallIsland.tsx
│   │   ├── lib
│   │   │   ├── expressiveRobot.ts
│   │   │   ├── flyingRobot.ts
│   │   │   ├── handTracker.ts
│   │   │   ├── hudBridge.ts
│   │   │   ├── jarvisAvatar.tsx
│   │   │   ├── jarvisFullBody.tsx
│   │   │   └── orbScene.ts
│   │   ├── public
│   │   │   └── models
│   │   │       ├── flying_robot.glb
│   │   │       ├── jarvis.glb
│   │   │       ├── jarvis1.glb
│   │   │       └── RobotExpressive.glb
│   │   ├── next-env.d.ts
│   │   ├── next.config.ts
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── tsconfig.json
│   │   └── tsconfig.tsbuildinfo
│   ├── __init__.py
│   ├── adapter.py
│   ├── bus.py
│   ├── desktop_window.py
│   ├── emitter.py
│   ├── event_contract.py
│   ├── events.py
│   ├── integration.py
│   ├── manager.py
│   ├── runtime.py
│   ├── state.py
│   ├── telemetry.py
│   ├── web_bridge.py
│   └── workspace_center.py
├── services
│   ├── android
│   │   ├── __init__.py
│   │   ├── adb_client.py
│   │   ├── android_intents.py
│   │   ├── device_manager.py
│   │   └── models.py
│   ├── contact_manager.py
│   ├── email_contact_manager.py
│   ├── file_manager.py
│   ├── gmail_service.py
│   ├── location.py
│   ├── personal_link_service.py
│   ├── remote_control.py
│   ├── spotify_api.py
│   ├── web_launcher.py
│   ├── whatsapp_api.py
│   ├── whatsapp_parser.py
│   └── windows_automation.py
├── skills
│   ├── ai
│   │   ├── __init__.py
│   │   └── clarify.py
│   ├── android_control
│   │   ├── __init__.py
│   │   └── android_control.py
│   ├── assistant
│   │   ├── __init__.py
│   │   ├── greetings.py
│   │   └── test_greetings.py
│   ├── automation
│   │   ├── ESP CODE.ino
│   │   ├── ESP CODE.txt
│   │   ├── home_automation.py
│   │   ├── init.py
│   │   └── scheduling.py
│   ├── browser
│   │   ├── __init__.py
│   │   ├── browser_ai.py
│   │   ├── browser_config.py
│   │   ├── browser_controller.py
│   │   ├── browser_open.py
│   │   ├── browser_resolver.py
│   │   ├── browser_runtime.py
│   │   ├── navigation.py
│   │   ├── youtube_api.py
│   │   └── youtube.py
│   ├── browser_control
│   │   ├── __init__.py
│   │   └── browser_controls.py
│   ├── camera
│   │   ├── __init__.py
│   │   ├── camera.py
│   │   ├── detector.py
│   │   ├── face_recognizer.py
│   │   ├── face_registration.py
│   │   ├── face_registry.py
│   │   ├── face_speech.py
│   │   ├── scene_analyzer.py
│   │   ├── spatial_analyzer.py
│   │   ├── vision_analyzer.py
│   │   ├── vision_loop.py
│   │   ├── vision_query.py
│   │   ├── vision_skill.py
│   │   └── vision.py
│   ├── communication
│   │   ├── __init__.py
│   │   ├── chatgpt.py
│   │   ├── contact.py
│   │   ├── email.py
│   │   ├── github.py
│   │   └── whatsapp.py
│   ├── files
│   │   ├── __init__.py
│   │   ├── file_info.py
│   │   ├── file_intelligence.py
│   │   ├── files.py
│   │   ├── recent.py
│   │   ├── recycle.py
│   │   └── zip_manager.py
│   ├── media
│   │   ├── __init__.py
│   │   ├── image_generation.py
│   │   ├── media.py
│   │   └── spotify.py
│   ├── memory
│   │   ├── __init__.py
│   │   ├── memory.py
│   │   ├── notes.py
│   │   └── reminders.py
│   ├── navigation
│   │   ├── maps.py
│   │   └── translate.py
│   ├── network
│   │   ├── __init__.py
│   │   ├── bluetooth.py
│   │   ├── weather.py
│   │   └── wifi.py
│   ├── news
│   │   └── news.py
│   ├── payments
│   │   ├── __init__.py
│   │   └── payments.py
│   ├── phone_call
│   │   ├── __init__.py
│   │   ├── monitor.py
│   │   └── phone_call.py
│   ├── screen
│   │   ├── __init__.py
│   │   ├── clipboard.py
│   │   ├── screen_vision_skill.py
│   │   ├── screen_vision.py
│   │   ├── screenshot_ai.py
│   │   └── screenshot.py
│   ├── system
│   │   ├── __init__.py
│   │   ├── battery.py
│   │   ├── brightness.py
│   │   ├── process.py
│   │   ├── system.py
│   │   ├── taskmanager.py
│   │   └── volume.py
│   ├── utilities
│   │   ├── __init__.py
│   │   ├── calculator.py
│   │   ├── search.py
│   │   └── time_skill.py
│   ├── web
│   │   └── personal_links.py
│   ├── __init__.py
│   └── loader.py
├── tools
│   ├── database_delete.py
│   └── windows_integration.py
├── voice
│   ├── models
│   │   └── en_US-lessac-medium.onnx.json
│   ├── offline
│   │   ├── __init__.py
│   │   ├── offline_action_bridge.py
│   │   ├── offline_ai.py
│   │   ├── offline_player.py
│   │   ├── offline_runner.py
│   │   ├── offline_stt.py
│   │   ├── offline_tts.py
│   │   └── offline_voice.py
│   ├── __init__.py
│   ├── agent.py
│   ├── interrupt.py
│   ├── manager.py
│   ├── mode.py
│   ├── offline_piper.py
│   ├── online_edge.py
│   ├── online_runner.py
│   ├── player.py
│   ├── queue.py
│   ├── runner.py
│   ├── speech_state.py
│   ├── speech_text.py
│   ├── state.py
│   └── tts_pipeline.py
├── workspace
├── .env.example
├── format_project_comments.py
├── main.py
├── PROJECT_DOCUMENTATION.md
├── PROJECT_DOCUMENTATION.txt
├── README.md
├── requirements.txt
└── run_jarvis.py
~~~

Generated dependency and cache directories such as
<code>hud/web/node_modules/</code>, <code>__pycache__/</code>,
<code>.pytest_cache/</code>, and <code>voice/cache/</code> are not source
modules.

## 🔑 Key Architecture Files

| File or directory | Purpose |
| --- | --- |
| <code>main.py</code> | Application lifecycle, online/offline startup, HUD, dashboard, voice, and shutdown |
| <code>core/dispatcher.py</code> | Shared command processing and follow-up priority |
| <code>core/fast_router.py</code> | Ordered deterministic routing |
| <code>core/registry.py</code> | Skill/action registration and execution |
| <code>skills/loader.py</code> | Configured skill imports and loader diagnostics |
| <code>brain/</code> | Intent, conversation, clarification, planning, and developer routing |
| <code>services/android/</code> | Shared safe ADB transport and Android device management |
| <code>skills/browser/</code> | Browser configuration, runtime, controller, and web actions |
| <code>dashboard/server.py</code> | Active FastAPI remote/local dashboard |
| <code>hud/</code> | Python event bus, state, telemetry, bridge, and native window |
| <code>hud/web/</code> | Integrated Next.js HUD frontend |
| <code>voice/</code> | Online/offline speech pipelines and Agent |

## 🔐 Safety and Design Boundaries

- Payment authorization stays inside the official Android payment application.
- JARVIS PRO does not handle UPI PINs, OTPs, CVVs, biometrics, or final payment
  authorization.
- Android commands use the shared <code>services/android/</code> bridge and
  target the phone only when the command is explicitly phone-scoped.
- Answer/reject/end phone-call actions are not presented as safe automatic ADB
  controls by the current implementation.
- Browser automation uses a dedicated local profile; browser profile data may
  contain sensitive sessions.
- API keys, OAuth files, tokens, cookies, and private URLs belong in local
  configuration and must not be committed.
- File deletion, process control, power actions, ADB, messaging, email, and
  browser automation are capability-bearing operations. Use them deliberately.

## 🧪 Testing

Test locations include:

- <code>tests/</code>: configuration, JARVIS PRO routing, offline mode, browser
  references, Android/payment routing, vision, phone calls, remote events,
  providers, and personal links.
- <code>brain/tests/</code>: clarification and intent behavior.
- <code>brain/developer/tests/</code>: developer analyzers, planners, generators,
  validators, repair, and workspace behavior.
- <code>brain/developer/editor/tests/</code>: editor, parser, patch, backup,
  rollback, and validation behavior.
- <code>brain/developer/integration/tests/</code>: developer and dispatcher
  integration.
- <code>skills/assistant/test_greetings.py</code>: greeting behavior.

A focused test command is:

~~~powershell
python -m unittest discover -s tests -p "test_*.py"
~~~

The repository also contains deeper developer test suites. Run those separately
when working on the corresponding subsystem. Tests may require optional runtime
dependencies or Windows integrations; this README does not claim that tests
pass in every environment.

No automated test run is claimed for this documentation change.

## 🛠️ Troubleshooting

| Problem | Check |
| --- | --- |
| HUD does not open | Confirm Node/npm is installed, run <code>npm install</code> in <code>hud/web</code>, and inspect runtime logs under <code>data/logs/</code>. |
| Ollama is unavailable | Confirm Ollama is running, the configured model exists, and <code>OLLAMA_API_URL</code> is reachable. |
| Microphone is not detected | Check Windows microphone permissions and the SpeechRecognition/PyAudio or Faster-Whisper dependencies. |
| Android device is unavailable | Confirm ADB is installed, the device is authorized, and <code>ANDROID_ADB_PATH</code>/<code>ANDROID_DEVICE_ID</code> are correct. |
| Wireless ADB fails | Confirm the phone and PC can reach each other, use the correct address/port, and connect through the HUD or Android service. |
| Browser skill fails | Install Chrome, Edge, or Chromium and check the browser executable/profile/CDP environment values. |
| Optional integration fails | Configure only the relevant API/OAuth variables and verify the desktop application or external service is available. |

## 🤝 Contributing and Extending JARVIS PRO

Use the existing architecture boundaries:

1. Add a capability under the appropriate <code>skills/&lt;category&gt;/</code>
   package.
2. Register executable actions with <code>core.registry</code>.
3. Add or update a deterministic router in <code>core/routers/</code> when a
   command needs explicit parsing or priority.
4. Put shared external/API/OS adapters under <code>services/</code>.
5. Put defaults and environment-backed settings under <code>config/</code>.
6. Add focused tests under <code>tests/</code> or the relevant subsystem
   directory.
7. Update this README when user-visible capabilities or architecture change.

Keep skill handlers small and route shared behavior through existing services
and registries. Do not create a second dispatcher or duplicate Android,
browser, HUD, or payment transport.

## 📜 License

No license file or explicit license declaration was found in the repository.
