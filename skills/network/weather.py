"""
JARVIS PRO
Weather Skill

Provides current weather information.

Uses Open-Meteo for weather data and geocoding.
No API key required.
"""

import asyncio
import requests
from core.diagnostics import debug_print

from core.registry import register
from voice.manager import speak
from services.location import location_service

# * =========================================================
# * Configuration
# * =========================================================

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

REQUEST_TIMEOUT = 5

NOMINATIM_HEADERS = {
    "User-Agent": "JARVIS-PRO/1.0"
}


# * =========================================================
# * Weather Code Descriptions
# * =========================================================

WEATHER_CODES = {
    0: "clear skies",
    1: "mainly clear skies",
    2: "partly cloudy skies",
    3: "overcast skies",

    45: "foggy conditions",
    48: "foggy conditions",

    51: "light drizzle",
    53: "moderate drizzle",
    55: "heavy drizzle",

    56: "light freezing drizzle",
    57: "heavy freezing drizzle",

    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",

    66: "light freezing rain",
    67: "heavy freezing rain",

    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",

    77: "snow grains",

    80: "light rain showers",
    81: "moderate rain showers",
    82: "heavy rain showers",

    85: "light snow showers",
    86: "heavy snow showers",

    95: "a thunderstorm",
    96: "a thunderstorm with hail",
    99: "a thunderstorm with heavy hail",
}

# * =========================================================
# * Location Name Normalization
# * =========================================================

LOCATION_ALIASES = {
    "banglore": "Bangalore",
    "bangalore": "Bangalore",
    "bengaluru": "Bengaluru",

    "mysore": "Mysore",
    "mysuru": "Mysuru",   
    
}


def _normalize_location_name(location):
    """
    Normalize common speech-recognition location variants.

    This is intentionally kept small so JARVIS does not
    depend on a large hardcoded city dictionary.
    """

    normalized = str(location).strip()

    if not normalized:
        return normalized

    alias = LOCATION_ALIASES.get(
        normalized.lower()
    )

    if alias:
        return alias

    return normalized

# * =========================================================
# * Nominatim Result Selection
# * =========================================================

PREFERRED_PLACE_TYPES = {
    "city",
    "town",
    "village",
    "hamlet",
    "municipality",
    "administrative",
}


def _select_nominatim_result(results, requested_location):
    """
    Select the most appropriate Nominatim result.

    Prefer geographic places, but also accept a POI when
    its address explicitly identifies the requested location
    as a village/town/city.
    """

    if not results:
        return None

    requested = str(
        requested_location
    ).strip().lower()

    geographic_types = {
        "city",
        "town",
        "village",
        "hamlet",
        "municipality",
        "administrative",
    }

    # * -----------------------------------------------------
    # * 1. Exact geographic result
    # * -----------------------------------------------------

    for result in results:

        name = str(
            result.get("name", "")
        ).strip().lower()

        addresstype = str(
            result.get("addresstype", "")
        ).strip().lower()

        result_type = str(
            result.get("type", "")
        ).strip().lower()

        if name == requested:

            if (
                addresstype in geographic_types
                or result_type in geographic_types
            ):
                return result

    # * -----------------------------------------------------
    # * 2. Geographic result whose name matches the request
    # * -----------------------------------------------------

    for result in results:

        name = str(
            result.get("name", "")
        ).strip().lower()

        addresstype = str(
            result.get("addresstype", "")
        ).strip().lower()

        result_type = str(
            result.get("type", "")
        ).strip().lower()

        if (
            addresstype in geographic_types
            or result_type in geographic_types
        ):

            if (
                requested in name
                or name in requested
            ):
                return result

    # * -----------------------------------------------------
    # * 3. POI whose address identifies the requested
    # * geographic locality.
    # * -----------------------------------------------------

    for result in results:

        address = result.get(
            "address",
            {}
        )

        locality_candidates = [
            address.get("village"),
            address.get("town"),
            address.get("city"),
            address.get("municipality"),
            address.get("hamlet"),
        ]

        for locality in locality_candidates:

            if not locality:
                continue

            locality_lower = str(
                locality
            ).strip().lower()

            if (
                requested == locality_lower
                or requested in locality_lower
                or locality_lower in requested
            ):

                return result

    # * -----------------------------------------------------
    # * 4. Final fallback
    # * -----------------------------------------------------

    return results[0]

