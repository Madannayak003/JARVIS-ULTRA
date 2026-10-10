"""
JARVIS PRO
Vision Core

Stage 2.1:
Camera + YOLO object detection integration.
"""

from core.camera_manager import camera
from skills.camera.detector import detector


class VisionEngine:

    def __init__(self):

        self.enabled = False

    # * --------------------------------------------------
    # * Start Vision
    # * --------------------------------------------------

    def start(self):

        camera.start()

        if camera.camera is None:

            print("[VISION] Camera unavailable.")

            return False

        if not camera.camera.isOpened():

            print("[VISION] Camera failed to open.")

            return False

        self.enabled = True

        print("[VISION] Vision started.")

        return True

    # * --------------------------------------------------
    # * Get Frame
    # * --------------------------------------------------

    def get_frame(self):

        if not self.enabled:

            if not self.start():

                return None

        frame = camera.frame()

        if frame is None:

            print("[VISION] Frame unavailable.")

            return None

        return frame

    # * --------------------------------------------------
    # * Detect Objects
    # * --------------------------------------------------

    def detect(self, frame=None):

        if frame is None:

            frame = self.get_frame()

        if frame is None:

            return []

        results = detector.detect(frame)

        return results
    
    def track(self, frame=None):
        if frame is None:
            frame = self.get_frame()

        if frame is None:
            return []

        results = detector.track(frame)

        return results

    # * --------------------------------------------------
    # * Capture + Detect
    # * --------------------------------------------------

    def detect_current(self):

        frame = self.get_frame()

        if frame is None:

            return []

        return self.detect(frame)

    # * --------------------------------------------------
    # * Status
    # * --------------------------------------------------

    def status(self):

        if not self.enabled:

            return {
                "active": False,
                "camera": camera.opened(),
                "frame": False,
            }

        return {
            "active": True,
            "camera": camera.opened(),
            "frame": camera.current_frame is not None,
        }

    # * --------------------------------------------------
    # * Stop Vision
    # * --------------------------------------------------

    def stop(self):

        self.enabled = False

        camera.stop()

        print("[VISION] Vision stopped.")

        return True


vision = VisionEngine()