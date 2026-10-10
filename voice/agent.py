"""
=============================================================
JARVIS PRO — AGENT
=============================================================

Gemini Live native-audio conversation.

IMPORTANT ARCHITECTURE:

    Normal JARVIS microphone
            |
            | start_agent
            v
    pause normal listener
            |
            v
    ONE persistent Gemini Live session
            |
       +----+----+
       |         |
       v         v
   microphone   speaker
       |         ^
       v         |
      Gemini Live
       |
       +--> receive() completes one TURN
                |
                +--> receive() AGAIN
                |
                +--> receive() AGAIN
                |
                +--> receive() AGAIN
                |
               ...

The Gemini session itself is NOT recreated between turns.

No custom VAD.
No reconnect loop.
No session-resumption loop.
No audio_stream_end after every utterance.

Normal JARVIS architecture remains untouched outside Live mode.
"""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import Optional

import sounddevice as sd

from google import genai
from google.genai import types

from core.dispatcher import dispatch

from core.live_execution import (
    live_execution,
    get_live_responses,
    drain_live_tasks,
)
from core.live_agent import (
    build_live_capability_tool,
    build_live_search_tools,
    execute_live_capability,
    execute_live_open_result,
    execute_live_read_page,
    execute_live_search,
    structured_action_from_tool_name,
)

from hud.integration import HUDIntegration
from config.environment import get_env
from config.settings import (
    get_assistant_display_name,
    get_primary_gemini_live_model,
)
from core.diagnostics import debug_print

# * =============================================================
# * CONFIGURATION
# * =============================================================

# One fixed, centrally configured primary Live model.  Do not accept a runtime
# environment override or silently rotate to another model on failure.
LIVE_MODEL = get_primary_gemini_live_model()

INPUT_RATE = 16000
OUTPUT_RATE = 24000

CHANNELS = 1
DTYPE = "int16"

# * 1024 samples at 16 kHz ~= 64 ms.
BLOCK_SIZE = 1024

INPUT_QUEUE_SIZE = 64


# * =============================================================
# * API KEY
# * =============================================================

def _api_key() -> str:
    """
    Resolve Gemini API key.

    Priority:

        1. GEMINI_API_KEY
        2. config/api_keys.json
    """

    key = get_env("GEMINI_API_KEY").strip()

    if key:
        return key

    config_path = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "api_keys.json"
    )

    try:

        data = json.loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )

        return str(
            data.get(
                "gemini_api_key",
                "",
            )
        ).strip()

    except Exception:

        return ""


# * =============================================================
# * SYSTEM PROMPT
# * =============================================================

def _system_prompt() -> str:
    """
    Load the existing JARVIS prompt and add only the
    Agent behavior rules.
    """

    prompt_path = (
        Path(__file__).resolve().parents[1]
        / "core"
        / "prompt.txt"
    )

    try:

        prompt = prompt_path.read_text(
            encoding="utf-8"
        ).strip()

    except Exception:

        prompt = (
            f"You are {get_assistant_display_name()}, a helpful personal AI assistant."
        )

    assistant_name = get_assistant_display_name()

    live_rules = f"""
=============================================================
AGENT BEHAVIOR
=============================================================

You are {assistant_name} in a natural realtime spoken conversation.

GENERAL BEHAVIOR
- Speak naturally, calmly, and conversationally.
- Do not require a wake word between turns.
- Treat every clearly new user utterance as a new turn.
- Preserve conversation context when the user is clearly
  continuing the previous topic.
- Do not invent a connection between unrelated short inputs.
- If the user's new request is clear, answer it directly.

RESPONSE STYLE
- Keep spoken answers concise unless the user asks for detail.
- Usually answer in one or a few natural sentences.
- Do not repeatedly say:
  "Anything else?"
  "How can I help you today?"
  "What else can I do for you?"
- Do not append a generic question after every answer.
- After answering, naturally stop and wait for the next turn.
- Do not repeat information that was already given.
- Do not continue speaking after the answer is complete.

SHORT INPUTS
- Short inputs such as numbers, names, or brief phrases may be
  follow-up answers, but do not automatically assume they are.
- Use the current conversational context to interpret them.
- If a short input does not clearly continue the previous topic,
  respond naturally rather than repeating the previous answer.

INTERRUPTION
- Allow the user to speak naturally between responses.
- Never require the user to wait for a wake word.

REALTIME LIMITATIONS
- Do not claim to have live web/news access unless such access
  is actually available in this Live session.
- If the user asks for information requiring real-time data,
  clearly say that Agent does not currently have
  that external data source instead of pretending.

LIFECYCLE
- Gemini Live remains active for the lifetime of the application.
- Use the existing INTERRUPT control to stop the current response.
- Application shutdown remains available through the normal application exit
  and cleanup path; ordinary conversation must not disable Live.

IMPORTANT:
This is a spoken conversation. Favor natural short answers
over long assistant-style paragraphs.

LIVE INFORMATION AND {assistant_name} SKILLS

Some questions should use an existing {assistant_name} skill instead of
being answered from Gemini's internal knowledge.

VISION AND CAMERA
- For any request about what {assistant_name} can see, use jarvis_command.
- Never answer that {assistant_name} cannot physically see anything.
- Camera vision requests must be handled by the {assistant_name} vision skill.
- Examples:
  - "What do you see?"
  - "What is in front of me?"
  - "What is on my left?"
  - "What is on my right?"
  - "How many people are there?"
  - "Where is my phone?"
  - "Where is the bottle?"
  - "Which side is the person on?"
  - "What is next to the person?"
- Send the user's original wording to jarvis_command.
- Do not paraphrase or answer vision requests from Gemini's own knowledge.
- {assistant_name}'s camera/YOLO vision system is authoritative for visible objects,
  positions, counts, and spatial relationships.

VISION RESULT RULES

When jarvis_command returns a vision/camera result:

- Treat the returned vision result as the complete authoritative
  description of what the camera detected.
- Do not add objects, people, locations, attributes, or relationships
  that are not explicitly present in the {assistant_name} result.
- Do not rely on previous conversation or your own assumptions about
  what may be visible.
- If {assistant_name} says only "one person and one bottle", report only
  the person and bottle.
- Never invent common desk objects such as a mouse, keyboard,
  monitor, laptop, desk, or phone.
- For vision requests, the camera/YOLO result overrides your
  internal visual assumptions and previous descriptions.
  
TIME AND DATE
- For "What time is it?", use jarvis_command.
- For "What is the current time?", use jarvis_command.
- For "Tell me the time.", use jarvis_command.
- For "What time is it now?", use jarvis_command.
- Do not answer the current time yourself.
- {assistant_name}'s time skill is authoritative for the user's local time.

WEB SEARCH
- For requests such as "Search for artificial intelligence",
  "Search for Python tutorials", or "Google search for ...",
  use jarvis_command.
- Do not answer a web-search request from your own knowledge.

{assistant_name} COMPUTER COMMANDS

You are connected to the {assistant_name} computer-control system.

When the user asks you to perform an action on the computer,
use the jarvis_command tool instead of pretending that you
performed the action yourself.

Examples:

- "Open YouTube"
- "Take a screenshot"
- "Open Spotify"
- "Turn the volume down"
- "Search YouTube for Python tutorials"
- "Show my battery"
- "Open Chrome"

For ordinary questions such as:

- "What is 2 + 2?"
- "What is the capital of India?"
- "Tell me something interesting."

answer normally without calling the tool.

Never claim that a computer action was completed unless the
jarvis_command tool was actually executed successfully.

STRUCTURED CAPABILITIES
- Prefer jarvis_capability when the user's intent clearly maps to one
  registered capability shown in that tool's catalog.
- Pass the capability name in `action` and validated inputs in `parameters`.
  Do not invent action names or parameters.
- Treat failed, unsupported, and no-result responses as non-success. Explain
  the limitation or ask for missing information instead of guessing.
- Use jarvis_command when the request depends on JARVIS's natural-language
  dispatcher, contextual reference resolver, or an action not in the catalog.
- For "open the first/second result" use jarvis_open_result with the numbered
  position from the latest jarvis_search response. If the result context is
  stale or ambiguous, ask the user briefly rather than guessing.
- A page-opened result does not imply that page content was read. Only give a
  detailed page summary when jarvis_read_page explicitly returns extracted content.
- After a tool result, decide from that real result whether another dependent
  capability is needed. Do not execute a fixed sequence blindly.
- Ordinary conversation and static questions do not need a tool call.

FILE INTELLIGENCE
- The supported JARVIS dashboard upload flow ingests the uploaded file into
  File Intelligence and reports its processing status. Do not claim that a
  raw upload path alone is indexed.
- `file_list` reports registered File Intelligence records, not an arbitrary
  project-folder or filesystem directory listing.
- Use `file_search` only against indexed File Intelligence records. Treat its
  `no_results` status as an empty search, and treat ingestion or handler
  failures as failures.
- When explaining upload/indexing, tell the user to use the supported JARVIS
  File Intelligence upload control, wait for processing to be ready, then use
  `file_list` or `file_search`. Do not invent an unsupported directory path or
  indexing command.

After a command is executed, briefly tell the user the result
naturally.

REFERENCE PRESERVATION
- When a user refers to a previous search result or object using
  words such as "first one", "second one", "third one", "that one",
  "the previous one", or "this one", preserve that reference in
  the jarvis_command exactly as the user expressed it.
- Do not replace a positional reference with a description of the
  object.
- Example:
  User: "Open first one"
  Correct jarvis_command: "Open first one"
  Incorrect: "Open first Python tutorial result"
- {assistant_name} has its own reference-resolution system. Let {assistant_name}
  resolve which object the reference means.

"""

    return (
        prompt
        + "\n\n"
        + live_rules
    )


