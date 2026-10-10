"""
JARVIS PRO
HUD Runtime Bridge

Connects JARVIS runtime information to the HUD.

IMPORTANT:
This module is one-way.

JARVIS → HUD

The HUD never controls JARVIS through this bridge.
"""

from hud import HUDAdapter


class HUDBridge:

    # * =====================================================
    # * Voice
    # * =====================================================

    @staticmethod
    def listening():

        try:
            HUDAdapter.listening()

        except Exception as e:

            print(
                "[HUD BRIDGE] Listening update failed:",
                e
            )

    @staticmethod
    def thinking():

        try:
            HUDAdapter.thinking()

        except Exception as e:

            print(
                "[HUD BRIDGE] Thinking update failed:",
                e
            )

    @staticmethod
    def speaking():

        try:
            HUDAdapter.speaking()

        except Exception as e:

            print(
                "[HUD BRIDGE] Speaking update failed:",
                e
            )

    @staticmethod
    def idle():

        try:
            HUDAdapter.idle()

        except Exception as e:

            print(
                "[HUD BRIDGE] Idle update failed:",
                e
            )

    # * =====================================================
    # * Tasks
    # * =====================================================

    @staticmethod
    def task_started(task):

        try:
            HUDAdapter.task_started(
                task
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] Task start failed:",
                e
            )

    @staticmethod
    def executing(task=""):

        try:
            HUDAdapter.executing(
                task
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] Task execution update failed:",
                e
            )

    @staticmethod
    def task_finished(task=""):

        try:
            HUDAdapter.task_finished(
                task
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] Task finish failed:",
                e
            )

    @staticmethod
    def task_failed(
        task="",
        error=""
    ):

        try:
            HUDAdapter.task_failed(
                task,
                error
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] Task failure update failed:",
                e
            )

    # * =====================================================
    # AI
    # * =====================================================

    @staticmethod
    def ai_model(
        provider,
        model
    ):

        try:
            HUDAdapter.ai_model(
                provider,
                model
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] AI model update failed:",
                e
            )

    # * =====================================================
    # * Voice Mode
    # * =====================================================

    @staticmethod
    def voice_mode(mode):

        try:
            HUDAdapter.voice_mode(
                mode
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] Voice mode update failed:",
                e
            )

    # * =====================================================
    # * System
    # * =====================================================

    @staticmethod
    def system_update(data):

        try:
            HUDAdapter.system_update(
                data
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] System update failed:",
                e
            )

    # * =====================================================
    # * Notifications
    # * =====================================================

    @staticmethod
    def notify(message):

        try:
            HUDAdapter.notify(
                message
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] Notification failed:",
                e
            )

    # * =====================================================
    # ! Error
    # * =====================================================

    @staticmethod
    def error(message):

        try:
            HUDAdapter.error(
                message
            )

        except Exception as e:

            print(
                "[HUD BRIDGE] Error update failed:",
                e
            )


# * Global bridge

hud_bridge = HUDBridge()
