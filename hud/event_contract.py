"""
JARVIS PRO
HUD Event Contract

Defines the events that JARVIS is allowed to send to the HUD.

IMPORTANT:
This file contains NO JARVIS execution logic.
The HUD remains a passive display system.
"""


class HUDEvent:

    # * =====================================================
    # * Voice
    # * =====================================================

    LISTENING = "listening"

    SPEAKING = "speaking"

    # * =====================================================
    # AI
    # * =====================================================

    THINKING = "thinking"

    AI_MODEL_CHANGED = "ai_model_changed"

    # * =====================================================
    # * Conversation
    # * =====================================================

    COMMAND = "command"

    RESPONSE = "response"

    # * =====================================================
    # * Tasks
    # * =====================================================

    TASK_STARTED = "task_started"

    EXECUTING = "executing"

    TASK_FINISHED = "task_finished"

    TASK_FAILED = "task_failed"

    # * =====================================================
    # * Voice Mode
    # * =====================================================

    VOICE_MODE_CHANGED = "voice_mode_changed"

    # * =====================================================
    # * System
    # * =====================================================

    SYSTEM_UPDATE = "system_update"
    
    # * =====================================================
    # * System Activity
    # * =====================================================

    SYSTEM_ACTIVITY = "system_activity"

    # * Structured, configuration-backed personal website entries.
    PERSONAL_LINKS = "personal_links"

    # * =====================================================
    # * Notifications
    # * =====================================================

    NOTIFICATION = "notification"

    ERROR = "error"

    # * =====================================================
    # * General
    # * =====================================================

    IDLE = "idle"
