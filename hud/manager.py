"""
JARVIS PRO HUD
HUD Manager
"""

from datetime import datetime

from .bus import hud_bus

from .events import (
    HUDEvent,
    HUD_IDLE,
    HUD_LISTENING,
    HUD_THINKING,
    HUD_SPEAKING,
    HUD_EXECUTING,
    HUD_TASK_STARTED,
    HUD_TASK_FINISHED,
    HUD_TASK_FAILED,
    HUD_VOICE_MODE_CHANGED,
    HUD_AI_MODEL_CHANGED,
    HUD_SYSTEM_UPDATE,
    HUD_SYSTEM_ACTIVITY,
    HUD_PERSONAL_LINKS,
    HUD_NOTIFICATION,
    HUD_ERROR,
    HUD_COMMAND,
    HUD_RESPONSE,
)

from .state import HUDState


class HUDManager:

    def __init__(self):

        self.state = HUDState()

    # * =====================================================
    # * Internal
    # * =====================================================

    def _publish(
        self,
        name,
        data=None,
        source="jarvis",
    ):

        if data is None:
            data = {}

        event = HUDEvent(
            name=name,
            data=data,
            source=source,
        )

        self.state.last_event = name

        self.state.last_update = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        hud_bus.publish(event)

    # * =====================================================
    # * Voice
    # * =====================================================

    def listening(self):

        # * -----------------------------------------------------
        # * SPEAKING has priority over LISTENING.
        #
        # * The microphone can remain active while JARVIS is
        # ! speaking. Do not allow the microphone listener to
        # * overwrite the HUD speaking state.
        # * -----------------------------------------------------

        if self.state.speaking:

            return

        self.state.status = HUD_LISTENING

        self.state.listening = True
        self.state.speaking = False
        self.state.thinking = False
        self.state.executing = False

        self._publish(
            HUD_LISTENING
        )

    # * -----------------------------------------------------

    def thinking(self):

        self.state.status = HUD_THINKING

        self.state.listening = False
        self.state.speaking = False
        self.state.thinking = True
        self.state.executing = False

        self._publish(HUD_THINKING)

    # * -----------------------------------------------------

    def speaking(self):

        self.state.status = HUD_SPEAKING

        self.state.listening = False
        self.state.speaking = True
        self.state.thinking = False
        self.state.executing = False

        self._publish(HUD_SPEAKING)

    # * -----------------------------------------------------

    def idle(self):

        self.state.status = HUD_IDLE

        self.state.listening = False
        self.state.speaking = False
        self.state.thinking = False
        self.state.executing = False

        self._publish(HUD_IDLE)

    # * =====================================================
    # * Tasks
    # * =====================================================

    def executing(self, task=""):

        self.state.status = HUD_EXECUTING

        self.state.current_task = task

        self.state.task_status = "running"

        self.state.executing = True

        self._publish(
            HUD_EXECUTING,
            {
                "task": task
            }
        )

    # * -----------------------------------------------------

    def task_started(self, task):

        self.state.current_task = task

        self.state.task_status = "running"

        self._publish(
            HUD_TASK_STARTED,
            {
                "task": task
            }
        )

    # * -----------------------------------------------------

    def task_finished(self, task=""):

        self.state.task_status = "finished"

        self.state.executing = False

        self._publish(
            HUD_TASK_FINISHED,
            {
                "task": task
            }
        )

    # * -----------------------------------------------------

    def task_failed(
        self,
        task="",
        error="",
    ):

        self.state.task_status = "failed"

        self.state.executing = False

        self.state.error = error

        self._publish(
            HUD_TASK_FAILED,
            {
                "task": task,
                "error": error,
            }
        )

    # * =====================================================
    # AI
    # * =====================================================

    def ai_model(
        self,
        provider,
        model,
    ):

        self.state.ai_model = (
            f"{provider} {model}"
        )

        self._publish(
            HUD_AI_MODEL_CHANGED,
            {
                "provider": provider,
                "model": model,
            }
        )

    # * =====================================================
    # * Voice Mode
    # * =====================================================

    def voice_mode(self, mode):

        self.state.voice_mode = mode

        self._publish(
            HUD_VOICE_MODE_CHANGED,
            {
                "mode": mode
            }
        )

    # * =====================================================
    # * System
    # * =====================================================

    def system_update(self, data):

        if not isinstance(data, dict):
            return

        self.state.system.update(data)

        self._publish(
            HUD_SYSTEM_UPDATE,
            data,
        )
        
    # * =====================================================
    # * System Activity
    # * =====================================================

    def system_activity(
        self,
        message,
        actions=None,
    ):

        message = str(
            message
        ).strip()

        if not message:

            return

        self._publish(
            HUD_SYSTEM_ACTIVITY,
            {
                "message": message,
                "actions": actions or [],
            }
        )

    def personal_links(self, entries):
        """Publish safe structured website entries for the Activity Log."""

        safe_entries = []

        for entry in entries or []:
            if not isinstance(entry, dict):
                continue

            name = str(entry.get("name", "")).strip()
            url = str(entry.get("url", "")).strip()

            if name and url:
                safe_entries.append({"name": name, "url": url})

        self._publish(
            HUD_PERSONAL_LINKS,
            {
                "title": "MY WEBSITES",
                "entries": safe_entries,
                "message": (
                    "" if safe_entries
                    else "No personal websites are configured."
                ),
            },
        )

    # * =====================================================
    # * Command
    # * =====================================================

    def command(self, text, source="jarvis"):

        self.state.last_command = str(text)

        self._publish(
            HUD_COMMAND,
            {
                "text": str(text)
            },
            source=source,
        )

    # * =====================================================
    # * Response
    # * =====================================================

    def response(self, text, speaker="jarvis"):

        self.state.last_response = str(text)

        self._publish(
            HUD_RESPONSE,
            {
                "text": str(text),
                "speaker": str(speaker),
            }
        )

    # * =====================================================
    # * Notification
    # * =====================================================

    def notify(self, title_or_message, message=None, level="INFO", source="jarvis", metadata=None):

        if message is None:
            title = "JARVIS"
            message = str(title_or_message)
        else:
            title = str(title_or_message)

        self.state.notification = str(message)

        self._publish(
            HUD_NOTIFICATION,
            {
                "title": title,
                "message": str(message)
                ,"level": str(level).upper(),
                "source": str(source),
                "metadata": metadata or {},
            }
        )

    # * =====================================================
    # ! Error
    # * =====================================================

    def error(self, message):

        self.state.error = str(message)

        self._publish(
            HUD_ERROR,
            {
                "error": str(message)
            }
        )


hud = HUDManager()