# * =========================================================
# * Nominatim Geocoding
# * =========================================================

def _query_nominatim(query):
    """
    Query Nominatim and return search results.
    """

    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": query,
            "format": "jsonv2",
            "limit": 5,
            "countrycodes": "in",
            "addressdetails": 1,
        },
        headers=NOMINATIM_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()

def _has_geographic_result(results):
    """
    Check whether Nominatim returned an actual geographic
    place rather than only points of interest.
    """

    geographic_types = {
        "city",
        "town",
        "village",
        "hamlet",
        "municipality",
        "administrative",
    }

    for result in results:

        addresstype = str(
            result.get("addresstype", "")
        ).lower()

        result_type = str(
            result.get("type", "")
        ).lower()

        if (
            addresstype in PREFERRED_PLACE_TYPES
            or result_type in geographic_types
        ):
            return True

    return False

# * =========================================================
# * Resolve Location
# * =========================================================

def _resolve_location(location=None):
    """
    Resolve a location name into latitude/longitude.

    Resolution priority:

        1. Open-Meteo
        2. Nominatim / OpenStreetMap

    Examples:
        Bangalore
        Mysore
        London
        New York
    """

    if not location:
        return _detect_current_location()

    location = str(location).strip()

    if not location:
        return _detect_current_location()

    # * -----------------------------------------------------
    # * Normalize common speech-recognition variants
    # * -----------------------------------------------------

    original_location = location

    location = _normalize_location_name(
        location
    )

    if location != original_location:

        print(
            "[WEATHER LOCATION] "
            f"Normalized '{original_location}' "
            f"to '{location}'."
        )

    # * -----------------------------------------------------
    # * Primary geocoder: Open-Meteo
    # * -----------------------------------------------------

    try:

        response = requests.get(
            GEOCODING_URL,
            params={
                "name": location,
                "count": 5,
                "language": "en",
                "format": "json",
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if results:

            # * -----------------------------------------------------
            # * Prefer India results.
            #
            # * Open-Meteo can return a similarly named place in
            # * another country. For JARVIS's current location
            # * context, reject those results.
            # * -----------------------------------------------------

            india_results = [
                candidate
                for candidate in results
                if str(
                    candidate.get(
                        "country_code",
                        ""
                    )
                ).lower() == "in"
            ]

            if india_results:

                results = india_results

            else:

                print(
                    "[WEATHER GEOCODING] "
                    "Open-Meteo returned no Indian result. "
                    "Trying Nominatim."
                )

                results = []

            if results:

                result = results[0]

                requested_lower = location.lower()

                # * -------------------------------------------------
                # * Prefer exact name match.
                # * -------------------------------------------------

                for candidate in results:

                    candidate_name = str(
                        candidate.get("name", "")
                    ).strip().lower()

                    if candidate_name == requested_lower:

                        result = candidate
                        break

                print(
                    "[WEATHER GEOCODING] "
                    "Resolved using Open-Meteo."
                )

                return {
                    "name": result.get(
                        "name",
                        location,
                    ),
                    "country": result.get(
                        "country",
                        "",
                    ),
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                }

        print(
            "[WEATHER GEOCODING] "
            "Open-Meteo returned no suitable result. "
            "Trying Nominatim."
        )

    except Exception as e:

        print(
            f"[WEATHER GEOCODING ERROR] {e}"
        )

        print(
            "[WEATHER GEOCODING] "
            "Trying Nominatim fallback."
        )

    # * -----------------------------------------------------
    # * Secondary geocoder: Nominatim
    # * -----------------------------------------------------

    try:

        # * -------------------------------------------------
        # * First Nominatim query
        # * -------------------------------------------------

        nominatim_queries = [
            location,
        ]

        results = _query_nominatim(
            location
        )

        # * -------------------------------------------------
        # * If only POIs were returned, try more geographic
        # * search forms.
        # * -------------------------------------------------

        if not _has_geographic_result(results):

            geographic_queries = [
                f"{location}, Karnataka, India",
                f"{location} village, Karnataka, India",
            ]
            
            for query in geographic_queries:

                print(
                    "[WEATHER GEOCODING] "
                    f"Trying Nominatim query: {query}"
                )

                candidate_results = _query_nominatim(
                    query
                )

                if _has_geographic_result(
                    candidate_results
                ):

                    results = candidate_results
                    break

        # * -------------------------------------------------
        # * Select the best geographic result.
        # * -------------------------------------------------

        result = _select_nominatim_result(
            results,
            location,
        )

        if result is None:

            print(
                "[WEATHER GEOCODING] "
                "Nominatim returned no suitable result."
            )

            return None

        address = result.get(
            "address",
            {}
        )

        print(
            "[WEATHER GEOCODING] "
            "Resolved using Nominatim: "
            f"{result.get('display_name', location)}"
        )

        # * -------------------------------------------------
        # * Best human-readable location name
        # * -------------------------------------------------

        name = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or result.get("name")
            or location
        )

        country = address.get(
            "country",
            ""
        )

        return {
            "name": name,
            "country": country,
            "latitude": float(
                result["lat"]
            ),
            "longitude": float(
                result["lon"]
            ),
        }

    except Exception as e:

        print(
            f"[WEATHER NOMINATIM ERROR] {e}"
        )

        return None


# * =========================================================
# * Detect Current Location
# * =========================================================

def _detect_current_location():
    """
    Determine the current location.

    Priority:
        1. Windows device location
        2. IP geolocation fallback

    Windows location provides latitude/longitude and
    accuracy information. IP geolocation is retained
    as a fallback when Windows location is unavailable.
    """

    # * -----------------------------------------------------
    # * Primary: Windows Location
    # * -----------------------------------------------------

    try:
        location = asyncio.run(
            location_service.get_location()
        )

        if location:
            latitude = location.get("latitude")
            longitude = location.get("longitude")

            if latitude is not None and longitude is not None:

                debug_print(
                    "[WEATHER LOCATION] "
                    f"Windows location: "
                    f"{latitude}, {longitude} | "
                    f"Accuracy: "
                    f"{location.get('accuracy')} m | "
                    f"Source: "
                    f"{location.get('source')}"
                )

                return {
                    "name": "your current location",
                    "country": "",
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                }

    except Exception as e:

        print(
            f"[WEATHER WINDOWS LOCATION ERROR] {e}"
        )

    return _detect_ip_location()


def _detect_ip_location():
    """Resolve location through the existing one-request-per-provider fallback."""

    try:
        response = requests.get(
            "https://ipapi.co/json/",
            timeout=REQUEST_TIMEOUT,
        )
        if getattr(response, "status_code", None) == 429:
            debug_print("[WEATHER LOCATION] ipapi.co rate limited; using ipwho.is fallback.")
        response.raise_for_status()
        data = response.json()
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is not None and longitude is not None:
            debug_print("[WEATHER LOCATION] Using IP geolocation fallback.")
            return {
                "name": data.get("city", "your location"),
                "country": data.get("country_name", ""),
                "latitude": float(latitude),
                "longitude": float(longitude),
            }
    except Exception as error:
        print(f"[WEATHER PRIMARY LOCATION ERROR] {error}")

    try:
        response = requests.get(
            "https://ipwho.is/",
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("success") is False:
            raise RuntimeError(data.get("message", "Location lookup failed"))
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is None or longitude is None:
            raise RuntimeError("Location coordinates were not returned.")
        debug_print("[WEATHER LOCATION] Using ipwho.is fallback.")
        return {
            "name": data.get("city", "your location"),
            "country": data.get("country", ""),
            "latitude": float(latitude),
            "longitude": float(longitude),
        }
    except Exception as error:
        print(f"[WEATHER FALLBACK LOCATION ERROR] {error}")

    return None


async def _detect_current_location_async():
    """Resolve current location without creating a nested event loop."""

    try:
        location = await location_service.get_location()
        if location:
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            if latitude is not None and longitude is not None:
                debug_print(
                    "[WEATHER LOCATION] Windows location: "
                    f"{latitude}, {longitude} | Accuracy: "
                    f"{location.get('accuracy')} m | Source: "
                    f"{location.get('source')}"
                )
                return {
                    "name": "your current location",
                    "country": "",
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                }
    except Exception as error:
        print(f"[WEATHER WINDOWS LOCATION ERROR] {error}")

    # requests is intentionally kept off the Live event loop.
    return await asyncio.to_thread(_detect_ip_location)


async def _resolve_location_async(location=None):
    if location is None or not str(location).strip():
        return await _detect_current_location_async()
    return await asyncio.to_thread(_resolve_location, location)

# * =========================================================
# * Get Weather
# * =========================================================

def _get_weather(latitude, longitude):
    """
    Fetch current weather from Open-Meteo.
    """

    debug_print("[WEATHER] Fetching current weather...")

    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,

            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),

            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",

            "timezone": "auto",
        },

        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()
    current = data.get("current")
    if not isinstance(current, dict):
        raise ValueError("Open-Meteo response did not contain current weather data")

    debug_print("[WEATHER] Current weather ready")
    return data


