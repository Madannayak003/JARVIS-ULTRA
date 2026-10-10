"""
JARVIS PRO
HUD Adapter

Safe integration layer between JARVIS and the HUD.

IMPORTANT:

This adapter only reports information to the HUD.

It must NEVER:

- execute JARVIS commands
- control the AI
- control voice
- control Developer Mode
- control skills
- modify core runtime behavior
"""

from .manager import hud


class HUDAdapter:

    # * =====================================================
    # * Voice
    # * =====================================================

    @staticmethod
    def listening():

        hud.listening()

    @staticmethod
    def thinking():

        hud.thinking()

    @staticmethod
    def speaking():

        hud.speaking()

    @staticmethod
    def idle():

        hud.idle()

    # * =====================================================
    # * Conversation
    # * =====================================================

    @staticmethod
    def command(text, source="jarvis"):

        hud.command(
            text,
            source,
        )

    @staticmethod
    def response(text, speaker="jarvis"):

        hud.response(
            text,
            speaker
        )

    # * =====================================================
    # * Tasks
    # * =====================================================

    @staticmethod
    def task_started(task):

        hud.task_started(
            task
        )

    @staticmethod
    def executing(task=""):

        hud.executing(
            task
        )

    @staticmethod
    def task_finished(task=""):

        hud.task_finished(
            task
        )

    @staticmethod
    def task_failed(
        task="",
        error=""
    ):

        hud.task_failed(
            task,
            error
        )

    # * =====================================================
    # AI
    # * =====================================================

    @staticmethod
    def ai_model(
        provider,
        model
    ):

        hud.ai_model(
            provider,
            model
        )

    # * =====================================================
    # * Voice Mode
    # * =====================================================

    @staticmethod
    def voice_mode(mode):

        hud.voice_mode(
            mode
        )

    # * =====================================================
    # * System
    # * =====================================================

    @staticmethod
    def system_update(data):

        hud.system_update(
            data
        )
        
    # * =====================================================
    # * System Activity
    # * =====================================================

    @staticmethod
    def system_activity(message, actions=None):

        hud.system_activity(
            message,
            actions,
        )

    @staticmethod
    def personal_links(entries):

        hud.personal_links(entries)

    # * =====================================================
    # * Notifications
    # * =====================================================

    @staticmethod
    def notify(title_or_message, message=None, level="INFO", source="jarvis", metadata=None):

        hud.notify(
            title_or_message,
            message,
            level,
            source,
            metadata,
        )

    @staticmethod
    def error(message):

        hud.error(
            message
        )
