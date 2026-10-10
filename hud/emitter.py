"""
JARVIS PRO
HUD Event Emitter

One-way communication:

JARVIS
   ↓
HUDEmitter
   ↓
HUDAdapter
   ↓
HUDManager
   ↓
HUD UI

The HUD never sends commands back to JARVIS.
"""

from .adapter import HUDAdapter
from .event_contract import HUDEvent


class HUDEmitter:

    @staticmethod
    def emit(event, data=None):

        data = data or {}

        # * =========================================
        # * Voice
        # * =========================================

        if event == HUDEvent.LISTENING:

            HUDAdapter.listening()
            return

        if event == HUDEvent.SPEAKING:

            HUDAdapter.speaking()
            return

        if event == HUDEvent.IDLE:

            HUDAdapter.idle()
            return

        # * =========================================
        # AI
        # * =========================================

        if event == HUDEvent.THINKING:

            HUDAdapter.thinking()
            return

        if event == HUDEvent.AI_MODEL_CHANGED:

            HUDAdapter.ai_model(
                data.get("provider", ""),
                data.get("model", "")
            )
            return

        # * =========================================
        # * CONVERSATION
        # * =========================================

        if event == HUDEvent.COMMAND:

            HUDAdapter.command(
                data.get("text", ""),
                data.get("source", "jarvis"),
            )
            return

        if event == HUDEvent.RESPONSE:

            HUDAdapter.response(
                data.get("text", ""),
                data.get("speaker", "jarvis")
            )
            return

        # * =========================================
        # * Tasks
        # * =========================================

        if event == HUDEvent.TASK_STARTED:

            HUDAdapter.task_started(
                data.get("task", "")
            )
            return

        if event == HUDEvent.EXECUTING:

            HUDAdapter.executing(
                data.get("task", "")
            )
            return

        if event == HUDEvent.TASK_FINISHED:

            HUDAdapter.task_finished(
                data.get("task", "")
            )
            return

        if event == HUDEvent.TASK_FAILED:

            HUDAdapter.task_failed(
                data.get("task", ""),
                data.get("error", "")
            )
            return

        # * =========================================
        # * Voice Mode
        # * =========================================

        if event == HUDEvent.VOICE_MODE_CHANGED:

            HUDAdapter.voice_mode(
                data.get("mode", "")
            )
            return

        # * =========================================
        # * System
        # * =========================================

        if event == HUDEvent.SYSTEM_UPDATE:

            HUDAdapter.system_update(
                data
            )
            return
        
        if event == HUDEvent.SYSTEM_ACTIVITY:

            HUDAdapter.system_activity(
                data.get("message", ""),
                data.get("actions", []),
            )
            return

        if event == HUDEvent.PERSONAL_LINKS:

            HUDAdapter.personal_links(
                data.get("entries", [])
            )
            return

        # * =========================================
        # * Notifications
        # * =========================================

        if event == HUDEvent.NOTIFICATION:

            HUDAdapter.notify(
                data.get("title", "JARVIS"),
                data.get("message", ""),
                data.get("level", "INFO"),
                data.get("source", "jarvis"),
                data.get("metadata", {}),
            )
            return

        if event == HUDEvent.ERROR:

            HUDAdapter.error(
                data.get("message", "")
            )
            return

        # * =========================================
        # * Unknown
        # * =========================================

        print(
            f"[HUD EMITTER] Unknown event: {event}"
        )
