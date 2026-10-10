"""
JARVIS PRO
Volume Skill

Provides Windows system volume control.

Supports:
- Get current volume
- Set volume
- Increase volume
- Decrease volume
- Mute
- Unmute
"""

from ctypes import POINTER, cast

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from voice.manager import speak
from core.registry import register


# * =========================================================
# * Audio Device
# * =========================================================

_volume = None


def _get_volume_interface():
    """
    Get the Windows master-volume interface.

    Uses the EndpointVolume interface exposed by the
    current Pycaw AudioDevice wrapper.
    """

    global _volume

    if _volume is not None:
        return _volume

    device = AudioUtilities.GetSpeakers()

    if hasattr(device, "EndpointVolume"):
        _volume = device.EndpointVolume
        return _volume

    raise RuntimeError(
        "Pycaw AudioDevice does not expose EndpointVolume."
    )


# * =========================================================
# * Current Volume
# * =========================================================

def current():
    """
    Return current master volume as an integer percentage.
    """

    volume = _get_volume_interface()

    return int(
        round(
            volume.GetMasterVolumeLevelScalar() * 100
        )
    )


# * =========================================================
# * Set Volume
# * =========================================================

def set_volume(percent):
    """
    Set master volume between 0 and 100.
    """

    percent = max(
        0,
        min(
            100,
            int(percent),
        ),
    )

    volume = _get_volume_interface()

    volume.SetMasterVolumeLevelScalar(
        percent / 100,
        None,
    )

    return percent


# * =========================================================
# * Mute Status
# * =========================================================

def is_muted():
    """
    Return True if system audio is muted.
    """

    volume = _get_volume_interface()

    return bool(
        volume.GetMute()
    )


# * =========================================================
# * Volume Action
# * =========================================================

def volume_action(data=None):
    """
    Execute a volume command.

    Supported data:

        {"percent": 50}
        {"direction": "up"}
        {"direction": "down"}
        {"direction": "mute"}
        {"direction": "unmute"}
        {"direction": "status"}
    """

    if data is None:
        data = {}

    try:

        direction = str(
            data.get(
                "direction",
                "",
            )
        ).strip().lower()

        percent = data.get("percent")

        # * =================================================
        # * Exact Volume
        # * =================================================

        if percent is not None:

            try:
                percent = int(percent)
            except (TypeError, ValueError):

                speak(
                    "Please give me a valid volume percentage."
                )

                return False

            percent = set_volume(percent)

            # * Setting volume also naturally unmutes it.
            volume = _get_volume_interface()

            volume.SetMute(
                0,
                None,
            )

            speak(
                f"Volume set to {percent} percent."
            )

            return True

        # * =================================================
        # * Increase
        # * =================================================

        if direction in {
            "up",
            "increase",
            "higher",
            "louder",
        }:

            new_volume = min(
                100,
                current() + 10,
            )

            set_volume(new_volume)

            volume = _get_volume_interface()

            volume.SetMute(
                0,
                None,
            )

            speak(
                f"Volume is now {new_volume} percent."
            )

            return True

        # * =================================================
        # * Decrease
        # * =================================================

        if direction in {
            "down",
            "decrease",
            "lower",
            "quieter",
            "softer",
        }:

            new_volume = max(
                0,
                current() - 10,
            )

            set_volume(new_volume)

            speak(
                f"Volume is now {new_volume} percent."
            )

            return True

        # * =================================================
        # * Mute
        # * =================================================

        if direction in {
            "mute",
            "silent",
        }:

            volume = _get_volume_interface()

            volume.SetMute(
                1,
                None,
            )

            speak(
                "Muted."
            )

            return True

        # * =================================================
        # * Unmute
        # * =================================================

        if direction in {
            "unmute",
            "sound",
        }:

            volume = _get_volume_interface()

            volume.SetMute(
                0,
                None,
            )

            speak(
                f"Unmuted. Volume is {current()} percent."
            )

            return True

        # * =================================================
        # * Status
        # * =================================================

        if direction in {
            "status",
            "current",
            "check",
        }:

            percent = current()

            if is_muted():

                speak(
                    f"Your volume is {percent} percent, "
                    "and the system is muted."
                )

            else:

                speak(
                    f"Your volume is {percent} percent."
                )

            return True

        return False

    except Exception as e:

        print(
            f"[VOLUME ERROR] {e}"
        )

        speak(
            "I couldn't control the system volume."
        )

        return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "volume",
    volume_action,
)