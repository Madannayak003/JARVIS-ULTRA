"""
JARVIS PRO
Phase 11.3.7

Execution Context Resolver

Converts an already-executed JARVIS action into
semantic conversational context.

IMPORTANT:

This module does NOT:

    - execute actions
    - dispatch commands
    - call the planner
    - call an LLM
    - modify existing skills
    - modify existing routers

It only describes an action that has ALREADY been
executed by the existing JARVIS pipeline.

Natural Conversation uses this information to
understand follow-ups such as:

    "make it louder"
    "pause it"
    "close it"
    "continue"
    "change that"
    "play the same thing"
"""


from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


# * ============================================================
# * Execution Context
# * ============================================================

@dataclass
class ExecutionContext:

    application: Optional[str] = None

    skill: Optional[str] = None

    topic: Optional[str] = None

    task: Optional[str] = None

    intent: Optional[str] = None

    action: Optional[str] = None

    object: Optional[Any] = None

    objects: Optional[list[Any]] = None


# * ============================================================
# * Execution Context Resolver
# * ============================================================

class ExecutionContextResolver:

    """
    Converts existing JARVIS action names into semantic
    conversational information.

    This resolver is intentionally deterministic.

    No AI is used here.
    """

    # * ========================================================
    # * Action Definitions
    # * ========================================================

    ACTION_CONTEXT = {

        # * ----------------------------------------------------
        # * Spotify
        # * ----------------------------------------------------

        "spotify_open": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "open spotify",
            "intent": "spotify_open",
            "action": "open",
            "object": "spotify",
        },

        "spotify_close": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "close spotify",
            "intent": "spotify_close",
            "action": "close",
            "object": "spotify",
        },

        "spotify_play": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "play music",
            "intent": "spotify_play",
            "action": "play",
            "object": "music",
        },

        "spotify_pause": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "pause music",
            "intent": "spotify_pause",
            "action": "pause",
            "object": "music",
        },

        "spotify_next": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "next song",
            "intent": "spotify_next",
            "action": "next",
            "object": "song",
        },

        "spotify_previous": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "previous song",
            "intent": "spotify_previous",
            "action": "previous",
            "object": "song",
        },

        "spotify_volume_up": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "increase music volume",
            "intent": "spotify_volume_up",
            "action": "increase_volume",
            "object": "music",
        },

        "spotify_volume_down": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "decrease music volume",
            "intent": "spotify_volume_down",
            "action": "decrease_volume",
            "object": "music",
        },

        "spotify_play_song": {
            "application": "spotify",
            "skill": "spotify",
            "topic": "music",
            "task": "play song",
            "intent": "spotify_play_song",
            "action": "play",
            "object": "song",
        },


        # * ----------------------------------------------------
        # * YouTube
        # * ----------------------------------------------------

        "youtube_play_first": {
            "application": "youtube",
            "skill": "youtube",
            "topic": "video",
            "task": "play video",
            "intent": "youtube_play",
            "action": "play",
            "object": "video",
        },

        "youtube_pause": {
            "application": "youtube",
            "skill": "youtube",
            "topic": "video",
            "task": "pause video",
            "intent": "youtube_pause",
            "action": "pause",
            "object": "video",
        },

        "youtube_resume": {
            "application": "youtube",
            "skill": "youtube",
            "topic": "video",
            "task": "resume video",
            "intent": "youtube_resume",
            "action": "resume",
            "object": "video",
        },

        "youtube_next": {
            "application": "youtube",
            "skill": "youtube",
            "topic": "video",
            "task": "next video",
            "intent": "youtube_next",
            "action": "next",
            "object": "video",
        },

        "youtube_previous": {
            "application": "youtube",
            "skill": "youtube",
            "topic": "video",
            "task": "previous video",
            "intent": "youtube_previous",
            "action": "previous",
            "object": "video",
        },

        "youtube_search": {
            "application": "youtube",
            "skill": "youtube",
            "topic": "search",
            "task": "search youtube",
            "intent": "youtube_search",
            "action": "search",
            "object": "search",
        },


        # * ----------------------------------------------------
        # * Browser
        # * ----------------------------------------------------

        "google_search": {
            "application": "google",
            "skill": "browser",
            "topic": "search",
            "task": "search google",
            "intent": "google_search",
            "action": "search",
            "object": "search",
        },

        "browser_open_result": {
            "application": "browser",
            "skill": "browser",
            "topic": "search",
            "task": "open browser result",
            "intent": "browser_open_result",
            "action": "open",
        },

        "github_search": {
            "application": "github",
            "skill": "browser",
            "topic": "search",
            "task": "search github",
            "intent": "github_search",
            "action": "search",
            "object": "search",
        },

        "chatgpt_search": {
            "application": "chatgpt",
            "skill": "browser",
            "topic": "search",
            "task": "search chatgpt",
            "intent": "chatgpt_search",
            "action": "search",
            "object": "search",
        },


        # * ----------------------------------------------------
        # * WhatsApp
        # * ----------------------------------------------------

        "whatsapp_open": {
            "application": "whatsapp",
            "skill": "whatsapp",
            "topic": "communication",
            "task": "open whatsapp",
            "intent": "whatsapp_open",
            "action": "open",
            "object": "whatsapp",
        },

        "whatsapp_close": {
            "application": "whatsapp",
            "skill": "whatsapp",
            "topic": "communication",
            "task": "close whatsapp",
            "intent": "whatsapp_close",
            "action": "close",
            "object": "whatsapp",
        },

        "whatsapp_send_message": {
            "application": "whatsapp",
            "skill": "whatsapp",
            "topic": "communication",
            "task": "send whatsapp message",
            "intent": "whatsapp_send_message",
            "action": "send",
            "object": "message",
        },


        # * ----------------------------------------------------
        # * System
        # * ----------------------------------------------------

        "volume": {
            "application": "system",
            "skill": "system",
            "topic": "system",
            "task": "change volume",
            "intent": "volume",
            "action": "change_volume",
            "object": "system volume",
        },

        "brightness": {
            "application": "system",
            "skill": "system",
            "topic": "system",
            "task": "change brightness",
            "intent": "brightness",
            "action": "change_brightness",
            "object": "brightness",
        },

        "screenshot": {
            "application": "system",
            "skill": "screen",
            "topic": "screen",
            "task": "take screenshot",
            "intent": "screenshot",
            "action": "capture",
            "object": "screenshot",
        },
    }


    # * ========================================================
    # * Resolve
    # * ========================================================

    def resolve(
        self,
        action_name: str,
        action_data: Optional[dict] = None,
        result: Any = None,
    ) -> ExecutionContext:

        action_data = action_data or {}

        # * ----------------------------------------------------
        # * Start with known action definition
        # * ----------------------------------------------------

        definition = self.ACTION_CONTEXT.get(
            action_name,
            {}
        ).copy()

        # * ----------------------------------------------------
        # * Allow explicit metadata from an action plan
        # * to override defaults.
        # * ----------------------------------------------------

        for key in [
            "application",
            "skill",
            "topic",
            "task",
            "intent",
            "action",
            "object",
            "objects",
        ]:

            value = action_data.get(key)

            if value is not None:

                definition[key] = value

        # * ----------------------------------------------------
        # * Generic application metadata
        #
        # * Existing routers use:
        #
        # * {"action": "open", "app": "notepad"}
        #
        # * Natural Conversation needs the application/object
        # * information preserved in conversational context.
        # * ----------------------------------------------------

        if action_name == "open":

            app = action_data.get("app")

            if app:

                app = str(app).strip().lower()

                definition["application"] = app
                definition["object"] = app

                # * Windows applications
                if app in [
                    "notepad",
                    "calculator",
                    "calc",
                    "paint",
                    "cmd",
                    "command prompt",
                    "powershell",
                    "explorer",
                    "file explorer",
                    "task manager",
                    "registry editor",
                    "device manager",
                    "control panel",
                    "settings",
                ]:

                    definition["skill"] = "system"
                    definition["topic"] = "application"
                    definition["task"] = (
                        f"open {app}"
                    )
                    definition["intent"] = "open"

                # * Browser applications / websites
                elif app in [
                    "google",
                    "youtube",
                    "chrome",
                    "gmail",
                    "github",
                    "chatgpt",
                ]:

                    definition["skill"] = "browser"
                    definition["topic"] = "application"
                    definition["task"] = (
                        f"open {app}"
                    )
                    definition["intent"] = "open"

                else:

                    definition["topic"] = "application"
                    definition["task"] = (
                        f"open {app}"
                    )
                    definition["intent"] = "open"

        # * ----------------------------------------------------
        # * Generic close_process metadata
        #
        # * Used by Natural Conversation:
        #
        # * "close it"
        #
        # * -> close_process(notepad)
        # * ----------------------------------------------------

        if action_name == "close_process":

            process = action_data.get("process")

            if process:

                process = str(
                    process
                ).strip().lower()

                definition["application"] = process
                definition["skill"] = "system"
                definition["topic"] = "application"
                definition["task"] = (
                    f"close {process}"
                )
                definition["intent"] = "close"
                definition["action"] = (
                    "close"
                )
                definition["object"] = process
                
        # * ----------------------------------------------------
        # * Browser result context
        #
        # * Preserve the real Google / YouTube results that
        # * were produced by the already-executed browser action.
        #
        # * This allows Natural Conversation references such as:
        #
        # * "open the second one"
        # * "play the third one"
        #
        # * to resolve through the existing ConversationContext.
        # * ----------------------------------------------------

        if action_name in {
            "google_search",
            "browser_open_result",
            "youtube_search",
            "youtube_play_first",
            "youtube_play_result",
            "youtube_next",
            "youtube_previous",
        }:

            try:

                from core.browser_context import (
                    browser_context,
                )

                # * --------------------------------------------
                # * Google search results
                # * --------------------------------------------

                if action_name in {
                    "google_search",
                    "browser_open_result",
                }:

                    browser_results = (
                        browser_context.last_search_results
                    )

                    if browser_results:

                        definition["objects"] = (
                            browser_results
                        )

                        if action_name == "google_search":

                            definition["object"] = (
                                browser_results
                            )

                        else:

                            target_url = str(
                                action_data.get(
                                    "url",
                                    "",
                                )
                                or ""
                            ).strip()

                            current_result = next(
                                (
                                    browser_result
                                    for browser_result
                                    in browser_results
                                    if browser_result.url == target_url
                                ),
                                None,
                            )

                            if (
                                current_result is None
                                and browser_context.selected_result
                                in browser_results
                            ):

                                current_result = (
                                    browser_context.selected_result
                                )

                            definition["object"] = current_result

                # * --------------------------------------------
                # * YouTube queue
                # * --------------------------------------------

                elif action_name in {
                    "youtube_search",
                    "youtube_play_first",
                    "youtube_play_result",
                    "youtube_next",
                    "youtube_previous",
                }:
                    youtube_results = (
                        browser_context.youtube_queue
                    )

                    if youtube_results:

                        definition["objects"] = (
                            youtube_results
                        )

                        definition["object"] = (
                            browser_context.current_youtube_video
                        )

            except Exception as e:

                print(
                    "[EXECUTION CONTEXT] "
                    f"Browser context enrichment failed: {e}"
                )

        # * ----------------------------------------------------
        # * Action itself is always authoritative
        # * ----------------------------------------------------

        definition.setdefault(
            "action",
            action_name
        )

        # * ----------------------------------------------------
        # * Build result
        # * ----------------------------------------------------

        return ExecutionContext(

            application=definition.get(
                "application"
            ),

            skill=definition.get(
                "skill"
            ),

            topic=definition.get(
                "topic"
            ),

            task=definition.get(
                "task"
            ),

            intent=definition.get(
                "intent"
            ),

            action=definition.get(
                "action"
            ),

            object=definition.get(
                "object"
            ),

            objects=definition.get(
                "objects"
            ),
        )


# * ============================================================
# * Shared Resolver
# * ============================================================

execution_context_resolver = (
    ExecutionContextResolver()
)
