"""
=============================================================
JARVIS PRO — GOOGLE MAPS SKILL
=============================================================

Provides Google Maps opening and destination navigation.

Maps uses Google's universal Maps URLs, so no API key
is required for this skill.
"""

from urllib.parse import quote_plus
import webbrowser

from core.registry import register
from voice.manager import speak


GOOGLE_MAPS_URL = "https://www.google.com/maps"


# * =============================================================
# * OPEN GOOGLE MAPS
# * =============================================================

def maps_open(data=None):
    try:
        url = (
            "https://www.google.com/maps/"
            "?api=1"
        )

        opened = webbrowser.open_new_tab(url)

        if opened:
            speak("Opening Google Maps.")
            return True

        speak("I could not open Google Maps.")
        return False

    except Exception as error:
        print(f"[MAPS ERROR] {error}")
        speak("I could not open Google Maps.")
        return False


# * =============================================================
# * NAVIGATE TO DESTINATION
# * =============================================================

def maps_directions(data=None):
    data = data or {}

    origin = str(
        data.get("origin", "")
    ).strip()

    destination = str(
        data.get("destination", "")
    ).strip()

    if not destination:
        speak("Please tell me the destination.")
        return False

    encoded_destination = quote_plus(
        destination
    )

    # * ---------------------------------------------------------
    # * Origin + Destination
    # * ---------------------------------------------------------

    if origin:

        encoded_origin = quote_plus(
            origin
        )

        url = (
            "https://www.google.com/maps/dir/"
            "?api=1"
            f"&origin={encoded_origin}"
            f"&destination={encoded_destination}"
            "&travelmode=driving"
            "&dir_action=navigate"
        )

        success_message = (
            f"Opening directions from "
            f"{origin} to {destination}."
        )

    # * ---------------------------------------------------------
    # * Destination Only
    # * ---------------------------------------------------------

    else:

        # * Google Maps will use the device's current location
        # * when location is available.

        url = (
            "https://www.google.com/maps/dir/"
            "?api=1"
            f"&destination={encoded_destination}"
            "&travelmode=driving"
            "&dir_action=navigate"
        )

        success_message = (
            f"Opening directions to {destination}."
        )

    # * ---------------------------------------------------------
    # * OPEN MAPS
    # * ---------------------------------------------------------

    try:
        opened = webbrowser.open_new_tab(url)

        if opened:
            speak(success_message)
            return True

        speak(
            "I could not open Google Maps directions."
        )
        return False

    except Exception as error:
        print(
            f"[MAPS DIRECTIONS ERROR] {error}"
        )

        speak(
            "I could not open Google Maps directions."
        )

        return False


# * =============================================================
# * REGISTRATION
# * =============================================================

register(
    "maps_open",
    maps_open,
)

register(
    "maps_directions",
    maps_directions,
)