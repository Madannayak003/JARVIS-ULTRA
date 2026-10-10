"""
JARVIS PRO
HUD Integration Layer

Safe one-way integration between JARVIS runtime
and the HUD system.

IMPORTANT:

JARVIS controls the HUD.

HUD NEVER controls JARVIS.

This module is intentionally passive.

When integration is disabled, every method becomes
a no-op and the existing JARVIS runtime is unaffected.
"""

from .emitter import HUDEmitter
from .event_contract import HUDEvent
from config.hud_settings import HUD_ENABLED


# * ============================================================
# * HUD Integration
# * ============================================================

class HUDIntegration:

    """
    Safe bridge used by the JARVIS runtime.

    The runtime can report events through this class
    without knowing anything about HUDManager, HUDState,
    or the UI implementation.
    """

    # * --------------------------------------------------------
    # * Internal event sender
    # * --------------------------------------------------------

    @staticmethod
    def _emit(event, data=None):

        if not HUD_ENABLED:
            return

        try:

            HUDEmitter.emit(
                event,
                data
            )

        except Exception as e:

            # ! HUD failure must NEVER crash JARVIS.

            print(
                "[HUD INTEGRATION] "
                f"HUD event failed: {e}"
            )

    # * ========================================================
    # * Voice
    # * ========================================================

    @classmethod
    def listening(cls):

        cls._emit(
            HUDEvent.LISTENING
        )

    @classmethod
    def speaking(cls):

        cls._emit(
            HUDEvent.SPEAKING
        )

    @classmethod
    def idle(cls):

        cls._emit(
            HUDEvent.IDLE
        )

    # * ========================================================
    # AI
    # * ========================================================

    @classmethod
    def thinking(cls):

        cls._emit(
            HUDEvent.THINKING
        )

    @classmethod
    def ai_model(
        cls,
        provider,
        model
    ):

        cls._emit(
            HUDEvent.AI_MODEL_CHANGED,
            {
                "provider": provider,
                "model": model
            }
        )

    # * ========================================================
    # * Tasks
    # * ========================================================

    @classmethod
    def task_started(
        cls,
        task
    ):

        cls._emit(
            HUDEvent.TASK_STARTED,
            {
                "task": task
            }
        )

    @classmethod
    def executing(
        cls,
        task=""
    ):

        cls._emit(
            HUDEvent.EXECUTING,
            {
                "task": task
            }
        )

    @classmethod
    def task_finished(
        cls,
        task=""
    ):

        cls._emit(
            HUDEvent.TASK_FINISHED,
            {
                "task": task
            }
        )

    @classmethod
    def task_failed(
        cls,
        task="",
        error=""
    ):

        cls._emit(
            HUDEvent.TASK_FAILED,
            {
                "task": task,
                "error": error
            }
        )

    # * ========================================================
    # * Voice Mode
    # * ========================================================

    @classmethod
    def voice_mode(
        cls,
        mode
    ):

        cls._emit(
            HUDEvent.VOICE_MODE_CHANGED,
            {
                "mode": mode
            }
        )

    # * ========================================================
    # * System
    # * ========================================================

    @classmethod
    def system_update(
        cls,
        data
    ):

        cls._emit(
            HUDEvent.SYSTEM_UPDATE,
            data
        )
        
    # * ========================================================
    # * System Activity
    # * ========================================================

    @classmethod
    def system_activity(
        cls,
        message,
    ):

        cls._emit(
            HUDEvent.SYSTEM_ACTIVITY,
            {
                "message": str(message)
            }
        )

    @classmethod
    def activity_action(cls, message, actions):
        cls._emit(
            HUDEvent.SYSTEM_ACTIVITY,
            {
                "message": str(message),
                "actions": actions or [],
                "speaker": "jarvis",
            },
        )

    @classmethod
    def personal_links(
        cls,
        entries,
    ):

        cls._emit(
            HUDEvent.PERSONAL_LINKS,
            {
                "entries": entries or [],
            },
        )

    # * ========================================================
    # * Conversation Activity Log
    #
    # ! IMPORTANT:
    #
    # * These are conversation events.
    #
    # * They are intentionally separate from:
    #
    # * listening
    # * thinking
    # * speaking
    # * executing
    #
    # * Those are runtime states, not activity messages.
    # * ========================================================

    @classmethod
    def command(
        cls,
        text,
        source="jarvis",
    ):

        cls._emit(
            HUDEvent.COMMAND,
            {
                "text": str(text),
                "source": str(source),
            }
        )

    @classmethod
    def response(
        cls,
        text,
        speaker="jarvis",
    ):

        cls._emit(
            HUDEvent.RESPONSE,
            {
                "text": str(text),
                "speaker": str(speaker),
            }
        )

    # * ========================================================
    # * Notifications
    # * ========================================================

    @classmethod
    def notify(
        cls,
        title_or_message,
        message=None,
        level="INFO",
        source="jarvis",
        metadata=None,
    ):
        """Emit a structured notification while preserving notify(message)."""

        if message is None:
            title = "JARVIS"
            message = str(title_or_message)
        else:
            title = str(title_or_message)
            message = str(message)

        cls._emit(
            HUDEvent.NOTIFICATION,
            {
                "title": title,
                "message": message,
                "level": str(level).upper(),
                "source": str(source),
                "metadata": metadata or {},
            }
        )

    @classmethod
    def error(
        cls,
        message
    ):

        cls._emit(
            HUDEvent.ERROR,
            {
                "message": message
            }
        )

    # * ========================================================
    # * Status
    # * ========================================================

    @classmethod
    def enabled(cls):

        return HUD_ENABLED