def get_current_weather(location=None):
    """Return current weather through the existing provider without TTS."""
    resolved = _resolve_location(location)
    if resolved is None:
        return None
    weather_data = _get_weather(resolved["latitude"], resolved["longitude"])
    current = weather_data.get("current", {})
    code = current.get("weather_code")
    temperature = current.get("temperature_2m")
    if temperature is None and code is None:
        return None
    return {
        "location": resolved.get("name"),
        "temperature": temperature,
        "condition": WEATHER_CODES.get(code),
        "weather_code": code,
    }


async def get_current_weather_async(location=None):
    """Return weather from an existing asyncio event loop."""
    resolved = await _resolve_location_async(location)
    if resolved is None:
        return None
    weather_data = await asyncio.to_thread(
        _get_weather,
        resolved["latitude"],
        resolved["longitude"],
    )
    current = weather_data.get("current", {})
    code = current.get("weather_code")
    temperature = current.get("temperature_2m")
    if temperature is None and code is None:
        return None
    return {
        "location": resolved.get("name"),
        "temperature": temperature,
        "condition": WEATHER_CODES.get(code),
        "weather_code": code,
    }


# * =========================================================
# * Natural Weather Response
# * =========================================================

def _build_message(location, weather):
    """
    Build a natural JARVIS response.
    """

    current = weather.get("current", {})

    temperature = current.get(
        "temperature_2m"
    )

    feels_like = current.get(
        "apparent_temperature"
    )

    humidity = current.get(
        "relative_humidity_2m"
    )

    precipitation = current.get(
        "precipitation"
    )

    wind = current.get(
        "wind_speed_10m"
    )

    weather_code = current.get(
        "weather_code"
    )

    condition = WEATHER_CODES.get(
        weather_code,
        "unknown conditions",
    )

    city = location.get(
        "name",
        "your location",
    )

    parts = []

    # * -----------------------------------------------------
    # * Temperature
    # * -----------------------------------------------------

    if temperature is not None:

        parts.append(
            f"It's {round(temperature)} degrees"
        )

    # * -----------------------------------------------------
    # * Condition
    # * -----------------------------------------------------

    if condition:

        parts.append(
            f"with {condition}"
        )

    message = (
        f"Currently in {city}, "
        + " ".join(parts)
        + "."
    )

    # * -----------------------------------------------------
    # * Feels Like
    # * -----------------------------------------------------

    if feels_like is not None:

        message += (
            f" It feels like "
            f"{round(feels_like)} degrees."
        )

    # * -----------------------------------------------------
    # * Humidity
    # * -----------------------------------------------------

    if humidity is not None:

        message += (
            f" Humidity is "
            f"{round(humidity)} percent."
        )

    # * -----------------------------------------------------
    # * Wind
    # * -----------------------------------------------------

    if wind is not None:

        message += (
            f" Wind speed is "
            f"{round(wind)} kilometers per hour."
        )

    # * -----------------------------------------------------
    # * Rain
    # * -----------------------------------------------------

    if precipitation is not None:

        if precipitation > 0:

            message += (
                f" There is "
                f"{precipitation} millimeters "
                "of precipitation."
            )

    return message


