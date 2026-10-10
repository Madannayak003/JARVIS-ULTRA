from collections import Counter


class VisionAnalyzer:
    """
    Converts raw YOLO detections into human-friendly descriptions.
    """

    def __init__(self, confidence_threshold=0.40):
        self.confidence_threshold = confidence_threshold

    def filter_detections(self, detections):
        if not detections:
            return []

        return [
            detection
            for detection in detections
            if detection.get(
                "detection_confidence",
                detection.get("confidence", 0),
            ) >= self.confidence_threshold
        ]

    def count_objects(self, detections):
        counts = Counter(
            detection["label"]
            for detection in detections
        )

        return dict(counts)

    def describe(self, detections):
        detections = self.filter_detections(detections)

        if not detections:
            return "I don't see any recognizable objects."

        counts = self.count_objects(detections)

        parts = []

        for label, count in counts.items():

            if count == 1:
                parts.append(f"one {label}")
            else:
                parts.append(f"{count} {label}s")

        if len(parts) == 1:
            return f"I can see {parts[0]}."

        if len(parts) == 2:
            return f"I can see {parts[0]} and {parts[1]}."

        return "I can see " + ", ".join(parts[:-1]) + f", and {parts[-1]}."

    def analyze(self, detections):
        filtered = self.filter_detections(detections)

        return {
            "objects": filtered,
            "counts": self.count_objects(filtered),
            "description": self.describe(filtered),
        }


vision_analyzer = VisionAnalyzer()
