"""
JARVIS PRO
Vision Processing Loop

Stage 2.3:
Continuous YOLO scene processing with temporal stability.

Responsibilities:
- Capture frames through VisionEngine
- Run YOLO detection
- Analyze the scene
- Stabilize detections across frames
- Publish a reliable latest scene

CameraManager remains untouched.
"""

import threading
import time

from skills.camera.vision import vision
from skills.camera.scene_analyzer import scene_analyzer
from skills.camera.face_recognizer import face_recognizer
from skills.camera.face_speech import people_message, vision_speech_state


class VisionLoop:

    def __init__(
        self,
        interval=0.5,
        stability_frames=2,
    ):

        self.interval = interval

        self.running = False
        self.thread = None

        self.latest_scene = None

        # * Used to signal that the first scene is ready
        self.scene_ready = threading.Event()

        # * --------------------------------------------------
        # * Temporal stability
        # * --------------------------------------------------

        self.stability_frames = max(
            1,
            int(stability_frames),
        )

        self._candidate_scene = None
        self._candidate_signature = None
        self._candidate_count = 0

    # * --------------------------------------------------
    # * Start
    # * --------------------------------------------------

    def start(self):

        if self.running:

            print(
                "[VISION LOOP] Already running."
            )

            self.scene_ready.wait(
                timeout=5
            )

            return True

        print(
            "[VISION LOOP] Starting..."
        )

        # * Clear previous state
        self.latest_scene = None
        self.scene_ready.clear()

        self._reset_stability()

        if not vision.start():

            print(
                "[VISION LOOP] "
                "Vision failed to start."
            )

            return False

        self.running = True

        self.thread = threading.Thread(
            target=self._run,
            name="VisionLoop",
            daemon=True,
        )

        self.thread.start()

        print(
            "[VISION LOOP] Started. "
            "Waiting for first stable scene..."
        )

        if not self.scene_ready.wait(
            timeout=10
        ):

            print(
                "[VISION LOOP] WARNING: "
                "First stable scene was not ready "
                "within 10 seconds."
            )

        else:

            print(
                "[VISION LOOP] "
                "First stable scene ready."
            )

        return True

    # * --------------------------------------------------
    # * Detection Signature
    # * --------------------------------------------------

    def _scene_signature(self, scene):

        if not scene:

            return ()

        objects = scene.get(
            "objects",
            []
        )

        signature = []

        for obj in objects:

            label = str(
                obj.get(
                    "label",
                    ""
                )
            ).lower().strip()

            position = str(
                obj.get(
                    "position",
                    ""
                )
            ).lower().strip()

            region = str(
                obj.get(
                    "region",
                    ""
                )
            ).lower().strip()

            if not label:

                continue

            signature.append(
                (
                    label,
                    position,
                    region,
                )
            )

        return tuple(
            sorted(signature)
        )

    # * --------------------------------------------------
    # * Stability
    # * --------------------------------------------------

    def _reset_stability(self):

        self._candidate_scene = None
        self._candidate_signature = None
        self._candidate_count = 0

    def _update_stability(self, scene):

        signature = self._scene_signature(
            scene
        )

        # * No objects detected.
        if not signature:

            self._candidate_scene = scene
            self._candidate_signature = signature
            self._candidate_count += 1

        elif (
            signature
            == self._candidate_signature
        ):

            self._candidate_count += 1

        else:

            self._candidate_scene = scene
            self._candidate_signature = signature
            self._candidate_count = 1

        # * Stable enough to publish.
        if (
            self._candidate_count
            >= self.stability_frames
        ):

            return self._candidate_scene

        return None

    # * --------------------------------------------------
    # * Processing Loop
    # * --------------------------------------------------

    def _run(self):

        print(
            "[VISION LOOP] Worker started."
        )

        while self.running:

            try:

                frame = vision.get_frame()

                if frame is None:

                    time.sleep(
                        self.interval
                    )

                    continue

                detections = vision.track(frame)

                # * Reuse this frame and the existing YOLO detections. Face
                # * recognition only enriches person detections; it does not
                # * create a second camera or object-detection pipeline.
                detections = face_recognizer.enrich_detections(
                    frame,
                    detections,
                )

                scene = scene_analyzer.analyze(
                    detections,
                    frame.shape[1],
                    frame.shape[0],
                )

                stable_scene = (
                    self._update_stability(
                        scene
                    )
                )

                if stable_scene is not None:

                    self.latest_scene = (
                        stable_scene
                    )

                    self._announce_people(stable_scene)

                    # * Signal first stable scene
                    if not self.scene_ready.is_set():

                        self.scene_ready.set()

            except Exception as e:

                print(
                    "[VISION LOOP ERROR]",
                    e
                )

            if self.running:

                time.sleep(
                    self.interval
                )

        print(
            "[VISION LOOP] Worker exited."
        )

    @staticmethod
    def _announce_people(scene):
        objects = (scene or {}).get("objects", [])
        message = (scene or {}).get("description") or people_message(objects)
        if not message:
            # * An empty stable scene is the leave transition. Clear the
            # * previous identity so a later return can speak again.
            vision_speech_state.should_speak(objects)
            return
        if not vision_speech_state.should_speak(objects):
            return

        try:
            from hud.integration import HUDIntegration
            from voice.manager import speak

            HUDIntegration.system_activity(f"VISION: {message}")
            speak(message)
        except Exception as exc:
            print("[VISION SPEECH ERROR]", exc)

    # * --------------------------------------------------
    # * Get Latest Scene
    # * --------------------------------------------------

    def get_scene(self):

        return self.latest_scene

    # * --------------------------------------------------
    # * Status
    # * --------------------------------------------------

    def status(self):

        return {
            "running": self.running,
            "scene": self.latest_scene,
            "stability_frames": (
                self.stability_frames
            ),
            "candidate_count": (
                self._candidate_count
            ),
        }

    # * --------------------------------------------------
    # * Stop
    # * --------------------------------------------------

    def stop(self):

        if not self.running:

            print(
                "[VISION LOOP] Already stopped."
            )

            return True

        print(
            "[VISION LOOP] Stopping..."
        )

        self.running = False

        if (
            self.thread
            and self.thread.is_alive()
        ):

            self.thread.join(
                timeout=15
            )

        if (
            self.thread
            and self.thread.is_alive()
        ):

            print(
                "[VISION LOOP] WARNING: "
                "Worker did not stop within timeout."
            )

        self.thread = None

        vision.stop()
        vision_speech_state.reset()

        self.latest_scene = None
        self.scene_ready.clear()

        self._reset_stability()

        print(
            "[VISION LOOP] Stopped."
        )

        return True


vision_loop = VisionLoop()