# * =========================================================
# * Weather Action
# * =========================================================

def _weather_sync(data=None):
    """
    Report current weather.

    Supported data examples:

        {}

        {
            "location": "Bangalore"
        }

        {
            "city": "Mysore"
        }
    """

    if data is None:
        data = {}

    try:

        # * -------------------------------------------------
        # * Location
        # * -------------------------------------------------

        location = (
            data.get("location")
            or data.get("city")
            or data.get("place")
        )

        print(
            f"[WEATHER] Requested location: "
            f"{location or 'current location'}"
        )

        # * -------------------------------------------------
        # * Resolve location
        # * -------------------------------------------------

        resolved = _resolve_location(
            location
        )

        if resolved is None:

            speak(
                "I couldn't determine the location "
                "for the weather."
            )

            return False

        # * -------------------------------------------------
        # * Get weather
        # * -------------------------------------------------

        weather_data = _get_weather(
            resolved["latitude"],
            resolved["longitude"],
        )

        # * -------------------------------------------------
        # * Natural response
        # * -------------------------------------------------

        message = _build_message(
            resolved,
            weather_data,
        )

        speak(message)

        # * -------------------------------------------------
        # ! Debug
        # * -------------------------------------------------

        current = weather_data.get(
            "current",
            {},
        )

        print(
            f"[WEATHER] "
            f"{resolved['name']} | "
            f"{current.get('temperature_2m')}°C | "
            f"Code: {current.get('weather_code')} | "
            f"Humidity: "
            f"{current.get('relative_humidity_2m')}%"
        )

        return True

    except requests.RequestException as e:

        print(
            f"[WEATHER NETWORK ERROR] {e}"
        )

        speak(
            "I couldn't reach the weather service "
            "right now."
        )

        return False

    except Exception as e:

        print(
            f"[WEATHER ERROR] {e}"
        )

        speak(
            "I couldn't check the weather right now."
        )

        return False


