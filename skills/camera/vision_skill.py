"""
JARVIS PRO
One-Shot Vision Skill

Vision automatically starts when a vision command is requested.

Flow:

    Vision command
        ↓
    Start Vision
        ↓
    Wait for scene
        ↓
    Perform requested operation
        ↓
    Stop Vision
        ↓
    Camera released

Vision is NOT persistent.

Camera skill itself is not modified.
"""

from core.registry import register
from core.diagnostics import debug_print

from skills.camera.vision_loop import vision_loop
from skills.camera.vision_query import vision_query
from skills.camera.face_registration import face_registration
from skills.camera.face_registry import face_registry, sanitize_name
from skills.camera.face_speech import people_message


# * =========================================================
# * Vision Session Helpers
# * =========================================================

def _start_vision():
    """
    Start Vision for the current request.
    """

    if vision_loop.running:

        print(
            "[VISION] Already running."
        )

        return True

    print(
        "[VISION] Starting one-shot vision..."
    )

    return vision_loop.start()


def _stop_vision():
    """
    Stop Vision after the current request.
    """

    if not vision_loop.running:

        return True

    print(
        "[VISION] Stopping one-shot vision..."
    )

    return vision_loop.stop()


# * =========================================================
# * Vision Start
#
# * Compatibility command.
#
# * We keep this registered, but normal vision requests
# * no longer need it.
# * =========================================================

def vision_start(data=None):

    return _start_vision()


# * =========================================================
# * Vision Stop
#
# * Manual emergency/compatibility command.
# * =========================================================

def vision_stop(data=None):

    return _stop_vision()


# * =========================================================
# * Describe Scene
# * =========================================================

def vision_describe(data=None):

    started = False

    try:

        # * ---------------------------------------------
        # * Start Vision
        # * ---------------------------------------------

        if not vision_loop.running:

            if not _start_vision():

                return {
                    "error": "Unable to start vision."
                }

            started = True

        # * ---------------------------------------------
        # * Query scene
        # * ---------------------------------------------

        print(
            "[VISION] Describing scene..."
        )

        description = vision_query.describe()
        scene = vision_query.get_scene()
        if people_message((scene or {}).get("objects", [])):
            # * The processing loop already emitted the state-aware person
            # * announcement through the existing voice/HUD path.
            return None
        return description

    except Exception as e:

        print(
            "[VISION ERROR] Describe:",
            e
        )

        return {
            "error": str(e)
        }

    finally:

        # * ---------------------------------------------
        # * Always shut Vision down after this request.
        # * ---------------------------------------------

        if started:

            _stop_vision()


# * =========================================================
# * Count Object
# * =========================================================

def vision_count(data=None):

    started = False

    try:

        # * ---------------------------------------------
        # * Start Vision
        # * ---------------------------------------------

        if not vision_loop.running:

            if not _start_vision():

                return {
                    "error": "Unable to start vision."
                }

            started = True

        # * ---------------------------------------------
        # * Validate input
        # * ---------------------------------------------

        if not isinstance(data, dict):

            data = {}

        object_name = data.get("object")

        if not object_name:

            return {
                "error": "Object name is required."
            }

        # * ---------------------------------------------
        # * Count
        # * ---------------------------------------------

        print(
            f"[VISION] Counting: {object_name}"
        )

        return vision_query.count(
            object_name
        )

    except Exception as e:

        print(
            "[VISION ERROR] Count:",
            e
        )

        return {
            "error": str(e)
        }

    finally:

        if started:

            _stop_vision()


# * =========================================================
# * Check Object
# * =========================================================

def vision_check(data=None):

    started = False

    try:

        # * ---------------------------------------------
        # * Start Vision
        # * ---------------------------------------------

        if not vision_loop.running:

            if not _start_vision():

                return {
                    "error": "Unable to start vision."
                }

            started = True

        # * ---------------------------------------------
        # * Validate input
        # * ---------------------------------------------

        if not isinstance(data, dict):

            data = {}

        object_name = data.get("object")

        if not object_name:

            return {
                "error": "Object name is required."
            }

        # * ---------------------------------------------
        # * Check object
        # * ---------------------------------------------

        print(
            f"[VISION] Checking: {object_name}"
        )

        return vision_query.has_object(
            object_name
        )

    except Exception as e:

        print(
            "[VISION ERROR] Check:",
            e
        )

        return {
            "error": str(e)
        }

    finally:

        if started:

            _stop_vision()


# * =========================================================
# * Objects At Position
# * =========================================================

