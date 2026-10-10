"""
JARVIS PRO
Vision Query

Stage 2.6:
Target-aware queries over the current vision scene.

Supports:
- Scene description
- Object counting
- Object existence
- Position queries
- Object location queries
- Tracked-object queries
- Multiple-object targeting
- Spatial ranking
"""

from skills.camera.vision_loop import vision_loop


class VisionQuery:

    def get_scene(self):
        return vision_loop.get_scene()

    def describe(self):
        scene = self.get_scene()

        if not scene:
            return "I don't have a current vision scene."

        return scene.get(
            "description",
            "I don't see anything recognizable.",
        )

    def count(self, object_name):
        scene = self.get_scene()

        if not scene:
            return 0

        object_name = (
            object_name
            .lower()
            .strip()
        )

        counts = scene.get(
            "counts",
            {},
        )

        if object_name in counts:
            return counts[object_name]

        track_counts = scene.get(
            "track_counts",
            {},
        )

        return track_counts.get(
            object_name,
            0,
        )

    def has_object(self, object_name):
        return self.count(object_name) > 0

    def objects(self):
        scene = self.get_scene()

        if not scene:
            return []

        return scene.get(
            "objects",
            [],
        )

    def tracked_objects(self):
        scene = self.get_scene()

        if not scene:
            return {}

        return scene.get(
            "tracked_objects",
            {},
        )

    def objects_at(self, position):
        position = (
            position
            .lower()
            .strip()
        )

        objects = [
            obj
            for obj in self.objects()
            if obj.get("position") == position
        ]

        if not objects:
            return (
                f"I don't see anything "
                f"on your {position}."
            )

        labels = [
            obj.get(
                "label",
                "something",
            )
            for obj in objects
        ]

        if len(labels) == 1:
            return (
                f"I can see one "
                f"{labels[0]} "
                f"on your {position}."
            )

        if len(labels) == 2:
            return (
                f"I can see "
                f"{labels[0]} and "
                f"{labels[1]} "
                f"on your {position}."
            )

        return (
            f"I can see "
            f"{len(labels)} objects "
            f"on your {position}."
        )

    def locate(self, object_name):
        """
        Find the current location of an object.

        If multiple matching objects exist,
        return all distinct locations.
        """

        matches = self._find_objects(
            object_name
        )

        if not matches:
            return (
                f"I don't see a "
                f"{object_name.lower().strip()}."
            )

        if len(matches) == 1:
            obj = matches[0]

            return self._format_location(
                obj
            )

        locations = []

        for obj in matches:
            location = self._location_name(
                obj
            )

            if location not in locations:
                locations.append(location)

        label = object_name.lower().strip()

        if len(locations) == 1:
            return (
                f"I see {len(matches)} "
                f"{label}s in the "
                f"{locations[0]}."
            )

        return (
            f"I see {len(matches)} "
            f"{label}s across "
            + ", ".join(locations)
            + "."
        )

    def position_of(self, object_name):
        """
        Return the horizontal position of an object.

        For multiple matches, return all distinct
        horizontal positions.
        """

        matches = self._find_objects(
            object_name
        )

        if not matches:
            return None

        positions = []

        for obj in matches:
            position = obj.get(
                "position"
            )

            if (
                position
                and position not in positions
            ):
                positions.append(position)

        if len(positions) == 1:
            return positions[0]

        return positions

    def objects_in_region(self, region):
        """
        Return objects in a specific spatial region.
        """

        region = (
            region
            .lower()
            .strip()
        )

        return [
            obj
            for obj in self.objects()
            if obj.get("region") == region
        ]

    def find_objects(
        self,
        object_name,
    ):
        """
        Return all currently visible instances
        of an object type.
        """

        return self._find_objects(
            object_name
        )

    def nearest_to_center(
        self,
        object_name=None,
    ):
        """
        Find the object nearest to the center
        of the camera frame.

        If object_name is supplied, only that
        object type is considered.
        """

        objects = self.objects()

        if object_name:
            objects = self._find_objects(
                object_name
            )

        if not objects:
            return None

        return min(
            objects,
            key=self._center_distance,
        )

    def farthest_from_center(
        self,
        object_name=None,
    ):
        """
        Find the object farthest from the center
        of the camera frame.
        """

        objects = self.objects()

        if object_name:
            objects = self._find_objects(
                object_name
            )

        if not objects:
            return None

        return max(
            objects,
            key=self._center_distance,
        )

    def select_target(
        self,
        object_name,
        position=None,
        region=None,
    ):
        """
        Select the best matching target.

        Priority:
        1. Object label
        2. Requested region
        3. Requested horizontal position
        4. Closest to frame center
        5. Highest confidence

        Explicit position/region filters are strict.
        """

        matches = self._find_objects(
            object_name
        )

        if not matches:
            return None

        if region:
            region = (
                region
                .lower()
                .strip()
            )

            matches = [
                obj
                for obj in matches
                if obj.get("region") == region
            ]

            if not matches:
                return None

        if position:
            position = (
                position
                .lower()
                .strip()
            )

            matches = [
                obj
                for obj in matches
                if obj.get("position") == position
            ]

            if not matches:
                return None

        return min(
            matches,
            key=lambda obj: (
                self._center_distance(obj),
                -float(
                    obj.get(
                        "confidence",
                        0.0,
                    )
                ),
            ),
        )

    def target_info(
        self,
        object_name,
        position=None,
        region=None,
    ):
        """
        Return structured information about
        the best matching target.
        """

        target = self.select_target(
            object_name,
            position=position,
            region=region,
        )

        if target is None:
            return None

        return {
            "label": target.get(
                "label"
            ),
            "track_id": target.get(
                "track_id"
            ),
            "confidence": target.get(
                "confidence"
            ),
            "box": target.get(
                "box"
            ),
            "position": target.get(
                "position"
            ),
            "horizontal_position": target.get(
                "horizontal_position"
            ),
            "vertical_position": target.get(
                "vertical_position"
            ),
            "region": target.get(
                "region"
            ),
            "center": target.get(
                "center"
            ),
            "normalized_center": target.get(
                "normalized_center"
            ),
        }

    def scene_summary(self):
        """
        Return a concise summary of the current scene.
        """

        scene = self.get_scene()

        if not scene:
            return (
                "I don't have a current "
                "vision scene."
            )

        objects = scene.get(
            "objects",
            [],
        )

        if not objects:
            return (
                "I don't see any "
                "recognizable objects."
            )

        counts = scene.get(
            "counts",
            {},
        )

        parts = []

        for label, count in counts.items():
            if count == 1:
                parts.append(
                    f"1 {label}"
                )
            else:
                parts.append(
                    f"{count} {label}s"
                )

        if not parts:
            return (
                "I don't see any "
                "recognizable objects."
            )

        return (
            "I currently see "
            + ", ".join(parts)
            + "."
        )

    def _find_objects(self, object_name):
        object_name = (
            str(object_name)
            .lower()
            .strip()
        )

        return [
            obj
            for obj in self.objects()
            if str(
                obj.get("label", "")
            ).lower().strip()
            == object_name
        ]

    def _location_name(self, obj):
        return (
            obj.get("region")
            or obj.get("position")
            or "unknown"
        )

    def _format_location(self, obj):
        label = obj.get(
            "label",
            "object",
        )

        location = self._location_name(
            obj
        )

        return (
            f"The {label} "
            f"is in the {location}."
        )

    def _center_distance(self, obj):
        normalized = obj.get(
            "normalized_center"
        )

        if normalized:
            x = float(
                normalized.get("x", 0.5)
            )
            y = float(
                normalized.get("y", 0.5)
            )
        else:
            center = obj.get(
                "center",
                {}
            )

            x = float(
                center.get("x", 0)
            )
            y = float(
                center.get("y", 0)
            )

            width = 1280.0
            height = 720.0

            x /= width
            y /= height

        dx = x - 0.5
        dy = y - 0.5

        return (
            dx * dx
            + dy * dy
        ) ** 0.5


vision_query = VisionQuery()