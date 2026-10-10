"""YOLO person detection plus local LBPH identity recognition."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

try:
    from config.settings import (
        VISION_FACE_MIN_SIZE,
        VISION_FACE_RECOGNITION_THRESHOLD,
    )
except Exception:  # * Keep optional vision imports safe in minimal test envs.
    VISION_FACE_MIN_SIZE = 80
    VISION_FACE_RECOGNITION_THRESHOLD = 75.0
from skills.camera.face_registry import FaceRegistry, face_registry


class FaceRecognizer:
    """Detect faces and match them against ``data/faces`` locally.

    OpenCV is loaded lazily so the rest of JARVIS and its existing camera
    commands remain importable when the optional vision dependency is absent.
    """

    def __init__(
        self,
        registry: FaceRegistry | None = None,
        threshold: float = VISION_FACE_RECOGNITION_THRESHOLD,
        min_face_size: int = VISION_FACE_MIN_SIZE,
    ):
        self.registry = registry or face_registry
        self.threshold = float(threshold)
        self.min_face_size = int(min_face_size)
        self._model = None
        self._label_to_name: dict[int, str] = {}
        self._database_signature: tuple[tuple[str, int, int], ...] = ()
        self._lock = threading.RLock()

    @staticmethod
    def _cv2():
        try:
            import cv2
        except ImportError:
            return None
        return cv2

    def detect_faces(self, frame: Any, detections: list[dict] | None = None) -> list[dict]:
        """Build face-recognition regions from the existing YOLO person boxes.

        The bundled COCO YOLO model detects ``person`` rather than a separate
        ``face`` class. The upper portion of each person box is therefore used
        as the local recognition crop. Normal Vision passes its already-computed
        detections; registration performs one normal YOLO detection itself.
        """

        if frame is None:
            return []

        if detections is None:
            try:
                from skills.camera.detector import detector
                detections = detector.detect(frame)
            except Exception as exc:
                print(f"[VISION FACE ERROR] YOLO face region detection failed: {exc}")
                return []

        frame_shape = getattr(frame, "shape", (720, 1280, 3))
        results = []
        for detection in detections or []:
            if str(detection.get("label", "")).lower() != "person":
                continue
            box = detection.get("box")
            if not box or len(box) != 4:
                continue

            x1, y1, x2, y2 = [int(value) for value in box]
            width = max(0, x2 - x1)
            height = max(0, y2 - y1)
            if width < self.min_face_size or height < self.min_face_size:
                continue

            # * YOLO person boxes include the whole body. Crop the head/upper
            # * body region for LBPH without introducing another detector.
            margin_x = int(width * 0.18)
            head_box = [
                x1 + margin_x,
                y1,
                max(x1 + margin_x + 1, x2 - margin_x),
                min(y2, y1 + max(self.min_face_size, int(height * 0.42))),
            ]
            head_width = head_box[2] - head_box[0]
            head_height = head_box[3] - head_box[1]
            area_score = min(
                1.0,
                (head_width * head_height)
                / max(1, frame_shape[0] * frame_shape[1] * 0.02),
            )
            detection_confidence = float(detection.get("confidence", 0.0))
            quality = round((detection_confidence * 0.7) + (area_score * 0.3), 3)
            results.append(
                {
                    "type": "face",
                    "box": head_box,
                    "quality": quality,
                    "person_box": [x1, y1, x2, y2],
                }
            )

        return results

    def _signature(self) -> tuple[tuple[str, int, int], ...]:
        values = []
        for name, path in self.registry.all_samples():
            try:
                stat = path.stat()
            except OSError:
                continue
            values.append((name, stat.st_mtime_ns, stat.st_size))
        return tuple(values)

    def _prepare_crop(self, frame, box):
        cv2 = self._cv2()
        if cv2 is None:
            return None

        x1, y1, x2, y2 = [int(value) for value in box]
        crop = frame[max(0, y1) : max(0, y2), max(0, x1) : max(0, x2)]
        if crop is None or getattr(crop, "size", 0) == 0:
            return None
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        gray = cv2.resize(gray, (200, 200))
        return cv2.equalizeHist(gray)

    def _ensure_model(self):
        cv2 = self._cv2()
        if cv2 is None or not hasattr(cv2, "face"):
            self._model = None
            return False

        signature = self._signature()
        if signature == self._database_signature:
            return self._model is not None

        images = []
        labels = []
        label_to_name = {}
        next_label = 0

        for name in self.registry.identities():
            for path in self.registry.samples(name):
                image = cv2.imread(str(path))
                if image is None:
                    continue
                faces = self.detect_faces(image)
                if not faces:
                    continue
                crop = self._prepare_crop(image, faces[0]["box"])
                if crop is None:
                    continue
                images.append(crop)
                labels.append(next_label)
            if any(label == next_label for label in labels):
                label_to_name[next_label] = name
                next_label += 1

        self._database_signature = signature
        self._label_to_name = label_to_name
        self._model = None
        if images:
            try:
                factory = getattr(
                    cv2.face,
                    "LBPHFaceRecognizer_create",
                    None,
                )
                if factory is None:
                    recognizer_type = getattr(
                        cv2.face,
                        "LBPHFaceRecognizer",
                        None,
                    )
                    factory = getattr(
                        recognizer_type,
                        "create",
                        None,
                    )
                if factory is None:
                    raise RuntimeError(
                        "This OpenCV build exposes cv2.face but not LBPHFaceRecognizer."
                    )
                import numpy as np

                self._model = factory()
                self._model.train(
                    images,
                    np.asarray(labels, dtype=np.int32),
                )
            except Exception as exc:
                self._model = None
                print(f"[VISION FACE ERROR] LBPH training failed: {exc}")
        else:
            print(
                "[VISION FACE ERROR] YOLO found no usable face regions "
                "inside the registered samples."
            )

        return self._model is not None

    def prediction_result(self, label: int, distance: float) -> dict:
        """Convert an LBPH prediction into the public structured result."""

        name = self._label_to_name.get(int(label))
        confidence = max(0.0, min(1.0, 1.0 - (float(distance) / 100.0)))
        recognized = bool(name) and float(distance) <= self.threshold
        return {
            "type": "face",
            "name": name if recognized else None,
            "recognized": recognized,
            "confidence": round(confidence, 3),
        }

    def recognize_face(self, frame, face: dict) -> dict:
        result = {
            "type": "face",
            "name": None,
            "recognized": False,
            "confidence": 0.0,
        }

        with self._lock:
            if not self._ensure_model():
                return {**result, "box": face.get("box"), "quality": face.get("quality", 0.0)}

            crop = self._prepare_crop(frame, face.get("box", []))
            if crop is None:
                return {**result, "box": face.get("box"), "quality": face.get("quality", 0.0)}

            try:
                label, distance = self._model.predict(crop)
                result.update(self.prediction_result(label, distance))
            except Exception:
                pass

        result["box"] = face.get("box")
        result["quality"] = face.get("quality", 0.0)
        return result

    def analyze_frame(self, frame, detections: list[dict] | None = None) -> list[dict]:
        return [
            self.recognize_face(frame, face)
            for face in self.detect_faces(frame, detections=detections)
        ]

    def enrich_detections(self, frame, detections: list[dict]) -> list[dict]:
        """Add face identity fields to existing YOLO person detections."""

        result = [dict(item) for item in detections or []]
        faces = self.analyze_frame(frame, detections=result)
        person_indexes = [
            index for index, item in enumerate(result)
            if str(item.get("label", "")).lower() == "person"
        ]
        matched = set()

        for face in faces:
            box = face.get("box") or []
            if len(box) != 4:
                continue
            center_x = (box[0] + box[2]) / 2
            center_y = (box[1] + box[3]) / 2
            match_index = next(
                (
                    index for index in person_indexes
                    if index not in matched
                    and _center_inside(center_x, center_y, result[index].get("box"))
                ),
                None,
            )

            if match_index is None:
                result.append({
                    "label": "person",
                    "detection_confidence": max(
                        0.41,
                        float(face.get("quality", 0.0)),
                    ),
                    "box": box,
                    **face,
                })
                continue

            matched.add(match_index)
            detection_confidence = result[match_index].get(
                "confidence",
                result[match_index].get("detection_confidence", 0.0),
            )
            result[match_index].update(face)
            result[match_index]["detection_confidence"] = detection_confidence
            result[match_index]["face_confidence"] = face.get("confidence", 0.0)
            result[match_index]["type"] = "face"

        for index in person_indexes:
            result[index].setdefault("type", "person")
            result[index].setdefault("name", None)
            result[index].setdefault("recognized", False)
            result[index].setdefault("detection_confidence", result[index].get("confidence", 0.0))
            result[index].setdefault("face_confidence", 0.0)

        return result


def _center_inside(center_x: float, center_y: float, box) -> bool:
    if not box or len(box) != 4:
        return False
    return box[0] <= center_x <= box[2] and box[1] <= center_y <= box[3]


face_recognizer = FaceRecognizer()