# * =============================================================
# * JARVIS COMMAND TOOL
# * =============================================================

def _build_jarvis_command_tool() -> dict:
    assistant_name = get_assistant_display_name()

    return {
        "function_declarations": [
            {
                "name": "jarvis_command",
                "description": (
                    f"Execute a command using the existing {assistant_name} "
                    "command system. Use this when the user asks "
                    f"{assistant_name} to perform an action on the computer, "
                    f"use an installed {assistant_name} skill, retrieve current "
                    f"information through a {assistant_name} skill, or perform "
                    "a web search. Do not use it for ordinary static "
                    f"questions or casual conversation when no {assistant_name} "
                    "skill is required."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": (
                                f"The exact command to pass to {assistant_name}. "
                                "Preserve the user's command wording whenever possible. "
                                "Do NOT paraphrase, expand, reinterpret, or replace "
                                "references such as 'first one', 'second one', "
                                "'that result', 'the previous one', or 'this one'. "
                                "For positional or contextual references, preserve the "
                                f"reference exactly as the user said it so {assistant_name}'s own "
                                "reference resolver can resolve it. "
                                "Example: if the user says 'Open first one', send "
                                "'Open first one', NOT 'Open first Python tutorial result'."
                            ),
                        },
                    },
                    "required": [
                        "command"
                    ],
                },
            }
        ]
    }


# * Keep the historical export for callers that import this tool definition.
# * Live sessions build a fresh definition so a runtime rename is reflected.
JARVIS_COMMAND_TOOL = _build_jarvis_command_tool()


# * =============================================================
# * AGENT CLASS
# * =============================================================

