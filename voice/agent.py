"""
=============================================================
JARVIS ULTRA — AGENT
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
import math
import threading
import time
from array import array
from pathlib import Path
from typing import Optional
from uuid import uuid4

import sounddevice as sd

from google import genai
from google.genai import types

from core.dispatcher import dispatch

from core.live_execution import (
    live_execution,
    get_live_responses,
    drain_live_tasks,
    resolve_live_task_results,
    build_live_function_response,
    preserve_live_media,
    send_live_tool_response,
    LiveInvocationDeduplicator,
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
from services.whatsapp_parser import parse_scheduled_whatsapp

from hud.integration import HUDIntegration
from config.environment import get_env
from config.settings import (
    get_assistant_display_name,
    get_gemini_live_gender_setting,
    set_gemini_live_gender_setting,
    GEMINI_LIVE_DEFAULT_VOICE,
    GEMINI_LIVE_FEMALE_VOICE,
    get_primary_gemini_live_model,
)


def _live_whatsapp_schedule_key(parameters):
    """Build a turn-local identity for one structured WhatsApp schedule."""
    if not isinstance(parameters, dict):
        return None
    required = ("contact", "message", "send_at")
    if any(not str(parameters.get(name, "")).strip() for name in required):
        return None
    return json.dumps(
        {name: str(parameters[name]).strip().casefold() for name in required},
        sort_keys=True,
    )
from core.diagnostics import debug_print
from voice.live_context import (
    merge_transcript_text,
    recent_live_messages,
    record_live_turn,
)


# * =============================================================
# * CONFIGURATION
# * =============================================================

# One fixed, centrally configured primary Live model.  Do not accept a runtime
# environment override or silently rotate to another model on failure.
LIVE_MODEL = get_primary_gemini_live_model()


def _is_expired_session_resumption_error(error) -> bool:
    """Identify errors that require abandoning, rather than reusing, a handle."""

    text = str(error or "").lower()
    return (
        "1008" in text
        and ("session not found" in text or "expired" in text)
    ) or "session not found or expired" in text


def _live_reconnect_delay(attempt: int) -> float:
    """Return a bounded delay for repeated Live connection failures."""

    return min(30.0, 2.0 ** max(0, min(int(attempt) - 1, 5)))

INPUT_RATE = 16000
OUTPUT_RATE = 24000

CHANNELS = 1
DTYPE = "int16"

# * 1024 samples at 16 kHz ~= 64 ms.
BLOCK_SIZE = 1024

INPUT_QUEUE_SIZE = 64
VAD_START_RMS = 700.0
VAD_END_RMS = 450.0
VAD_SILENCE_FRAMES = 3
SCREEN_VISION_TIMEOUT_SECONDS = 10.0
MAX_LIVE_SCREEN_IMAGE_BYTES = 8 * 1024 * 1024


class LiveVoiceActivityDetector:
    """Small hysteresis detector for the existing 16-bit mic stream."""

    def __init__(self):
        self.active = False
        self._silence_frames = 0

    def update(self, rms: float) -> bool | None:
        if self.active:
            if rms <= VAD_END_RMS:
                self._silence_frames += 1
                if self._silence_frames >= VAD_SILENCE_FRAMES:
                    self.active = False
                    self._silence_frames = 0
                    return False
            else:
                self._silence_frames = 0
            return None

        if rms >= VAD_START_RMS:
            self.active = True
            self._silence_frames = 0
            return True

        return None

    def reset(self) -> None:
        self.active = False
        self._silence_frames = 0


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
- "Take a photo" or "Take a photo with my camera" (use the physical camera capture capability; never use screenshot)
- "Show camera preview" (use the physical camera preview capability)
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

SOFTWARE DEVELOPMENT REQUESTS
For requests to create, inspect, edit, repair, or test code or a project,
use the jarvis_developer tool with the user's original wording. Do not answer
the request as ordinary conversation and do not claim that a file or project
was changed without the returned Developer result.

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
- After a successful create_schedule capability, do not call jarvis_command for
  the scheduled command; scheduling stores it for the due time and is complete.
- After a successful schedule_whatsapp_message capability, do not call
  jarvis_command for that scheduled WhatsApp message.
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


def _build_jarvis_developer_tool() -> dict:
    """Declare the existing Developer Mode Live entry point."""
    return {
        "function_declarations": [
            {
                "name": "jarvis_developer",
                "description": (
                    "Execute a software-development request through the existing "
                    "JARVIS Developer Mode. Use this for creating, inspecting, "
                    "editing, repairing, or testing code and projects. Pass the "
                    "user's original wording unchanged. Do not answer a developer "
                    "request conversationally and do not claim success without "
                    "the returned Developer result."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The user's original software-development request.",
                        },
                    },
                    "required": ["command"],
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
        self._speaker = None
        self._speaker_lock = threading.Lock()
        self._speaker_io_lock = threading.RLock()
        self._speaker_started = False
        self._live_generation = 0
        self._live_discard_audio = False
        self._live_turn_active = False
        self._live_interrupt_pending = False
        self._live_interrupt_lock = threading.Lock()
        self._responded_screen_invocations = set()
        self._live_invocations = LiveInvocationDeduplicator(max_entries=256)
        self._live_voice_lock = threading.Lock()
        self._live_voice_enabled = get_gemini_live_gender_setting()
        self._live_voice_applied = GEMINI_LIVE_DEFAULT_VOICE
        self._live_voice_error = ""
        self._live_voice_switching = False
        self._live_voice_change = threading.Event()
        self._live_context_session_id = None

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

    def live_voice_setting(self) -> dict[str, object]:
        with self._live_voice_lock:
            requested_voice = (
                GEMINI_LIVE_FEMALE_VOICE
                if self._live_voice_enabled
                else GEMINI_LIVE_DEFAULT_VOICE
            )
            return {
                "enabled": self._live_voice_enabled,
                "requested_voice": requested_voice,
                "applied_voice": self._live_voice_applied,
                "applied": self._live_voice_applied == requested_voice,
                "reconnecting": self._live_voice_switching,
                "error": self._live_voice_error,
            }

    def set_live_voice_setting(self, enabled: bool) -> dict[str, object]:
        persisted_enabled = set_gemini_live_gender_setting(bool(enabled))
        requested_voice = (
            GEMINI_LIVE_FEMALE_VOICE
            if persisted_enabled
            else GEMINI_LIVE_DEFAULT_VOICE
        )
        with self._live_voice_lock:
            self._live_voice_enabled = persisted_enabled
            self._live_voice_error = ""
            reconnecting = self.running and self.connected
            voice_changed = requested_voice != self._live_voice_applied
            rollover_requested = (
                reconnecting
                and voice_changed
                and not self._live_voice_switching
            )
            if rollover_requested:
                self._live_voice_switching = True
                self._live_voice_change.set()
            switching = self._live_voice_switching

        if rollover_requested:
            self.interrupt_live_response()

        return {
            "enabled": persisted_enabled,
            "requested_voice": requested_voice,
            "applied": not voice_changed and self.connected,
            "active": self.running,
            "reconnecting": switching,
        }

    def _configured_live_voice(self) -> str:
        with self._live_voice_lock:
            return (
                GEMINI_LIVE_FEMALE_VOICE
                if self._live_voice_enabled
                else GEMINI_LIVE_DEFAULT_VOICE
            )

    def _refresh_live_voice_preference(self) -> bool:
        """Reload the persisted gender before every new Live connection."""
        enabled = get_gemini_live_gender_setting()
        with self._live_voice_lock:
            self._live_voice_enabled = enabled
        return enabled

    @staticmethod
    def _conversation_manager():
        try:
            from brain.conversation_coordinator import conversation_coordinator

            return conversation_coordinator.conversation
        except Exception as exc:
            print("[LIVE CONTEXT] Conversation manager unavailable:", exc)
            return None

    def _record_live_turn(
        self,
        user_text: str,
        assistant_text: str,
        turn_id: str,
        tool_results=(),
    ):
        manager = self._conversation_manager()
        if manager is None:
            return

        try:
            session_id = manager.get_session_id()
            if self._live_context_session_id != session_id:
                self._live_context_session_id = session_id
            if record_live_turn(
                manager,
                user_text,
                assistant_text,
                turn_id,
                tool_results,
            ):
                print("[LIVE CONTEXT] Recorded completed Live turn once.")
        except Exception as exc:
            print("[LIVE CONTEXT] Could not record Live turn:", exc)

    async def _restore_live_context(self, session) -> bool:
        """Restore recent project conversation turns without generating a reply."""
        manager = self._conversation_manager()
        if manager is None:
            return False

        try:
            session_id = manager.get_session_id()
            if self._live_context_session_id not in (None, session_id):
                return False
            self._live_context_session_id = session_id
            messages = recent_live_messages(manager, limit=10)
            if not messages:
                return False

            turns = [
                types.Content(
                    role=message["role"],
                    parts=[types.Part.from_text(text=message["content"])],
                )
                for message in messages
            ]
            await session.send_client_content(turns=turns, turn_complete=False)
            print(
                f"[LIVE CONTEXT] Restored {len(turns)} recent conversation turns."
            )
            return True
        except Exception as exc:
            print("[LIVE CONTEXT] Context restoration failed safely:", exc)
            return False

    def _next_live_generation(self) -> int:
        with self._live_interrupt_lock:
            self._live_generation += 1
            return self._live_generation

    def _live_generation_value(self) -> int:
        with self._live_interrupt_lock:
            return self._live_generation

    def _live_generation_current(self, generation: int) -> bool:
        with self._live_interrupt_lock:
            return self._live_generation == generation

    def _live_output_allowed(self, generation: int) -> bool:
        with self._live_interrupt_lock:
            return (
                self._live_generation == generation
                and not self._live_discard_audio
            )

    def _begin_live_audio_discard(self):
        with self._live_interrupt_lock:
            self._live_discard_audio = True

    def _finish_live_audio_discard(self):
        with self._live_interrupt_lock:
            self._live_discard_audio = False

    def _is_discarding_live_audio(self) -> bool:
        with self._live_interrupt_lock:
            return self._live_discard_audio

    def _set_live_turn_active(self, value: bool):
        with self._live_interrupt_lock:
            self._live_turn_active = bool(value)

    def _is_live_turn_active(self) -> bool:
        with self._live_interrupt_lock:
            return self._live_turn_active

    async def _send_live_interrupt(self, session):
        """End the current realtime input stream without closing Live."""
        try:
            # This is an installed-SDK-supported Live API operation. It keeps
            # the session open and the next audio chunk reopens the stream.
            await session.send_realtime_input(audio_stream_end=True)
        except Exception as exc:
            print("[LIVE] Interrupt signal unavailable:", exc)
        finally:
            with self._live_interrupt_lock:
                self._live_interrupt_pending = False

    def interrupt_live_response(self) -> bool:
        """Stop Live output locally and signal the active session safely."""
        with self._session_lock:
            session = self._session
            loop = self._session_loop

        with self._speaker_lock:
            speaker = self._speaker

        if not self.connected or session is None or loop is None:
            return False

        self._next_live_generation()
        if self._is_live_turn_active():
            self._begin_live_audio_discard()
        self._interrupt_speaker(speaker)

        # The authoritative local playback edge is immediate; no stale chunk
        # can write after the generation token changes.
        self._hud_stop_speaking()

        with self._live_interrupt_lock:
            if self._live_interrupt_pending:
                return True
            self._live_interrupt_pending = True

        try:
            asyncio.run_coroutine_threadsafe(
                self._send_live_interrupt(session),
                loop,
            )
        except Exception as exc:
            with self._live_interrupt_lock:
                self._live_interrupt_pending = False
            print("[LIVE] Interrupt dispatch failed:", exc)

        return True
            
    
    # * =========================================================
    # * LIVE MICROPHONE STATE
    # * =========================================================

    def set_microphone_enabled(
        self,
        enabled: bool,
        source="runtime",
    ):

        with self._microphone_lock:

            self._microphone_enabled = bool(
                enabled
            )

        print(
            "[LIVE] Microphone:",
            "ON" if enabled else "OFF",
            "source=",
            source,
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

    def _handle_live_voice_activity(self, active: bool):
        """Publish only real user-voice edges from the Live mic stream."""
        if not self.connected or not self.microphone_enabled() or self._hud_speaking:
            return

        try:
            if active:
                HUDIntegration.voice_activity(True)
            else:
                HUDIntegration.voice_activity(False)
        except Exception as exc:
            print(
                "[LIVE HUD] Voice activity event failed:",
                exc,
            )

    # * ---------------------------------------------------------

    def _hud_stop_speaking(self):
        try:
            # Live keeps the microphone/session open after assistant audio
            # ends. Returning to IDLE here contradicted the actual runtime.
            # A ready microphone is not the same as detected user speech.
            # Playback completion therefore returns to quiet IDLE; the mic VAD
            # will emit LISTENING again on the next speech-start edge.
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

    def _clear_session_resumption_handle(self):
        """Force the next Live connection to start a fresh session."""

        with self._session_resumption_lock:
            self._session_resumption_handle = None
            
            
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

    async def _execute_live_capability(
        self,
        action,
        parameters,
        *,
        invocation_id=None,
    ):
        """Execute blocking screen capture away from the Live event loop."""

        if action != "screen_vision_analyze":
            return execute_live_capability(
                action,
                parameters,
                invocation_id=invocation_id,
            )

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    execute_live_capability,
                    action,
                    parameters,
                    invocation_id=invocation_id,
                ),
                timeout=SCREEN_VISION_TIMEOUT_SECONDS,
            )
            image_bytes = (
                result.get("_live_image_bytes")
                if isinstance(result, dict)
                else None
            )
            if (
                isinstance(image_bytes, (bytes, bytearray))
                and len(image_bytes) > MAX_LIVE_SCREEN_IMAGE_BYTES
            ):
                return {
                    "ok": False,
                    "status": "failed",
                    "action": action,
                    "correlation_id": str(invocation_id or ""),
                    "message": "Screen image exceeded the Live payload limit.",
                }
            return result
        except asyncio.TimeoutError:
            return {
                "ok": False,
                "status": "timeout",
                "action": action,
                "correlation_id": str(invocation_id or ""),
                "message": "Screen capture timed out; Live analysis was not completed.",
            }

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
        
        self.set_microphone_enabled(True, source="agent_start")
        
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
                _build_jarvis_developer_tool(),
                build_live_capability_tool(),
                *build_live_search_tools(),
            ],

            speech_config=types.SpeechConfig(

                voice_config=types.VoiceConfig(

                    prebuilt_voice_config=(
                        types.PrebuiltVoiceConfig(
                            voice_name=self._configured_live_voice()
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

        microphone_status_state = {"last_logged": 0.0}
        voice_activity_detector = LiveVoiceActivityDetector()

        def process_microphone_audio(audio_bytes):
            """Process copied mic data on the Live loop, not PortAudio's callback thread."""
            try:
                samples = array("h")
                samples.frombytes(audio_bytes)
                if samples:
                    rms = math.sqrt(
                        sum(sample * sample for sample in samples) / len(samples)
                    )
                    activity_change = voice_activity_detector.update(rms)
                    if activity_change is not None:
                        self._handle_live_voice_activity(activity_change)

                self._queue_audio(input_queue, audio_bytes)
            except Exception as exc:
                print("[LIVE] Microphone audio processing error:", exc)

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
                voice_activity_detector.reset()
                return

            if status:
                # PortAudio invokes this callback on its real-time thread.
                # Never print from it: terminal I/O can block the callback and
                # contribute to the very overflow being diagnosed.
                now = time.monotonic()
                if now - microphone_status_state["last_logged"] >= 1.0:
                    microphone_status_state["last_logged"] = now
                    loop.call_soon_threadsafe(
                        print,
                        f"[LIVE] Microphone status: {status}",
                    )

            # Copy only and return immediately. RMS/VAD and queue mutation run
            # on the Live loop so the PortAudio real-time thread never performs
            # Python iteration, logging, or other potentially blocking work.
            audio_bytes = bytes(indata)
            loop.call_soon_threadsafe(
                process_microphone_audio,
                audio_bytes,
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

            with self._speaker_lock:
                self._speaker = speaker

            microphone.start()

            with self._speaker_io_lock:
                speaker.start()
                self._speaker_started = True

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
                reconnect_attempts = 0

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

                    requested_female = self._refresh_live_voice_preference()
                    configured_voice = self._configured_live_voice()
                    voice_rollover = self._live_voice_switching
                    session_resumption_handle = (
                        None
                        if voice_rollover
                        else self._get_session_resumption_handle()
                    )
                    if voice_rollover:
                        # Resumption keeps the previous Live session setup,
                        # including its voice. A voice change needs a fresh
                        # session so the new speech_config is authoritative.
                        self._clear_session_resumption_handle()
                    print(
                        "[LIVE VOICE] Requested preference:",
                        "FEMALE" if requested_female else "MALE",
                    )
                    print("[LIVE VOICE] Configured voice:", configured_voice)
                    if voice_rollover:
                        print(
                            "[LIVE VOICE] Using a fresh session for voice rollover."
                        )

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
                            _build_jarvis_developer_tool(),
                            build_live_capability_tool(),
                            *build_live_search_tools(),
                        ],

                        speech_config=types.SpeechConfig(

                            voice_config=types.VoiceConfig(

                                prebuilt_voice_config=(
                                    types.PrebuiltVoiceConfig(
                                        voice_name=configured_voice
                                    )
                                )

                            )

                        ),

                        session_resumption=(
                            types.SessionResumptionConfig(
                                handle=(
                                    session_resumption_handle
                                ),
                            )
                        )
                        if session_resumption_handle
                        else None,
                    )

                    connection_should_retry = False
                    connection_started_at = 0.0

                    try:

                        async with client.aio.live.connect(
                            model=LIVE_MODEL,
                            config=connection_config,
                        ) as session:

                            connection_started_at = time.monotonic()

                            print("[AGENT] Connected")
                            print(
                                f"[LIVE VOICE] Connection #{connection_number} "
                                f"ready with configured voice: {configured_voice}"
                            )

                            with self._session_lock:
                                self._session = session
                                self._session_loop = loop
                            self._set_connected(True)
                            with self._live_voice_lock:
                                self._live_voice_applied = (
                                    GEMINI_LIVE_FEMALE_VOICE
                                    if self._live_voice_enabled
                                    else GEMINI_LIVE_DEFAULT_VOICE
                                )
                                self._live_voice_error = ""
                                self._live_voice_switching = False

                            voice_activity_detector.reset()
                            HUDIntegration.idle()

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

                            if voice_rollover:
                                await self._restore_live_context(session)

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
                                voice_change_requested = False
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

                                        stop_reason = stop_task.result()

                                        if stop_reason == "voice_change_requested":
                                            self._live_voice_change.clear()
                                            voice_change_requested = True
                                            connection_should_retry = True

                                            if not receive_task.done():
                                                receive_task.cancel()

                                            await asyncio.gather(
                                                receive_task,
                                                return_exceptions=True,
                                            )

                                            break

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

                                            if result == "interrupted":

                                                # A user barge-in or server-side
                                                # interruption ends only this
                                                # turn. It is not a connection
                                                # failure and must not roll the
                                                # persistent Live session.
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

                                            if _is_expired_session_resumption_error(exc):
                                                print(
                                                    "[LIVE] Session resumption handle expired; "
                                                    "starting a fresh Live session."
                                                )
                                                self._clear_session_resumption_handle()

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

                                if voice_change_requested and not self._stop_event.is_set():
                                    stop_task = asyncio.create_task(
                                        self._wait_for_stop(),
                                        name="JARVIS-AgentStopWatcher",
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
                        print(
                            f"[LIVE VOICE] Connection #{connection_number} failed "
                            f"with configured voice: {locals().get('configured_voice', 'unknown')}"
                        )

                        with self._live_voice_lock:
                            requested_voice = (
                                GEMINI_LIVE_FEMALE_VOICE
                                if self._live_voice_enabled
                                else GEMINI_LIVE_DEFAULT_VOICE
                            )
                            if requested_voice != self._live_voice_applied:
                                self._live_voice_error = (
                                    f"Gemini Live rejected the requested voice "
                                    f"{requested_voice}: {exc}"
                                )
                                self._live_voice_enabled = (
                                    self._live_voice_applied == GEMINI_LIVE_FEMALE_VOICE
                                )
                                self._live_voice_switching = False
                                self._live_voice_change.clear()
                                set_gemini_live_gender_setting(self._live_voice_enabled)

                        if _is_expired_session_resumption_error(exc):
                            print(
                                "[LIVE] Session resumption handle expired; "
                                "starting a fresh Live session."
                            )
                            self._clear_session_resumption_handle()

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

                        if (
                            connection_started_at
                            and time.monotonic() - connection_started_at >= 10.0
                        ):
                            reconnect_attempts = 0
                        reconnect_attempts += 1
                        reconnect_delay = _live_reconnect_delay(reconnect_attempts)
                        print(
                            "[LIVE] Reconnect backoff:",
                            f"{reconnect_delay:.1f}s",
                        )
                        await asyncio.sleep(reconnect_delay)

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

            voice_activity_detector.reset()
            self._finish_live_audio_discard()

            with self._speaker_lock:
                self._speaker = None

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

                with self._speaker_io_lock:
                    try:

                        speaker.stop()

                    except Exception:
                        pass

                    try:

                        speaker.close()

                    except Exception:
                        pass

                    self._speaker_started = False

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

    def _interrupt_speaker(
        self,
        speaker,
    ) -> bool:
        """
        Immediately interrupt Live audio playback.

        IMPORTANT:
        abort() clears the current PortAudio playback,
        but it leaves the stream stopped. Do not restart it
        here: PortAudio may still be draining the device,
        and an immediate start can raise PaErrorCode -9999.
        The stream is reopened lazily before the next chunk.

        This affects ONLY the Agent speaker.
        """

        if speaker is None:

            return True

        with self._speaker_io_lock:
            try:

                # * Immediately discard currently buffered audio.
                speaker.abort()
                self._speaker_started = False

                print(
                    "[LIVE] Speaker output interrupted."
                )

                print(
                    "[LIVE] Speaker stream left stopped until next output."
                )

                return True

            except Exception as exc:

                print(
                    "[LIVE] Speaker interruption failed:",
                    exc,
                )
                return False

    def _write_speaker(self, speaker, audio: bytes):
        """Start output only after an interrupt has fully returned."""
        with self._speaker_io_lock:
            if not self._speaker_started:
                speaker.start()
                self._speaker_started = True

            speaker.write(audio)

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
        
        turn_id = uuid4().hex
        input_text = ""
        output_text = ""
        tool_result_summaries = []
        turn_generation = self._live_generation_value()
        scheduled_whatsapp_results = {}

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

                self._set_live_turn_active(True)

                if (
                    not self._live_generation_current(turn_generation)
                    and not self._is_discarding_live_audio()
                ):
                    self._set_live_turn_active(False)
                    return "interrupted"

                # A Live interruption can have already returned the current
                # receive call while Gemini is still draining the interrupted
                # turn. Keep consuming that turn, but discard every late
                # audio/tool event until its server-side boundary arrives.
                if self._is_discarding_live_audio():
                    server_content = getattr(response, "server_content", None)
                    if server_content and (
                        getattr(server_content, "interrupted", False)
                        or getattr(server_content, "turn_complete", False)
                    ):
                        self._finish_live_audio_discard()
                        self._set_live_turn_active(False)
                        self._hud_stop_speaking()
                        return "turn_complete"
                    continue
                
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
                    batch_results = {}
                    scheduled_commands = {
                        str(function_call.args.get("command", "")).strip().casefold()
                        for function_call in response.tool_call.function_calls
                        if structured_action_from_tool_name(function_call.name) == "create_schedule"
                        and isinstance(function_call.args, dict)
                        and str(function_call.args.get("command", "")).strip()
                    }
                    scheduled_whatsapp_messages = {
                        (
                            str(function_call.args.get("contact", "")).strip().casefold(),
                            str(function_call.args.get("message", "")).strip().casefold(),
                        )
                        for function_call in response.tool_call.function_calls
                        if structured_action_from_tool_name(function_call.name) == "schedule_whatsapp_message"
                        and isinstance(function_call.args, dict)
                        and str(function_call.args.get("contact", "")).strip()
                        and str(function_call.args.get("message", "")).strip()
                    }

                    for function_call in (
                        response.tool_call.function_calls
                    ):

                        invocation_id = str(function_call.id or "").strip()
                        invocation_status, invocation_value = (
                            self._live_invocations.begin(invocation_id)
                        )
                        if invocation_status == "cached":
                            function_responses.append(invocation_value)
                            continue
                        if invocation_status == "wait":
                            cached_response = await self._live_invocations.wait(
                                invocation_value
                            )
                            if cached_response is not None:
                                function_responses.append(cached_response)
                            else:
                                function_responses.append(
                                    build_live_function_response(
                                        types,
                                        function_call.id,
                                        function_call.name,
                                        {
                                            "success": False,
                                            "status": "duplicate_wait_timeout",
                                            "message": "The original Live invocation did not finish in time.",
                                        },
                                    )
                                )
                            continue

                        function_name = (
                            function_call.name
                        )

                        # A single Live response can contain the same command
                        # more than once. Coalesce only within this response
                        # batch; separate user turns remain independent.
                        batch_key = None
                        if function_name in {"jarvis_command", "jarvis_capability"} or function_name.startswith("jarvis_capability__"):
                            batch_key = (
                                function_name,
                                json.dumps(function_call.args or {}, sort_keys=True, default=str),
                            )
                            if batch_key in batch_results:
                                function_responses.append(
                                    build_live_function_response(
                                        types,
                                        function_call.id,
                                        function_name,
                                        batch_results[batch_key],
                                    )
                                )
                                print("[LIVE TOOL] Duplicate command in one response batch; reusing result")
                                continue

                        print(
                            "[LIVE TOOL]",
                            function_name,
                        )

                        HUDIntegration.executing(function_name or "Live tool")

                        # * -----------------------------------------
                        # * JARVIS COMMAND
                        # * -----------------------------------------

                        if function_name in {"jarvis_command", "jarvis_developer"}:

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

                                    scheduled_whatsapp = parse_scheduled_whatsapp(command)
                                    is_scheduled_duplicate = (
                                        command.casefold() in scheduled_commands
                                        or (
                                            scheduled_whatsapp is not None
                                            and (
                                                scheduled_whatsapp["contact"].casefold(),
                                                scheduled_whatsapp["message"].casefold(),
                                            ) in scheduled_whatsapp_messages
                                        )
                                    )
                                    if is_scheduled_duplicate:
                                        result = {
                                            "success": True,
                                            "status": "scheduled_only",
                                            "message": "That command is already stored for scheduled execution; it was not run now.",
                                        }
                                        print("[LIVE TOOL] Scheduled command was not dispatched immediately:", command)
                                        raise StopIteration

                                    # * ---------------------------------
                                    # * Existing JARVIS dispatcher
                                    # * remains authoritative.
                                    # * ---------------------------------

                                    with live_execution(session=session, loop=asyncio.get_running_loop()):

                                        dispatch_result = dispatch(
                                            command,
                                            live_invocation_id=function_call.id,
                                        )

                                        live_task_results = await drain_live_tasks()

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

                                    result = resolve_live_task_results(
                                        {"success": bool(dispatch_result), "status": "completed" if dispatch_result else "pending", "message": authoritative_response},
                                        live_task_results,
                                    )
                                    if result.get("status") == "failed":

                                        result = {
                                            "success": False,
                                            "status": "failed",
                                            "message": authoritative_response or "The Live command failed during asynchronous execution.",
                                        }

                                    elif authoritative_response:

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
                                        result = preserve_live_media(
                                            result,
                                            dispatch_result,
                                        )

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

                                except StopIteration:
                                    pass
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
                                    args.get("provider"),
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
                                schedule_key = None
                                if action == "schedule_whatsapp_message":
                                    schedule_key = _live_whatsapp_schedule_key(args)
                                    if schedule_key in scheduled_whatsapp_results:
                                        result = scheduled_whatsapp_results[schedule_key]
                                        print("[LIVE TOOL] Duplicate WhatsApp schedule in one turn; reusing result")
                                        raise StopIteration
                                with live_execution(session=session, loop=asyncio.get_running_loop()):
                                    result = await self._execute_live_capability(
                                        action,
                                        args,
                                        invocation_id=function_call.id,
                                    )
                                    live_task_results = await drain_live_tasks()
                                    live_responses = get_live_responses()
                                    result = resolve_live_task_results(result, live_task_results, action)
                                    if result.get("status") == "failed":
                                        result = {
                                            "ok": False,
                                            "status": "failed",
                                            "action": action,
                                            "message": " ".join(live_responses) or "The Live capability failed during asynchronous execution.",
                                        }
                                    elif live_responses and not result.get("authoritative"):
                                        result = {
                                            "ok": True,
                                            "status": "reported_success",
                                            "action": action,
                                            "authoritative": True,
                                            "message": " ".join(live_responses),
                                        }
                                if result.get("authoritative"):
                                    jarvis_authoritative_response = True
                                if schedule_key is not None:
                                    scheduled_whatsapp_results[schedule_key] = result
                            except StopIteration:
                                pass
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
                                    result = await self._execute_live_capability(
                                        action,
                                        parameters,
                                        invocation_id=function_call.id,
                                    )
                                    live_task_results = await drain_live_tasks()
                                    live_responses = get_live_responses()
                                    result = resolve_live_task_results(result, live_task_results, action)
                                    if result.get("status") == "failed":
                                        result = {
                                            "ok": False,
                                            "status": "failed",
                                            "action": action,
                                            "message": " ".join(live_responses) or "The Live capability failed during asynchronous execution.",
                                        }
                                    elif live_responses and not result.get("authoritative"):
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

                        if batch_key is not None:
                            batch_results[batch_key] = result

                        live_function_response = build_live_function_response(
                            types,
                            function_call.id,
                            function_name,
                            result,
                        )
                        tool_result_summaries.append(
                            json.dumps(result, ensure_ascii=False, default=str)[:1200]
                        )
                        function_responses.append(live_function_response)
                        self._live_invocations.complete(
                            invocation_id,
                            live_function_response,
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

                    # Tool execution is part of the response. Keep THINKING
                    # active until Gemini produces audio or completes the turn.
                    HUDIntegration.thinking()

                    # * ---------------------------------------------
                    # * Send result back to Gemini.
                    # * ---------------------------------------------

                    if function_responses:
                        await send_live_tool_response(
                            session,
                            function_responses=function_responses
                        )

                    continue

                if self._stop_event.is_set():

                    return "stopped"

                # * =============================================
                # * AUDIO OUTPUT
                # * =============================================

                if response.data:

                    if not self._live_output_allowed(turn_generation):
                        return "interrupted"

                    # * Gemini has produced actual speaker audio.
                    # * Tell the HUD that JARVIS is now speaking.
                    self._hud_start_speaking()

                    await asyncio.to_thread(
                        self._write_speaker,
                        speaker,
                        response.data,
                    )

                    if not self._live_output_allowed(turn_generation):
                        return "interrupted"

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

                        input_text = merge_transcript_text(input_text, user_text)

                        print(
                            "[YOU]",
                            user_text,
                        )

                        try:
                            HUDIntegration.thinking()
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

                    output_chunk = (
                        output_transcription.text.strip()
                    )

                    if output_chunk:
                        output_text = merge_transcript_text(output_text, output_chunk)

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
                    self._set_live_turn_active(False)

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

                    self._set_live_turn_active(False)

                    complete_output = output_text.strip()

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
                    self._record_live_turn(
                        input_text,
                        complete_output,
                        turn_id,
                        tool_result_summaries,
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

        while not self._stop_event.is_set() and not self._live_voice_change.is_set():

            await asyncio.sleep(
                0.1
            )

        return "stop requested" if self._stop_event.is_set() else "voice_change_requested"

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


def interrupt_live_response() -> bool:
    """Interrupt Live output without closing the persistent session."""

    return _agent.interrupt_live_response()


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


def agent_state(
    _data=None,
):
    """Return authoritative structured state for API consumers.

    ``agent_status`` remains a backward-compatible human-readable response.
    New API code should use these fields instead of comparing presentation
    strings.
    """

    running = _agent.running
    connected = _agent.connected

    if connected:
        state = "connected"
    elif running:
        state = "reconnecting"
    else:
        state = "stopped"

    return {
        "running": running,
        "connected": connected,
        "state": state,
        "microphone_enabled": (
            _agent.microphone_enabled()
            if running
            else False
        ),
        "controller": "gemini-live",
    }


def live_voice_state(_data=None):
    return _agent.live_voice_setting()


def set_live_voice_state(enabled: bool):
    return _agent.set_live_voice_setting(enabled)
