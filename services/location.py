"""
=============================================================
JARVIS PRO — WINDOWS LOCATION SERVICE
=============================================================

Provides the device's current geographic location using
Windows Runtime Geolocation.

Windows location is preferred when available.

This service does NOT control Google Maps.
Google Maps continues to use its own device/browser location.

Returns:
    latitude
    longitude
    accuracy
    source
"""

from winrt.windows.devices.geolocation import (
    Geolocator,
    PositionAccuracy,
)


class LocationService:

    def __init__(self):
        self._locator = None

    def _get_locator(self):
        """
        Create the Windows Geolocator lazily.
        """

        if self._locator is not None:
            return self._locator

        locator = Geolocator()

        locator.desired_accuracy = PositionAccuracy.HIGH
        locator.desired_accuracy_in_meters = 100

        self._locator = locator

        return locator

    async def get_location(self):
        """
        Get the current Windows location.

        Returns a dictionary containing:
            latitude
            longitude
            accuracy
            source

        Returns None if Windows location cannot be obtained.
        """

        try:
            locator = self._get_locator()

            position = await locator.get_geoposition_async()

            coordinate = position.coordinate

            return {
                "latitude": coordinate.latitude,
                "longitude": coordinate.longitude,
                "accuracy": coordinate.accuracy,
                "source": coordinate.position_source,
            }

        except Exception as error:
            print(f"[LOCATION ERROR] {error}")
            return None


location_service = LocationService()