class Agent:

    def __init__(self):

        self._thread: Optional[
            threading.Thread
        ] = None

        self._stop_event = threading.Event()

        self._state_lock = threading.Lock()

        self._running = False
        self._connected = False
        self._hud_speaking = False
        
        # * -----------------------------------------------------
        # * Live microphone state.
        #
        # * This is separate from the normal JARVIS listener.
        # * Turning the HUD microphone OFF while Live is running
        # ! must silence Live input without closing the session.
        # * -----------------------------------------------------

        self._microphone_enabled = True

        self._microphone_lock = threading.Lock()

        # * -----------------------------------------------------
        # * Prevent duplicate pause/resume operations.
        #
        # * This is intentionally owned by Agent so
        # * repeated calls cannot pause/resume the normal listener
        # * multiple times.
        # * -----------------------------------------------------

        self._normal_mic_paused = False

        self._normal_mic_lock = threading.Lock()

        # * -----------------------------------------------------
        # * Gemini Live session resumption.
        #
        # * Gemini provides a resumable handle before a Live
        # * connection reaches its server-side lifetime limit.
        # * The handle is used to continue the same conversation
        # * on the next Gemini connection.
        # * -----------------------------------------------------

        self._session_resumption_handle = None

        self._session_resumption_lock = threading.Lock()

        # The greeting is generated by Gemini Live after the first confirmed
        # connection, so it uses the Live speaker and cannot compete with the
        # legacy TTS path.  Keep it once per Agent lifecycle, including Live
        # connection rollovers.
        self._startup_greeting_sent = False
        self._startup_greeting_lock = threading.Lock()

        # * -----------------------------------------------------
        # * Typed Command Input -> Gemini Live bridge.
        #
        # * These point only to the currently active Gemini
        # ! connection. They are replaced automatically whenever
        # * Live performs a connection rollover.
        # * -----------------------------------------------------

        self._session = None
        self._session_loop = None
        self._session_lock = threading.Lock()

    # * =========================================================
    # * STATE
    # * =========================================================

    @property
    def running(self) -> bool:

        with self._state_lock:

            return self._running

    def _set_running(
        self,
        value: bool,
    ):

        with self._state_lock:

            self._running = value

    @property
    def connected(self) -> bool:
        with self._state_lock:
            return self._connected

    def _set_connected(self, value: bool):
        with self._state_lock:
            self._connected = bool(value)
            
    
    # * =========================================================
    # * LIVE MICROPHONE STATE
    # * =========================================================

    def set_microphone_enabled(
        self,
        enabled: bool,
    ):

        with self._microphone_lock:

            self._microphone_enabled = bool(
                enabled
            )

        print(
            "[LIVE] Microphone:",
            "ON" if enabled else "OFF",
        )

    # * ---------------------------------------------------------

    def microphone_enabled(self) -> bool:

        with self._microphone_lock:

            return self._microphone_enabled

    async def _send_startup_brief(self, session) -> bool:
        """Deliver the configured existing startup brief through Live once."""
        with self._startup_greeting_lock:
            if self._startup_greeting_sent:
                return False
            self._startup_greeting_sent = True

        try:
            from core.assistant import is_morning_brief_enabled
            from core.startup_brief import speak_startup_brief, start_weather_fetch
            from core.morning_brief import start_news_fetch

            weather_future = start_weather_fetch()
            news_future = start_news_fetch() if is_morning_brief_enabled() else None
            brief = await asyncio.to_thread(
                speak_startup_brief,
                lambda _text: None,
                profile={},
                news_enabled=is_morning_brief_enabled(),
                news_future=news_future,
                weather_future=weather_future,
                return_text=True,
            )
            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part.from_text(
                        text=(
                            "Begin this session by speaking this exact configured "
                            f"startup briefing to the user: {brief}"
                        )
                    )],
                ),
                turn_complete=True,
            )
            print("[LIVE] Startup briefing requested through Gemini Live.")
            return True
        except Exception as exc:
            with self._startup_greeting_lock:
                self._startup_greeting_sent = False
            print("[LIVE] Startup greeting unavailable:", exc)
            return False
        
        
    # * =========================================================
    # * HUD SPEAKING STATE
    # * =========================================================

    def _hud_start_speaking(self):
        if self._hud_speaking:
            return

        try:
            HUDIntegration.speaking()
            self._hud_speaking = True

            print(
                "[LIVE HUD] SPEAKING ON"
            )

        except Exception as exc:
            print(
                "[LIVE HUD] Speaking event failed:",
                exc,
            )

    # * ---------------------------------------------------------

    def _hud_stop_speaking(self):
        if not self._hud_speaking:
            return

        try:
            HUDIntegration.idle()

            print(
                "[LIVE HUD] SPEAKING OFF"
            )

        except Exception as exc:
            print(
                "[LIVE HUD] Idle event failed:",
                exc,
            )

        finally:
            self._hud_speaking = False
        
    # * =========================================================
    # * GEMINI SESSION RESUMPTION
    # * =========================================================

    def _get_session_resumption_handle(self):

        with self._session_resumption_lock:

            return self._session_resumption_handle

    # * ---------------------------------------------------------

    def _set_session_resumption_handle(
        self,
        handle,
    ):

        if not handle:

            return

        with self._session_resumption_lock:

            self._session_resumption_handle = handle
            
            
    # * =========================================================
    # * TYPED TEXT -> GEMINI LIVE
    # * =========================================================

    def send_text(
        self,
        text: str,
    ) -> bool:
        """
        Send typed Command Input into the currently active
        Gemini Live session.

        This method may be called from a normal JARVIS/dashboard
        worker thread, so the Gemini Live asyncio session is
        accessed through its owning event loop.
        """

        text = str(text or "").strip()

        if not text:
            return False

        with self._session_lock:
            session = self._session
            loop = self._session_loop

        if (
            session is None
            or loop is None
            or loop.is_closed()
        ):
            
            return False

        async def _send():
            await session.send_realtime_input(
                text=text,
            )

        try:

            future = asyncio.run_coroutine_threadsafe(
                _send(),
                loop,
            )

            future.result(
                timeout=5,
            )

            print(
                "[LIVE TEXT] Sent to Gemini Live:",
                text,
            )

            return True

        except Exception as exc:

            print(
                "[LIVE] Failed to send typed text:",
                exc,
            )

            return False

    # * =========================================================
    # * START
    # * =========================================================

    def start(self):

        if self.running:

            debug_print("[LIVE] Already running.")

            return

        if not _api_key():

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self._stop_event.clear()

        with self._startup_greeting_lock:
            self._startup_greeting_sent = False
        
        self.set_microphone_enabled(True)
        
        print("[AGENT] Starting...")

        self._thread = threading.Thread(
            target=self._thread_main,
            daemon=True,
            name="JARVIS-Agent",
        )

        self._thread.start()

    # * =========================================================
    # * STOP
    # * =========================================================

    def stop(self):

        if not self.running:

            debug_print("[LIVE] Already stopped.")

            return

        print("[AGENT] Stopping...")

        self._stop_event.set()

    # * =========================================================
    # * THREAD ENTRY
    # * =========================================================

    def _thread_main(self):

        self._set_running(True)

        try:

            asyncio.run(
                self._run()
            )

        except Exception as exc:

            print(
                f"[LIVE] Fatal error: {exc}"
            )

        finally:

            self._set_running(False)

            print("[AGENT] Stopped")

    # * =========================================================
    # * MAIN SESSION
    # * =========================================================

    async def _run(self):

        api_key = _api_key()

        if not api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )
            
        debug_print("[LIVE] AGENT STARTING")
        debug_print("[LIVE] Starting Gemini Live session...")
        debug_print(f"[LIVE] Model: {LIVE_MODEL}")

        # * -----------------------------------------------------
        # * Pause the normal JARVIS microphone exactly once.
        # * -----------------------------------------------------

        self._pause_normal_microphone()
        
        debug_print(
            f"[LIVE] Normal {get_assistant_display_name()} microphone paused."
        )

        input_queue: asyncio.Queue[
            bytes
        ] = asyncio.Queue(
            maxsize=INPUT_QUEUE_SIZE
        )

        loop = asyncio.get_running_loop()

        microphone = None
        speaker = None

        client = genai.Client(
            api_key=api_key
        )

        # * =====================================================
        # * GEMINI LIVE CONFIGURATION
        # * =====================================================

        config = types.LiveConnectConfig(

            response_modalities=[
                types.Modality.AUDIO
            ],

            input_audio_transcription=(
                types.AudioTranscriptionConfig()
            ),

            output_audio_transcription=(
                types.AudioTranscriptionConfig()
            ),

            system_instruction=types.Content(
                parts=[
                    types.Part(
                        text=_system_prompt()
                    )
                ]
            ),
            
            tools=[
                _build_jarvis_command_tool(),
                build_live_capability_tool(),
                *build_live_search_tools(),
            ],

            speech_config=types.SpeechConfig(

                voice_config=types.VoiceConfig(

                    prebuilt_voice_config=(
                        types.PrebuiltVoiceConfig(
                            voice_name="Charon"
                        )
                    )

                )

            ),

            # * -------------------------------------------------
            # * Allow Gemini to provide a resumable session
            # * handle when this connection approaches its
            # * server-side lifetime limit.
            # * -------------------------------------------------

            session_resumption=types.SessionResumptionConfig(
                handle=self._get_session_resumption_handle(),

            ),
        )

        # * =====================================================
        # * MICROPHONE CALLBACK
        # * =====================================================

        def microphone_callback(
            indata,
            frames,
            time_info,
            status,
        ):

            if self._stop_event.is_set():

                return

            # * -------------------------------------------------
            # * HUD microphone switch.
            #
            # * Live session remains connected while the
            # * microphone is OFF. Only audio input is muted.
            # * -------------------------------------------------

            if not self.microphone_enabled():

                return

            if status:

                print(
                    f"[LIVE] Microphone status: {status}"
                )

            try:

                audio_bytes = bytes(
                    indata
                )

                loop.call_soon_threadsafe(
                    self._queue_audio,
                    input_queue,
                    audio_bytes,
                )

            except Exception as exc:

                print(
                    "[LIVE] Microphone callback error:",
                    exc,
                )

        try:

            # * =================================================
            # * LIVE AUDIO DEVICES
            # * =================================================
            #
            # * These remain alive across Gemini connection
            # * rollovers.
            #
            # * The physical microphone and speaker belong to
            # * the Agent instance, not to a single
            # * Gemini connection.
            # * =================================================

            microphone = sd.RawInputStream(

                samplerate=INPUT_RATE,

                channels=CHANNELS,

                dtype=DTYPE,

                blocksize=BLOCK_SIZE,

                callback=microphone_callback,
            )

            speaker = sd.RawOutputStream(

                samplerate=OUTPUT_RATE,

                channels=CHANNELS,

                dtype=DTYPE,

                blocksize=BLOCK_SIZE,
            )

            microphone.start()

            speaker.start()

            print(
                "[LIVE] Microphone active."
            )

            print(
                "[LIVE] Speaker active."
            )

            # * =================================================
            # * STOP WATCHER
            # * =================================================

            stop_task = asyncio.create_task(
                self._wait_for_stop(),
                name="JARVIS-AgentStopWatcher",
            )

            try:

                # * =================================================
                # * PERSISTENT LIVE CONNECTION LOOP
                # * =================================================
                #
                # * Gemini connections have a server-side lifetime.
                #
                # * This loop allows JARVIS to replace an expired
                # * connection automatically.
                #
                # * The session-resumption handle captured from the
                # * previous connection is supplied to the next
                # * connection so Gemini can resume the conversation.
                #
                # * The user remains in ONE continuous JARVIS Live
                # * Conversation from their perspective.
                # * =================================================

                connection_number = 0

                while not self._stop_event.is_set():

                    connection_number += 1

                    print(
                        "[LIVE] Connecting Gemini Live "
                        f"connection #{connection_number}..."
                    )

                    # * ---------------------------------------------
                    # * Build configuration for THIS connection.
                    #
                    # ! Important:
                    # * The latest session-resumption handle is read
                    # * immediately before connecting.
                    # * ---------------------------------------------

                    connection_config = types.LiveConnectConfig(

                        response_modalities=[
                            types.Modality.AUDIO
                        ],

                        input_audio_transcription=(
                            types.AudioTranscriptionConfig()
                        ),

                        output_audio_transcription=(
                            types.AudioTranscriptionConfig()
                        ),

                        system_instruction=types.Content(
                            parts=[
                                types.Part(
                                    text=_system_prompt()
                                )
                            ]
                        ),

                        tools=[
                            _build_jarvis_command_tool(),
                            build_live_capability_tool(),
                            *build_live_search_tools(),
                        ],

                        speech_config=types.SpeechConfig(

                            voice_config=types.VoiceConfig(

                                prebuilt_voice_config=(
                                    types.PrebuiltVoiceConfig(
                                        voice_name="Charon"
                                    )
                                )

                            )

                        ),

                        session_resumption=(
                            types.SessionResumptionConfig(
                                handle=(
                                    self._get_session_resumption_handle()
                                ),
                            )
                        ),
                    )

                    connection_should_retry = False

                    try:

                        async with client.aio.live.connect(
                            model=LIVE_MODEL,
                            config=connection_config,
                        ) as session:

                            print("[AGENT] Connected")

                            with self._session_lock:
                                self._session = session
                                self._session_loop = loop
                            self._set_connected(True)

                            if connection_number == 1:

                                print(
                                    "[LIVE] Persistent Live session active."
                                )

                            else:

                                print(
                                    "[LIVE] Gemini Live connection "
                                    "resumed automatically."
                                )

                            print("[AGENT] Listening...")

                            # * =========================================
                            # * AUDIO SENDER
                            # * =========================================

                            sender_task = asyncio.create_task(
                                self._send_audio(
                                    session,
                                    input_queue,
                                ),
                                name="JARVIS-LiveAudioSender",
                            )

                            try:

                                # * =====================================
                                # * RECEIVE / STOP LOOP
                                # * =====================================

                                startup_brief_started = False
                                while not self._stop_event.is_set():

                                    receive_task = asyncio.create_task(
                                        self._receive_one_turn(
                                            session,
                                            speaker,
                                        ),
                                        name="JARVIS-LiveReceiveTurn",
                                    )

                                    # Start the configured briefing only after
                                    # the receiver is already consuming Live
                                    # events. Sending it before this task exists
                                    # can starve protocol keepalive handling.
                                    if connection_number == 1 and not startup_brief_started:
                                        startup_brief_started = True
                                        await self._send_startup_brief(session)

                                    done, pending = await asyncio.wait(
                                        {
                                            receive_task,
                                            stop_task,
                                            sender_task,
                                        },
                                        return_when=asyncio.FIRST_COMPLETED,
                                    )

                                    # * ---------------------------------
                                    # * USER STOPPED LIVE
                                    # * ---------------------------------

                                    if stop_task in done:

                                        self._stop_event.set()

                                        if not receive_task.done():

                                            receive_task.cancel()

                                        await asyncio.gather(
                                            receive_task,
                                            return_exceptions=True,
                                        )

                                        break

                                    if sender_task in done:
                                        try:
                                            sender_error = sender_task.exception()
                                        except asyncio.CancelledError:
                                            sender_error = None
                                        if not self._stop_event.is_set():
                                            print(
                                                "[LIVE] Audio sender ended; "
                                                "reconnecting the Live session:",
                                                sender_error,
                                            )
                                            connection_should_retry = True
                                        if not receive_task.done():
                                            receive_task.cancel()
                                        await asyncio.gather(
                                            receive_task,
                                            return_exceptions=True,
                                        )
                                        break

                                    # * ---------------------------------
                                    # * GEMINI RECEIVE COMPLETED
                                    # * ---------------------------------

                                    if receive_task in done:

                                        try:

                                            result = (
                                                receive_task.result()
                                            )

                                            if result in (
                                                "stop_requested",
                                                "stopped",
                                            ):

                                                self._stop_event.set()

                                                break

                                            if result == "turn_complete":

                                                continue
                                            
                                            # * ---------------------------------
                                            # * GEMINI GO-AWAY
                                            # * ---------------------------------
                                            #
                                            # * Gemini has warned that this
                                            # * connection is reaching its
                                            # * server-side lifetime limit.
                                            #
                                            # ! The current connection must be
                                            # * allowed to close cleanly.
                                            #
                                            # * The outer connection loop will
                                            # * then reconnect using the latest
                                            # * session-resumption handle.
                                            # * ---------------------------------

                                            if result == "go_away":

                                                print(
                                                    "[LIVE] GoAway handled. "
                                                    "Closing current Gemini "
                                                    "connection cleanly."
                                                )

                                                connection_should_retry = True

                                                break

                                            # * ---------------------------------
                                            # * Gemini ended receive normally.
                                            #
                                            # * Treat this as a connection event,
                                            # * not as a user stop.
                                            # * ---------------------------------

                                            if result == "session_closed":

                                                print(
                                                    "[LIVE] Gemini Live "
                                                    "session closed."
                                                )

                                                connection_should_retry = True

                                                break

                                        except asyncio.CancelledError:

                                            break

                                        except Exception as exc:

                                            print(
                                                "[LIVE] Gemini connection "
                                                "ended unexpectedly:",
                                                exc,
                                            )

                                            connection_should_retry = True

                                            break

                            finally:

                                with self._session_lock:
                                    if self._session is session:
                                        self._session = None
                                        self._session_loop = None
                                self._set_connected(False)

                                sender_task.cancel()

                                await asyncio.gather(
                                    sender_task,
                                    return_exceptions=True,
                                )

                    except asyncio.CancelledError:

                        raise

                    except Exception as exc:

                        if self._stop_event.is_set():

                            break

                        print(
                            "[LIVE] Gemini Live connection error:",
                            exc,
                        )

                        connection_should_retry = True

                    # * ---------------------------------------------
                    # ! DO NOT reconnect after an explicit stop.
                    # * ---------------------------------------------

                    if self._stop_event.is_set():

                        break

                    # * ---------------------------------------------
                    # * Gemini connection ended.
                    #
                    # * We have a resumption handle from the server,
                    # * so reconnect automatically.
                    # * ---------------------------------------------

                    if connection_should_retry:

                        print(
                            "[LIVE] Preparing automatic Live "
                            "connection rollover..."
                        )

                        await asyncio.sleep(1.0)

                        print(
                            "[LIVE] Resuming Agent..."
                        )

                        continue

                    # * ---------------------------------------------
                    # * Defensive fallback.
                    #
                    # * If the connection somehow exits without an
                    # * explicit stop or retry request, keep Live
                    # * Conversation alive rather than silently ending.
                    # * ---------------------------------------------

                    print(
                        "[LIVE] Gemini Live connection ended."
                    )

                    await asyncio.sleep(1.0)

            finally:

                stop_task.cancel()

                await asyncio.gather(
                    stop_task,
                    return_exceptions=True,
                )

        finally:

            with self._session_lock:
                self._session = None
                self._session_loop = None
            self._set_connected(False)
            
            # * =================================================
            # * HUD SPEAKING CLEANUP
            # * =================================================

            self._hud_stop_speaking()

            # * =================================================
            # * CLOSE MICROPHONE
            # * =================================================

            if microphone is not None:

                try:

                    microphone.stop()

                except Exception:
                    pass

                try:

                    microphone.close()

                except Exception:
                    pass

            # * =================================================
            # * CLOSE SPEAKER
            # * =================================================

            if speaker is not None:

                try:

                    speaker.stop()

                except Exception:
                    pass

                try:

                    speaker.close()

                except Exception:
                    pass

            print(
                "[LIVE] Audio devices closed."
            )

            # * =================================================
            # * RESUME NORMAL JARVIS MICROPHONE
            # * =================================================

            self._resume_normal_microphone()

            print(
                f"[LIVE] Normal {get_assistant_display_name()} microphone resumed."
            )

    # * =========================================================
    # * QUEUE AUDIO
    # * =========================================================

    @staticmethod
    def _queue_audio(
        queue: asyncio.Queue,
        audio: bytes,
    ):

        try:

            queue.put_nowait(
                audio
            )

        except asyncio.QueueFull:

            # * Drop oldest audio chunk to keep latency bounded.

            try:

                queue.get_nowait()

            except asyncio.QueueEmpty:
                pass

            try:

                queue.put_nowait(
                    audio
                )

            except asyncio.QueueFull:
                pass
            
    # * =========================================================
    # * INTERRUPT LIVE SPEAKER
    # * =========================================================

    @staticmethod
    def _interrupt_speaker(
        speaker,
    ):
        """
        Immediately interrupt Live audio playback.

        IMPORTANT:
        abort() clears the current PortAudio playback,
        but it also leaves the stream stopped.

        Therefore the same stream is immediately restarted
        so the next Gemini response can continue using it.

        This affects ONLY the Agent speaker.
        """

        if speaker is None:

            return

        try:

            # * Immediately discard currently buffered audio.
            speaker.abort()

            # * Re-open the same active stream for the
            # * next Gemini response.
            speaker.start()

            print(
                "[LIVE] Speaker output interrupted."
            )

            print(
                "[LIVE] Speaker stream restarted."
            )

        except Exception as exc:

            print(
                "[LIVE] Speaker interruption failed:",
                exc,
            )

    # * =========================================================
    # * SEND AUDIO
    # * =========================================================

    async def _send_audio(
        self,
        session,
        input_queue: asyncio.Queue,
    ):

        try:

            while not self._stop_event.is_set():

                try:

                    audio = await asyncio.wait_for(
                        input_queue.get(),
                        timeout=0.25,
                    )

                except asyncio.TimeoutError:

                    continue

                # * ------------------------------------------------
                # ! DO NOT send audio_stream_end after each phrase.
                #
                # * Gemini's automatic VAD handles speech turns.
                # * ------------------------------------------------

                await session.send_realtime_input(

                    audio=types.Blob(
                        data=audio,
                        mime_type=(
                            "audio/pcm;rate=16000"
                        ),
                    )

                )

        except asyncio.CancelledError:

            raise

        except Exception as exc:

            print(
                "[LIVE] Audio sender stopped:",
                exc,
            )

            raise

    # * =========================================================
    # * RECEIVE ONE GEMINI TURN
    # * =========================================================

    async def _receive_one_turn(
        self,
        session,
        speaker,
    ):
        """
        Receive exactly ONE Gemini model turn.

        IMPORTANT:

        Returning from this function does NOT terminate
        Agent.

        The SAME Gemini session remains alive.

        The caller invokes this method again.
        """
        
        output_text_parts = []

        # * True when an existing JARVIS skill already produced the
        # * authoritative response for this Live turn.
        # * In that case the normal voice/HUD path has already logged
        # ! the response, so Live must not log it a second time.
        
        jarvis_authoritative_response = False

        try:
            
            print(
                "[LIVE TURN] Waiting for user..."
            )

            async for response in session.receive():
                
                # * =============================================
                # * SERVER GO-AWAY NOTICE
                # * =============================================
                #
                # * Gemini is telling us that this Live
                # * connection is approaching closure.
                #
                # ! Do not reconnect here.
                # ! Do not create another Live session.
                # * Just report the server notice and allow
                # * the current receive operation to finish.
                # * =============================================

                if response.go_away:

                    time_left = (
                        response.go_away.time_left
                        or "unknown"
                    )

                    print(
                        "[LIVE] Gemini Live connection "
                        f"will close soon. Time left: {time_left}"
                    )

                    # * ---------------------------------------------
                    # ! IMPORTANT:
                    #
                    # * Gemini has explicitly told us that this
                    # * connection is going to close.
                    #
                    # ! Do NOT wait for Gemini to forcibly terminate
                    # * the connection with 1008.
                    #
                    # * Return immediately so _run() can cleanly
                    # * exit this connection and create the next
                    # * Gemini connection using the latest
                    # * session-resumption handle.
                    # * ---------------------------------------------

                    print(
                        "[LIVE] GoAway received. "
                        "Preparing automatic connection rollover."
                    )

                    return "go_away"

                # * =============================================
                # * SESSION RESUMPTION UPDATE
                # * =============================================

                if response.session_resumption_update:

                    update = (
                        response.session_resumption_update
                    )

                    if (
                        update.resumable
                        and update.new_handle
                    ):

                        self._set_session_resumption_handle(
                            update.new_handle
                        )
                
                # * =============================================
                # * TOOL CALL CANCELLATION
                # * =============================================
                #
                # * Gemini may cancel a previously issued tool
                # * call, for example when the user interrupts
                # * the response or changes direction.
                #
                # * This is NOT a Live session failure.
                #
                # ! Do not stop the entire conversation.
                # ! Do not reconnect.
                # * =============================================

                if response.tool_call_cancellation:

                    cancelled_ids = (
                        response.tool_call_cancellation.ids
                        or []
                    )

                    print(
                        "[LIVE TOOL] Tool call cancelled:",
                        cancelled_ids,
                    )

                    # * Continue receiving from the SAME
                    # * persistent Gemini Live session.
                    continue

                if response.tool_call:

                    function_responses = []

                    for function_call in (
                        response.tool_call.function_calls
                    ):

                        function_name = (
                            function_call.name
                        )

                        print(
                            "[LIVE TOOL]",
                            function_name,
                        )

                        # * -----------------------------------------
                        # * JARVIS COMMAND
                        # * -----------------------------------------

                        if function_name == "jarvis_command":

                            args = (
                                function_call.args
                                or {}
                            )

                            command = str(
                                args.get(
                                    "command",
                                    "",
                                )
                            ).strip()

                            print(
                                "[LIVE TOOL COMMAND]",
                                command,
                            )

                            if not command:

                                result = {
                                    "success": False,
                                    "message": (
                                        f"No {get_assistant_display_name()} command was provided."
                                    ),
                                }

                            else:

                                try:

                                    # * ---------------------------------
                                    # * Existing JARVIS dispatcher
                                    # * remains authoritative.
                                    # * ---------------------------------

                                    with live_execution(session=session, loop=asyncio.get_running_loop()):

                                        dispatch_result = dispatch(
                                            command
                                        )

                                        await drain_live_tasks()

                                        live_responses = get_live_responses()


                                    # * -------------------------------------------------
                                    # * Prefer the actual response produced by the
                                    # * existing JARVIS skill.
                                    #
                                    # * Example:
                                    #
                                    # * time_skill
                                    # * ↓
                                    # * speak("The time is 01:49 AM")
                                    # * ↓
                                    # * captured here
                                    #
                                    # ! Gemini must receive that authoritative result
                                    # * instead of generating its own answer.
                                    # * -------------------------------------------------

                                    authoritative_response = " ".join(
                                        response.strip()
                                        for response in live_responses
                                        if response and response.strip()
                                    )

                                    if authoritative_response:

                                        print(
                                            f"[LIVE] {get_assistant_display_name()} skill response:",
                                            authoritative_response,
                                        )
                                        
                                        jarvis_authoritative_response = True

                                        result = {
                                            "success": True,
                                            "message": (
                                                f"{get_assistant_display_name()} result: {authoritative_response}. "
                                                "Use this result as the authoritative answer to the user's request. "
                                                "Do not generate a different value."
                                            ),
                                            "authoritative": True,
                                        }

                                    elif isinstance(
                                        dispatch_result,
                                        bool,
                                    ):

                                        result = {
                                            "success": dispatch_result,
                                            "message": (
                                                "I completed that request."
                                                if dispatch_result
                                                else "I couldn't complete that request."
                                            ),
                                        }

                                    elif isinstance(dispatch_result, dict):

                                        result = dispatch_result

                                    elif dispatch_result is None:

                                        result = {
                                            "success": False,
                                            "status": "no_result",
                                            "message": (
                                                "The command was dispatched, but it returned no result, "
                                                "so completion could not be verified."
                                            ),
                                        }

                                    else:

                                        result = {
                                            "success": True,
                                            "message": str(
                                                dispatch_result
                                            ),
                                        }

                                except Exception as exc:

                                    print(
                                        "[LIVE TOOL ERROR]",
                                        exc,
                                    )

                                    result = {
                                        "success": False,
                                        "message": str(
                                            exc
                                        ),
                                    }

                        elif function_name == "jarvis_search":

                            args = function_call.args or {}
                            with live_execution(session=session, loop=asyncio.get_running_loop()):
                                result = execute_live_search(
                                    args.get("query"),
                                    args.get("provider", "google"),
                                )
                            if result.get("authoritative"):
                                jarvis_authoritative_response = True

                        elif function_name == "jarvis_open_result":

                            args = function_call.args or {}
                            with live_execution(session=session, loop=asyncio.get_running_loop()):
                                result = execute_live_open_result(
                                    args.get("position"),
                                    args.get("url"),
                                )
                            if result.get("authoritative"):
                                jarvis_authoritative_response = True

                        elif function_name == "jarvis_read_page":

                            args = function_call.args or {}
                            with live_execution(session=session, loop=asyncio.get_running_loop()):
                                result = execute_live_read_page(args)
                            if result.get("authoritative"):
                                jarvis_authoritative_response = True

                        elif structured_action_from_tool_name(function_name):

                            args = function_call.args or {}
                            action = structured_action_from_tool_name(function_name)

                            try:
                                with live_execution(session=session, loop=asyncio.get_running_loop()):
                                    result = execute_live_capability(
                                        action,
                                        args,
                                    )
                                    await drain_live_tasks()
                                    live_responses = get_live_responses()
                                    if live_responses and not result.get("authoritative"):
                                        result = {
                                            "ok": True,
                                            "status": "reported_success",
                                            "action": action,
                                            "authoritative": True,
                                            "message": " ".join(live_responses),
                                        }
                                if result.get("authoritative"):
                                    jarvis_authoritative_response = True
                            except Exception as exc:
                                debug_print(
                                    "[LIVE CAPABILITY ERROR]",
                                    type(exc).__name__,
                                )
                                result = {
                                    "ok": False,
                                    "status": "failed",
                                    "action": action,
                                    "message": str(exc),
                                }

                        elif function_name == "jarvis_capability":

                            args = function_call.args or {}
                            action = args.get("action", "")
                            parameters = args.get("parameters", {})

                            try:
                                # Keep the existing live execution context so
                                # skill-generated speech remains authoritative.
                                with live_execution(session=session, loop=asyncio.get_running_loop()):
                                    result = execute_live_capability(
                                        action,
                                        parameters,
                                    )
                                    await drain_live_tasks()
                                    live_responses = get_live_responses()
                                    if live_responses and not result.get("authoritative"):
                                        result = {
                                            "ok": True,
                                            "status": "reported_success",
                                            "action": action,
                                            "authoritative": True,
                                            "message": " ".join(live_responses),
                                        }
                                if result.get("authoritative"):
                                    jarvis_authoritative_response = True
                            except Exception as exc:
                                debug_print(
                                    "[LIVE CAPABILITY ERROR]",
                                    type(exc).__name__,
                                )
                                result = {
                                    "ok": False,
                                    "status": "failed",
                                    "message": str(exc),
                                }

                        else:

                            result = {
                                "success": False,
                                "message": (
                                    f"Unknown {get_assistant_display_name()} tool: "
                                    f"{function_name}"
                                ),
                            }

                        function_responses.append(
                            types.FunctionResponse(
                                id=function_call.id,
                                name=function_name,
                                response=result,
                            )
                        )

                        # Keep runtime diagnostics useful without logging page
                        # content, URLs with sensitive parameters, or secrets.
                        if function_name == "jarvis_read_page" and isinstance(result, dict):
                            print(
                                "[LIVE PAGE READ RESULT]",
                                "status=", result.get("status"),
                                "extraction_status=", result.get("extraction_status"),
                                "ok=", result.get("ok"),
                                "content_length=", result.get("content_length", 0),
                                "truncated=", result.get("truncated", False),
                            )

                    # * ---------------------------------------------
                    # * Send result back to Gemini.
                    # * ---------------------------------------------

                    await session.send_tool_response(
                        function_responses=function_responses
                    )

                    continue

                if self._stop_event.is_set():

                    return "stopped"

                # * =============================================
                # * AUDIO OUTPUT
                # * =============================================

                if response.data:

                    # * Gemini has produced actual speaker audio.
                    # * Tell the HUD that JARVIS is now speaking.
                    self._hud_start_speaking()

                    await asyncio.to_thread(
                        speaker.write,
                        response.data,
                    )

                # * =============================================
                # * SERVER CONTENT
                # * =============================================

                server_content = (
                    response.server_content
                )

                if not server_content:

                    continue

                # * =============================================
                # * USER TRANSCRIPTION
                # * =============================================

                input_transcription = (
                    server_content.input_transcription
                )

                if (
                    input_transcription
                    and input_transcription.text
                ):

                    user_text = (
                        input_transcription.text.strip()
                    )

                    if user_text:

                        print(
                            "[YOU]",
                            user_text,
                        )

                        try:
                            HUDIntegration.command(
                                user_text
                            )
                        except Exception as exc:
                            print(
                                "[HUD LIVE COMMAND LOG] Failed:",
                                exc,
                            )

                # * =============================================
                # * JARVIS TRANSCRIPTION
                # * =============================================

                output_transcription = (
                    server_content.output_transcription
                )

                if (
                    output_transcription
                    and output_transcription.text
                ):

                    output_text = (
                        output_transcription.text.strip()
                    )

                    if output_text:

                        output_text_parts.append(
                            output_text
                        )

                # * =============================================
                # * MODEL RESPONSE INTERRUPTED
                # * =============================================
                #
                # * The user may begin speaking while Gemini is
                # * producing audio.
                #
                # * This is a normal Agent event.
                #
                # ! IMPORTANT:
                # ! Do NOT close the Gemini session.
                # ! Do NOT reconnect.
                # ! Do NOT set the global stop event.
                # * The same session continues with the user's
                # * new turn.
                # * =============================================

                if getattr(
                    server_content,
                    "interrupted",
                    False,
                ):

                    print(
                        "[LIVE] --------------------------------------------------"
                    )
                    print(
                        "[LIVE] USER INTERRUPTED MODEL RESPONSE"
                    )
                    print(
                        "[LIVE] --------------------------------------------------"
                    )
                    
                    self._hud_stop_speaking()

                    self._interrupt_speaker(
                        speaker
                    )

                    print(
                        "[LIVE] Continuing same Gemini Live session."
                    )

                    return "turn_complete"


                # * =============================================
                # * TURN COMPLETE
                # * =============================================

                if getattr(
                    server_content,
                    "turn_complete",
                    False,
                ):

                    if output_text_parts:

                        complete_output = " ".join(
                            output_text_parts
                        ).strip()

                        if complete_output:

                            print(
                                f"[{get_assistant_display_name()}]",
                                complete_output,
                            )

                            if not jarvis_authoritative_response:

                                try:
                                    HUDIntegration.response(
                                        complete_output,
                                        speaker="live",
                                    )
                                except Exception as exc:
                                    print(
                                        "[HUD LIVE RESPONSE LOG] Failed:",
                                        exc,
                                    )
                    self._hud_stop_speaking()

                    print(
                        "[LIVE] Turn complete."
                    )

                    # * -----------------------------------------
                    # * Only this receive operation ends.
                    #
                    # * Gemini session remains alive.
                    #
                    # * _run() calls receive() again.
                    # * -----------------------------------------

                    return "turn_complete"

            return "session_closed"

        except asyncio.CancelledError:

            raise

        except Exception as exc:

            print(
                "[LIVE] Gemini receive error:",
                exc,
            )

            # * ---------------------------------------------
            # ! A Gemini connection error is NOT the same as
            # * the user requesting Live to stop.
            #
            # * _run() will detect the failed connection and
            # * automatically reconnect using the latest
            # * session-resumption handle.
            # * ---------------------------------------------

            raise

    # * =========================================================
    # * STOP WATCHER
    # * =========================================================

    async def _wait_for_stop(self):

        while not self._stop_event.is_set():

            await asyncio.sleep(
                0.1
            )

        return "stop requested"

    # * =========================================================
    # * NORMAL JARVIS MICROPHONE
    # * =========================================================

    def _pause_normal_microphone(self):
        """
        Pause the normal JARVIS listener exactly once.

        This prevents duplicate calls if the Live action is
        triggered while another part of JARVIS has already
        initiated the pause.
        """

        with self._normal_mic_lock:

            if self._normal_mic_paused:

                print(
                    "[MIC] Background listener already paused"
                )

                return

            try:

                from core.listener import (
                    pause_listener,
                )

                pause_listener()

                self._normal_mic_paused = True

            except ImportError:

                print(
                    "[MIC] Background listener pause API unavailable."
                )

            except Exception as exc:

                print(
                    "[MIC] Could not pause listener:",
                    exc,
                )

    def _resume_normal_microphone(self):
        """
        Resume the normal JARVIS listener exactly once.
        """

        with self._normal_mic_lock:

            if not self._normal_mic_paused:

                print(
                    "[MIC] Background listener already resumed"
                )

                return

            try:

                from core.listener import (
                    resume_listener,
                )

                resume_listener()

                self._normal_mic_paused = False

            except ImportError:

                print(
                    "[MIC] Background listener resume API unavailable."
                )

            except Exception as exc:

                print(
                    "[MIC] Could not resume listener:",
                    exc,
                )


