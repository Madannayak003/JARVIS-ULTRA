"""
JARVIS PRO
Vision Object Detector

Stage 2:
YOLO-based object detection and tracking.

Responsibilities:
- Load YOLO11 once
- Select the best available inference device
- Run optimized object detection
- Run native YOLO object tracking
- Apply inference-level confidence/IoU limits
- Return standardized detection dictionaries

The detector is independent from CameraManager.
"""

from pathlib import Path

import torch
from ultralytics import YOLO


class ObjectDetector:

    def __init__(
        self,
        model_path="yolo11n.pt",
        confidence=0.25,
        iou=0.45,
        image_size=640,
        max_detections=25,
    ):
        self.model_path = Path(model_path)

        self.confidence = float(confidence)
        self.iou = float(iou)
        self.image_size = int(image_size)
        self.max_detections = int(max_detections)

        self.model = None
        self.loaded = False

        # * Prefer NVIDIA CUDA when available.
        # * Fall back safely to CPU.
        self.device = (
            0
            if torch.cuda.is_available()
            else "cpu"
        )

        # ! FP16 is useful on CUDA, but must not be used on CPU.
        self.half = torch.cuda.is_available()

    def load(self):
        if self.loaded:
            return True

        try:
            print(
                "[VISION DETECTOR] "
                f"Loading model: {self.model_path}"
            )
            print(
                "[VISION DETECTOR] "
                f"Device: {self.device}"
            )

            self.model = YOLO(
                str(self.model_path)
            )

            self.loaded = True

            print(
                "[VISION DETECTOR] "
                "Model loaded."
            )

            return True

        except Exception as e:
            print(
                "[VISION DETECTOR ERROR] "
                f"Model load failed: {e}"
            )

            self.model = None
            self.loaded = False

            return False

    def _build_detections(self, results):
        detections = []

        for result in results:
            boxes = result.boxes

            if boxes is None:
                continue

            for box in boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                coordinates = [
                    int(value)
                    for value in
                    box.xyxy[0].tolist()
                ]

                label = result.names.get(
                    class_id,
                    str(class_id)
                )

                detection = {
                    "label": label,
                    "confidence": confidence,
                    "box": coordinates,
                }

                # * Native YOLO tracking ID.
                # * Normal detection mode does not have one.
                if boxes.id is not None:
                    detection["track_id"] = int(
                        box.id[0]
                    )

                detections.append(
                    detection
                )

        return detections

    def detect(self, frame):
        """
        Standard object detection.

        Returns the existing detection format:
        {
            "label": str,
            "confidence": float,
            "box": [x1, y1, x2, y2]
        }
        """

        if frame is None:
            print(
                "[VISION DETECTOR] "
                "No frame supplied."
            )
            return []

        if not self.load():
            return []

        try:
            results = self.model.predict(
                source=frame,
                device=self.device,
                conf=self.confidence,
                iou=self.iou,
                imgsz=self.image_size,
                max_det=self.max_detections,
                half=self.half,
                verbose=False,
            )

            return self._build_detections(
                results
            )

        except Exception as e:
            print(
                "[VISION DETECTOR ERROR] "
                f"Detection failed: {e}"
            )
            return []

    def track(
        self,
        frame,
        persist=True,
        tracker="bytetrack.yaml",
    ):
        """
        Native YOLO object tracking.

        Track IDs remain associated with objects across
        sequential frames when persist=True.

        Returns:
        {
            "label": str,
            "confidence": float,
            "box": [x1, y1, x2, y2],
            "track_id": int
        }
        """

        if frame is None:
            print(
                "[VISION DETECTOR] "
                "No frame supplied."
            )
            return []

        if not self.load():
            return []

        try:
            results = self.model.track(
                source=frame,
                device=self.device,
                conf=self.confidence,
                iou=self.iou,
                imgsz=self.image_size,
                max_det=self.max_detections,
                half=self.half,
                persist=persist,
                tracker=tracker,
                verbose=False,
            )

            return self._build_detections(
                results
            )

        except Exception as e:
            print(
                "[VISION DETECTOR ERROR] "
                f"Tracking failed: {e}"
            )
            return []

    def reset_tracking(self):
        """
        Reset the native YOLO tracker state.
        """

        if self.model is None:
            return

        try:
            self.model.predictor = None
            print(
                "[VISION DETECTOR] "
                "Tracking state reset."
            )
        except Exception as e:
            print(
                "[VISION DETECTOR ERROR] "
                f"Tracking reset failed: {e}"
            )

    def status(self):
        return {
            "loaded": self.loaded,
            "model": str(self.model_path),
            "device": self.device,
            "half_precision": self.half,
            "confidence": self.confidence,
            "iou": self.iou,
            "image_size": self.image_size,
            "max_detections": self.max_detections,
        }


detector = ObjectDetector()