async def _weather_async(data=None):
    """Execute the weather skill without nesting asyncio.run()."""
    if data is None:
        data = {}

    try:
        location_name = (
            data.get("location")
            or data.get("city")
            or data.get("place")
        )
        print(
            f"[WEATHER] Requested location: "
            f"{location_name or 'current location'}"
        )

        resolved = await _resolve_location_async(location_name)
        if resolved is None:
            speak("I couldn't determine the location for the weather.")
            return False

        weather_data = await asyncio.to_thread(
            _get_weather,
            resolved["latitude"],
            resolved["longitude"],
        )
        speak(_build_message(resolved, weather_data))

        current = weather_data.get("current", {})
        print(
            f"[WEATHER] {resolved['name']} | "
            f"{current.get('temperature_2m')}°C | "
            f"Code: {current.get('weather_code')} | Humidity: "
            f"{current.get('relative_humidity_2m')}%"
        )
        return True
    except requests.RequestException as error:
        print(f"[WEATHER NETWORK ERROR] {error}")
        speak("I couldn't reach the weather service right now.")
        return False
    except Exception as error:
        print(f"[WEATHER ERROR] {error}")
        speak("I couldn't check the weather right now.")
        return False


def weather(data=None):
    """Run synchronously, or schedule the async path for Gemini Live."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _weather_sync(data)

    from core.live_execution import is_live_execution, schedule_live_task

    if is_live_execution():
        pending = _weather_async(data)
        if schedule_live_task(pending):
            return {
                "status": "pending_weather",
                "message": "Weather lookup scheduled through Gemini Live.",
            }
        return False

    print("[WEATHER ERROR] Async caller must use get_current_weather_async().")
    return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "weather",
    weather,
)