def vision_position(data=None):

    started = False

    try:

        # * ---------------------------------------------
        # * Start Vision
        # * ---------------------------------------------

        if not vision_loop.running:

            if not _start_vision():

                return {
                    "error": "Unable to start vision."
                }

            started = True

        # * ---------------------------------------------
        # * Validate input
        # * ---------------------------------------------

        if not isinstance(data, dict):

            data = {}

        position = data.get("position")

        if not position:

            return {
                "error": "Position is required."
            }

        # * ---------------------------------------------
        # * Query position
        # * ---------------------------------------------

        print(
            f"[VISION] Checking position: {position}"
        )

        return vision_query.objects_at(
            position
        )

    except Exception as e:

        print(
            "[VISION ERROR] Position:",
            e
        )

        return {
            "error": str(e)
        }

    finally:

        if started:

            _stop_vision()


def vision_locate(data=None):
    started = False

    try:
        if not vision_loop.running:
            if not _start_vision():
                return {
                    "error": "Unable to start vision."
                }

            started = True

        if not isinstance(data, dict):
            data = {}

        object_name = data.get("object")

        if not object_name:
            return {
                "error": "Object name is required."
            }

        print(
            f"[VISION] Locating: {object_name}"
        )

        return vision_query.locate(
            object_name
        )

    except Exception as e:

        print(
            "[VISION ERROR] Locate:",
            e
        )

        return {
            "error": str(e)
        }

    finally:

        if started:
            _stop_vision()
            

def vision_target(data=None):
    started = False

    try:
        if not vision_loop.running:
            if not _start_vision():
                return {
                    "error": "Unable to start vision."
                }

            started = True

        if not isinstance(data, dict):
            data = {}

        object_name = data.get("object")

        if not object_name:
            return {
                "error": "Object name is required."
            }

        position = data.get("position")
        region = data.get("region")

        print(
            f"[VISION] Selecting target: "
            f"{object_name}"
        )

        return vision_query.target_info(
            object_name,
            position=position,
            region=region,
        )

    except Exception as e:

        print(
            "[VISION ERROR] Target:",
            e
        )

        return {
            "error": str(e)
        }

    finally:

        if started:
            _stop_vision()


# * =========================================================
# * Local Face Registration
# * =========================================================

def register_face(data=None):
    name = data.get("name") if isinstance(data, dict) else None

    try:
        if not face_registration.start(name=name):
            from voice.manager import speak
            speak("Face registration is already in progress.")
        return True
    except ValueError as exc:
        from voice.manager import speak
        speak(str(exc))
        return True
    except Exception as exc:
        print("[VISION REGISTRATION ERROR]", exc)
        from voice.manager import speak
        speak("Face registration wasn't completed.")
        return True


def cancel_face_registration(data=None):
    if not face_registration.cancel():
        from voice.manager import speak
        speak("There is no active face registration.")
    return True


def delete_face(data=None):
    data = data if isinstance(data, dict) else {}

    try:
        if data.get("all"):
            deleted = face_registry.delete_all()
            from voice.manager import speak
            speak(
                "All registered faces were deleted."
                if deleted
                else "There were no registered faces to delete."
            )
            return True

        name = data.get("name")
        if not name:
            from voice.manager import speak
            speak("Please specify a registered name, or say delete all faces.")
            return True

        safe_name = sanitize_name(name)
        deleted = face_registry.delete_identity(safe_name)
        from voice.manager import speak
        speak(
            f"Face registration for {safe_name} was deleted."
            if deleted
            else f"I couldn't find a registered face for {safe_name}."
        )
        return True
    except ValueError as exc:
        from voice.manager import speak
        speak(str(exc))
        return True
    except Exception as exc:
        print("[VISION FACE DELETE ERROR]", exc)
        from voice.manager import speak
        speak("I couldn't delete that face registration.")
        return True

# * =========================================================
# * Registry
# * =========================================================

register(
    "vision_start",
    vision_start,
    category="camera",
)

register(
    "vision_stop",
    vision_stop,
    category="camera",
)

register(
    "vision_describe",
    vision_describe,
    category="camera",
)

register(
    "vision_count",
    vision_count,
    category="camera",
)

register(
    "vision_check",
    vision_check,
    category="camera",
)

register(
    "vision_position",
    vision_position,
    category="camera",
)

register(
    "vision_locate",
    vision_locate,
    category="camera",
)

register(
    "vision_target",
    vision_target,
    category="camera",
)

register(
    "register_face",
    register_face,
    category="camera",
)

register(
    "cancel_face_registration",
    cancel_face_registration,
    category="camera",
)

register(
    "delete_face",
    delete_face,
    category="camera",
)


debug_print(
    "[VISION SKILL] Registered."
)
