"""
JARVIS PRO
Vision Spatial Analyzer

Stage 2.7:
Convert YOLO bounding boxes into spatial and geometric
information.

Existing compatibility:
- position
- horizontal_position
- vertical_position
- region
- center
- normalized_center

Additional intelligence:
- box width / height
- box area
- normalized area
- center distance
- relative size
"""

import math


class SpatialAnalyzer:

    def __init__(
        self,
        frame_width=1280,
        frame_height=720,
    ):
        self.frame_width = frame_width
        self.frame_height = frame_height

    def get_center(self, box):
        x1, y1, x2, y2 = box

        return {
            "x": (x1 + x2) / 2,
            "y": (y1 + y2) / 2,
        }

    def get_horizontal_position(
        self,
        center_x,
        frame_width=None,
    ):
        width = (
            frame_width
            or self.frame_width
        )

        left_boundary = width / 3
        right_boundary = (
            width * 2
        ) / 3

        if center_x < left_boundary:
            return "left"

        if center_x > right_boundary:
            return "right"

        return "center"

    def get_vertical_position(
        self,
        center_y,
        frame_height=None,
    ):
        height = (
            frame_height
            or self.frame_height
        )

        top_boundary = height / 3
        bottom_boundary = (
            height * 2
        ) / 3

        if center_y < top_boundary:
            return "top"

        if center_y > bottom_boundary:
            return "bottom"

        return "middle"

    def get_position(
        self,
        box,
        frame_width=None,
    ):
        center = self.get_center(box)

        return self.get_horizontal_position(
            center["x"],
            frame_width,
        )

    def get_region(
        self,
        horizontal,
        vertical,
    ):
        if vertical == "middle":
            return horizontal

        return (
            f"{vertical}-{horizontal}"
        )

    def get_geometry(
        self,
        box,
        frame_width=None,
        frame_height=None,
    ):
        """
        Calculate geometric information for a
        bounding box.
        """

        width = (
            frame_width
            or self.frame_width
        )

        height = (
            frame_height
            or self.frame_height
        )

        x1, y1, x2, y2 = box

        box_width = max(
            0,
            x2 - x1,
        )

        box_height = max(
            0,
            y2 - y1,
        )

        area = (
            box_width
            * box_height
        )

        frame_area = (
            width * height
        )

        normalized_area = (
            area / frame_area
            if frame_area > 0
            else 0.0
        )

        center = self.get_center(
            box
        )

        normalized_x = (
            center["x"] / width
            if width > 0
            else 0.5
        )

        normalized_y = (
            center["y"] / height
            if height > 0
            else 0.5
        )

        # * Distance from the center of the
        # * camera frame, normalized to 0..1.
        dx = normalized_x - 0.5
        dy = normalized_y - 0.5

        center_distance = math.sqrt(
            (dx * dx)
            + (dy * dy)
        )

        return {
            "width": int(box_width),
            "height": int(box_height),
            "area": int(area),
            "normalized_area": round(
                normalized_area,
                4,
            ),
            "center_distance": round(
                center_distance,
                4,
            ),
        }

    def get_relative_size(
        self,
        normalized_area,
    ):
        """
        Classify apparent object size in the frame.

        This is NOT a physical distance measurement.
        It is an image-based size estimate.
        """

        if normalized_area >= 0.35:
            return "very-large"

        if normalized_area >= 0.20:
            return "large"

        if normalized_area >= 0.08:
            return "medium"

        if normalized_area >= 0.02:
            return "small"

        return "very-small"
    
    def get_relative_position(self, first, second):
        """
        Determine the position of one object relative
        to another object.

        Returns a combination such as:
        - left
        - right
        - above
        - below
        - upper-left
        - upper-right
        - lower-left
        - lower-right
        - overlapping
        """

        first_center = first.get("center", {})
        second_center = second.get("center", {})

        first_x = float(
            first_center.get("x", 0)
        )
        first_y = float(
            first_center.get("y", 0)
        )

        second_x = float(
            second_center.get("x", 0)
        )
        second_y = float(
            second_center.get("y", 0)
        )

        dx = first_x - second_x
        dy = first_y - second_y

        # * Small tolerance prevents tiny detection
        # * movements from creating meaningless relationships.
        horizontal_tolerance = (
            self.frame_width * 0.08
        )
        vertical_tolerance = (
            self.frame_height * 0.08
        )

        horizontal = None
        vertical = None

        if dx < -horizontal_tolerance:
            horizontal = "left"
        elif dx > horizontal_tolerance:
            horizontal = "right"

        if dy < -vertical_tolerance:
            vertical = "above"
        elif dy > vertical_tolerance:
            vertical = "below"

        if horizontal and vertical:
            return f"{vertical}-{horizontal}"

        if horizontal:
            return horizontal

        if vertical:
            return vertical

        return "overlapping"

    def calculate_relationships(self, objects):
        """
        Calculate spatial relationships between every
        pair of visible objects.

        Each relationship describes the first object
        relative to the second object.
        """

        relationships = []

        for index, first in enumerate(objects):

            for second_index, second in enumerate(objects):

                if index == second_index:
                    continue

                first_label = first.get(
                    "label",
                    "object",
                )

                second_label = second.get(
                    "label",
                    "object",
                )

                first_track_id = first.get(
                    "track_id"
                )

                second_track_id = second.get(
                    "track_id"
                )

                relation = self.get_relative_position(
                    first,
                    second,
                )

                relationships.append(
                    {
                        "first": {
                            "label": first_label,
                            "track_id": first_track_id,
                        },
                        "second": {
                            "label": second_label,
                            "track_id": second_track_id,
                        },
                        "relation": relation,
                    }
                )

        return relationships
    
    def analyze_relationships(self, objects):
        """
        Calculate relationships using already analyzed
        spatial objects.

        Keeps analyze() backward compatible.
        """

        return self.calculate_relationships(
            objects
        )

    def analyze(
        self,
        detections,
        frame_width=None,
        frame_height=None,
    ):
        width = (
            frame_width
            or self.frame_width
        )

        height = (
            frame_height
            or self.frame_height
        )

        results = []

        for detection in detections:

            box = detection.get(
                "box"
            )

            if (
                not box
                or len(box) != 4
            ):
                continue

            center = self.get_center(
                box
            )

            horizontal = (
                self.get_horizontal_position(
                    center["x"],
                    width,
                )
            )

            vertical = (
                self.get_vertical_position(
                    center["y"],
                    height,
                )
            )

            region = self.get_region(
                horizontal,
                vertical,
            )

            normalized_x = (
                center["x"] / width
                if width > 0
                else 0.0
            )

            normalized_y = (
                center["y"] / height
                if height > 0
                else 0.0
            )

            geometry = self.get_geometry(
                box,
                width,
                height,
            )

            relative_size = (
                self.get_relative_size(
                    geometry["normalized_area"]
                )
            )

            results.append(
                {
                    **detection,
                    "position": horizontal,
                    "horizontal_position": horizontal,
                    "vertical_position": vertical,
                    "region": region,
                    "center": {
                        "x": round(
                            center["x"],
                            1,
                        ),
                        "y": round(
                            center["y"],
                            1,
                        ),
                    },
                    "normalized_center": {
                        "x": round(
                            normalized_x,
                            4,
                        ),
                        "y": round(
                            normalized_y,
                            4,
                        ),
                    },
                    "geometry": geometry,
                    "relative_size": relative_size,
                }
            )

        return results


spatial_analyzer = SpatialAnalyzer()