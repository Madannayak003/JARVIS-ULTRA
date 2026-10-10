"""Asynchronous, cancellable face-registration flow for the existing camera."""

from __future__ import annotations

import threading
import time

try:
    from config.settings import (
        VISION_FACE_MIN_QUALITY,
        VISION_REGISTRATION_MAX_ATTEMPTS,
        VISION_REGISTRATION_SAMPLE_COUNT,
        VISION_REGISTRATION_SAMPLE_INTERVAL,
    )
except Exception:  # * Registration remains safely importable without optional deps.
    VISION_FACE_MIN_QUALITY = 0.20
    VISION_REGISTRATION_MAX_ATTEMPTS = 30
    VISION_REGISTRATION_SAMPLE_COUNT = 5
    VISION_REGISTRATION_SAMPLE_INTERVAL = 0.25
from skills.camera.face_registry import FaceRegistry, sanitize_name, face_registry
from skills.camera.face_recognizer import FaceRecognizer, face_recognizer


class FaceRegistrationFlow:
    def __init__(
        self,
        registry: FaceRegistry | None = None,
        recognizer: FaceRecognizer | None = None,
        camera_manager=None,
    ):
        self.registry = registry or face_registry
        self.recognizer = recognizer or face_recognizer
        self._camera = camera_manager
        self._lock = threading.RLock()
        self._cancel = threading.Event()
        self._thread = None
        self._samples = []
        self._phase = None
        self._camera_owned = False

    @property
    def active(self) -> bool:
        with self._lock:
            return self._phase is not None

    @property
    def waiting_for_name(self) -> bool:
        with self._lock:
            return self._phase == "awaiting_name"

    def start(self, name: str | None = None) -> bool:
        with self._lock:
            if self._phase is not None:
                return False
            safe_name = sanitize_name(name) if name else None
            self._cancel.clear()
            self._samples = []
            self._phase = "capturing"
            self._camera_owned = not self._camera_manager().opened()
            self._thread = threading.Thread(
                target=self._capture_worker,
                args=(safe_name,),
                daemon=True,
                name="JARVIS-FaceRegistration",
            )
            self._thread.start()

        _speak("Sure. Please look at the camera.")
        return True

    def provide_name(self, name: str) -> bool:
        with self._lock:
            if self._phase != "awaiting_name":
                return False
            samples = list(self._samples)

        try:
            safe_name = sanitize_name(name)
            self.registry.save_samples(safe_name, samples)
        except Exception:
            self._finish()
            _speak("Face registration wasn't completed.")
            return True

        self._finish()
        _speak(f"Face registration for {safe_name} is complete.")
        return True

    def cancel(self) -> bool:
        with self._lock:
            if self._phase is None:
                return False
            self._cancel.set()
            self._phase = None
            self._samples = []
            owned = self._camera_owned
            self._camera_owned = False

        if owned:
            self._camera_manager().stop()
        _speak("Face registration cancelled.")
        return True

    def handle_pending_input(self, command: str) -> bool:
        with self._lock:
            phase = self._phase
        if phase is None:
            return False

        normalized = " ".join((command or "").lower().split())
        if normalized in {"cancel", "cancel registration", "stop", "stop registration"}:
            return self.cancel()
        if phase == "awaiting_name":
            return self.provide_name(command)
        return True

    def _capture_worker(self, name: str | None):
        camera = self._camera_manager()
        if not camera.start():
            self._fail("I can't access the camera right now.")
            return

        attempts = 0
        last_frame = None
        saw_multiple_faces = False
        while attempts < VISION_REGISTRATION_MAX_ATTEMPTS and not self._cancel.is_set():
            attempts += 1
            frame = camera.frame()
            faces = self.recognizer.detect_faces(frame)

            if len(faces) > 1:
                saw_multiple_faces = True

            if len(faces) == 1:
                face = faces[0]
                if face.get("quality", 0.0) >= VISION_FACE_MIN_QUALITY:
                    # * Prefer visibly different samples, but take a periodic
                    # * sample when the person holds a steady pose.
                    if self._distinct_frame(frame, last_frame) or attempts % 3 == 0:
                        with self._lock:
                            self._samples.append(frame.copy() if hasattr(frame, "copy") else frame)
                        last_frame = frame.copy() if hasattr(frame, "copy") else frame
                        if len(self._samples) >= VISION_REGISTRATION_SAMPLE_COUNT:
                            break

            time.sleep(VISION_REGISTRATION_SAMPLE_INTERVAL)

        if self._cancel.is_set():
            return
        if len(self._samples) < VISION_REGISTRATION_SAMPLE_COUNT:
            self._fail(
                "Please make sure only one person is visible."
                if saw_multiple_faces
                else "I can't see a face clearly. Please look at the camera."
            )
            return

        if name:
            try:
                self.registry.save_samples(name, self._samples)
            except Exception:
                self._fail("Face registration wasn't completed.")
                return
            self._finish()
            _speak(f"Face registration for {name} is complete.")
            return

        with self._lock:
            self._phase = "awaiting_name"
        _speak("Got it. What name should I use?")

    @staticmethod
    def _distinct_frame(current, previous) -> bool:
        if current is None or previous is None:
            return True
        try:
            import cv2

            first = cv2.resize(current, (64, 64))
            second = cv2.resize(previous, (64, 64))
            difference = cv2.absdiff(first, second).mean()
            return float(difference) >= 2.0
        except Exception:
            return current is not previous

    def _fail(self, message: str):
        self._finish()
        _speak(message)

    def _finish(self):
        with self._lock:
            owned = self._camera_owned
            self._camera_owned = False
            self._phase = None
            self._samples = []
        if owned:
            self._camera_manager().stop()

    def _camera_manager(self):
        if self._camera is None:
            from core.camera_manager import camera
            self._camera = camera
        return self._camera


def _speak(message: str):
    try:
        from voice.manager import speak
        speak(message)
    except Exception as exc:
        print(f"[VISION REGISTRATION] Speech failed: {exc}")


face_registration = FaceRegistrationFlow()
