"""
JARVIS PRO
Screen Vision Engine

Captures the current desktop directly in memory
for multimodal AI analysis.

This does NOT save screenshots to disk.
"""

from datetime import datetime
from typing import Optional

import pyautogui


class ScreenVision:

    # * ==================================================
    # * Initialization
    # * ==================================================

    def __init__(self):

        self.last_capture = None
        self.last_capture_time: Optional[datetime] = None
        self.capture_count = 0

    # * ==================================================
    # * Capture Current Screen
    # * ==================================================

    def capture(self):

        try:

            image = pyautogui.screenshot()

            # * ------------------------------------------
            # * Validate capture
            # * ------------------------------------------

            if image is None:

                print(
                    "[SCREEN VISION ERROR] "
                    "Screen capture returned no image."
                )

                return None

            # * ------------------------------------------
            # * Store current frame in memory
            # * ------------------------------------------

            self.last_capture = image

            self.last_capture_time = datetime.now()

            self.capture_count += 1

            # * ------------------------------------------
            # * Diagnostics
            # * ------------------------------------------

            print(
                "[SCREEN VISION] Current screen captured."
            )

            print(
                "[SCREEN VISION] Resolution:",
                image.size,
            )

            print(
                "[SCREEN VISION] Capture count:",
                self.capture_count,
            )

            return image

        except Exception as e:

            print(
                f"[SCREEN VISION ERROR] {e}"
            )

            return None

    # * ==================================================
    # * Last Captured Frame
    # * ==================================================

    def get_last_capture(self):

        return self.last_capture

    # * ==================================================
    # * Capture Information
    # * ==================================================

    def get_capture_info(self):

        if self.last_capture is None:

            return {
                "available": False,
                
                "resolution": None,
                "captured_at": None,
                "capture_count": self.capture_count,
            }

        return {
            "available": True,
            "resolution": self.last_capture.size,
            "captured_at": self.last_capture_time,
            "capture_count": self.capture_count,
        }


# * ======================================================
# * Shared Screen Vision
# * ======================================================

screen_vision = ScreenVision()