# * =============================================================
# * GLOBAL LIVE INSTANCE
# * =============================================================

_agent = Agent()


# * =============================================================
# * LIVE TEXT BRIDGE
# * =============================================================

def send_agent_text(
    text: str,
) -> bool:
    """
    Send typed Command Input to the active Gemini Live session.
    """

    return _agent.send_text(text)


# * =============================================================
# * REGISTRY ACTIONS
# * =============================================================

def start_agent(
    _data=None,
):

    if _agent.running:

        return (
            "Agent is already running."
        )

    _agent.start()

    try:

        HUDIntegration.system_activity(
            "AGENT ON"
        )

    except Exception as exc:

        print(
            "[HUD AGENT LOG ERROR]",
            exc,
        )

    return (
        "Agent started."
    )


def stop_agent(
    _data=None,
):

    if not _agent.running:

        return (
            "Agent is already stopped."
        )

    _agent.stop()

    try:

        HUDIntegration.system_activity(
            "AGENT OFF"
        )

    except Exception as exc:

        print(
            "[HUD AGENT LOG ERROR]",
            exc,
        )

    return (
        "Stopping Agent."
    )


def agent_status(
    _data=None,
):

    if _agent.connected:

        return (
            "Agent is connected."
        )

    if _agent.running:

        return (
            "Agent is reconnecting."
        )

    return (
        "Agent is stopped."
    )
