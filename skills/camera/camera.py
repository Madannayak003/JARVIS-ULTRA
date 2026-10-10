import cv2
import datetime

from core.registry import register
from voice.manager import speak
from core.camera_manager import camera
from core.paths import CAPTURES

import cv2
import datetime

from core.registry import register
from voice.manager import speak
from core.camera_manager import camera
from core.paths import CAPTURES


def capture(data):

    speak("Opening camera.")

    frame = camera.capture_with_countdown(3)

    if frame is None:

        speak("Camera not available.")

        return True

    filename = datetime.datetime.now().strftime(
        "Capture_%Y%m%d_%H%M%S.jpg"
    )

    path = CAPTURES / filename

    cv2.imwrite(str(path), frame)

    camera.stop()

    speak("Photo captured.")

    print(f"[PHOTO] {path}")

    return True

def preview(data):

    speak("Opening camera")

    camera.show()

    return True


def close_camera(data):

    camera.stop()

    speak("Camera closed")

    return True

def start_recording(data):

    camera.start_recording()

    speak("Recording started")

    return True


def stop_recording(data):

    camera.stop_recording()

    speak("Recording stopped")

    return True

def camera_status(data):

    if camera.opened():

        speak("Camera is open.")

    else:

        speak("Camera is closed.")

    return True


register(
    "camera_status",
    camera_status
)

register(
    "capture",
    capture
)

register(
    "camera_preview",
    preview
)

register(
    "camera_close",
    close_camera
)

register(
    "start_recording",
    start_recording
)

register(
    "stop_recording",
    stop_recording
)