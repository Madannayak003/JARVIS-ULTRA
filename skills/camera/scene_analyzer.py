"""
JARVIS PRO
Vision Scene Analyzer

Stage 2.4:
Convert YOLO detections and spatial information into
a structured, tracking-aware vision scene.

Responsibilities:
- Filter detections
- Add spatial information
- Count objects
- Count positions and regions
- Track object identities
- Build object-position information
- Build a human-friendly scene description
"""

from skills.camera.vision_analyzer import vision_analyzer
from skills.camera.spatial_analyzer import spatial_analyzer
from skills.camera.face_speech import people_message


class SceneAnalyzer:

    def analyze(
        self,
        detections,
        frame_width=1280,
        frame_height=720,
    ):
        filtered = vision_analyzer.filter_detections(
            detections
        )

        spatial = spatial_analyzer.analyze(
            filtered,
            frame_width,
            frame_height,
        )
        
        relationships = (
            spatial_analyzer.analyze_relationships(
                spatial
            )
        )

        counts = vision_analyzer.count_objects(
            filtered
        )

        position_counts = self._count_positions(
            spatial
        )

        region_counts = self._count_regions(
            spatial
        )

        object_positions = (
            self._build_object_positions(
                spatial
            )
        )

        tracked_objects = (
            self._build_tracked_objects(
                spatial
            )
        )

        track_counts = (
            self._count_tracks(
                spatial
            )
        )

        description = self._build_description(
            spatial,
            counts,
        )

        return {
            "objects": spatial,
            "counts": counts,
            "description": description,
            "position_counts": position_counts,
            "region_counts": region_counts,
            "object_positions": object_positions,
            "tracked_objects": tracked_objects,
            "track_counts": track_counts,
            "relationships": relationships,
        }

    def _count_positions(self, objects):
        counts = {
            "left": 0,
            "center": 0,
            "right": 0,
        }

        for obj in objects:
            position = obj.get("position")

            if position in counts:
                counts[position] += 1

        return {
            position: count
            for position, count in counts.items()
            if count > 0
        }

    def _count_regions(self, objects):
        counts = {}

        for obj in objects:
            region = obj.get("region")

            if not region:
                continue

            counts[region] = (
                counts.get(region, 0) + 1
            )

        return counts

    def _build_object_positions(self, objects):
        result = {}

        for obj in objects:
            label = obj.get("label")

            if not label:
                continue

            entry = {
                "position": obj.get("position"),
                "horizontal_position": obj.get(
                    "horizontal_position"
                ),
                "vertical_position": obj.get(
                    "vertical_position"
                ),
                "region": obj.get("region"),
                "center": obj.get("center"),
                "normalized_center": obj.get(
                    "normalized_center"
                ),
                "confidence": obj.get(
                    "confidence"
                ),
            }

            result.setdefault(
                label,
                []
            ).append(entry)

        return result

    def _build_tracked_objects(self, objects):
        """
        Build a lookup of currently tracked objects.

        Only detections with a valid native YOLO
        track_id are included.
        """

        tracked = {}

        for obj in objects:
            track_id = obj.get("track_id")

            if track_id is None:
                continue

            tracked[str(track_id)] = {
                "track_id": track_id,
                "label": obj.get("label"),
                "confidence": obj.get(
                    "confidence"
                ),
                "box": obj.get("box"),
                "position": obj.get(
                    "position"
                ),
                "horizontal_position": obj.get(
                    "horizontal_position"
                ),
                "vertical_position": obj.get(
                    "vertical_position"
                ),
                "region": obj.get(
                    "region"
                ),
                "center": obj.get(
                    "center"
                ),
                "normalized_center": obj.get(
                    "normalized_center"
                ),
            }

        return tracked

    def _count_tracks(self, objects):
        """
        Count unique active track IDs grouped by label.
        """

        tracks = {}

        for obj in objects:
            track_id = obj.get("track_id")
            label = obj.get("label")

            if track_id is None or not label:
                continue

            tracks.setdefault(
                label,
                set()
            ).add(track_id)

        return {
            label: len(track_ids)
            for label, track_ids in tracks.items()
        }

    def _build_description(
        self,
        objects,
        counts,
    ):
        person_description = people_message(objects)
        if person_description:
            other_objects = [
                obj
                for obj in objects
                if str(obj.get("label", "")).lower() != "person"
            ]

            if not other_objects:
                return person_description

            other_description = self._build_description(
                other_objects,
                counts,
            )
            other_description = other_description.removeprefix(
                "I can see "
            )
            return (
                f"{person_description[:-1]}, and "
                f"{other_description}."
            )

        if not objects:
            return (
                "I don't see any recognizable objects."
            )

        grouped = {}

        for obj in objects:
            label = obj.get(
                "label",
                "something",
            )

            grouped.setdefault(
                label,
                []
            ).append(obj)

        descriptions = []

        for label, items in grouped.items():
            count = len(items)

            if count == 1:
                obj = items[0]

                position = obj.get(
                    "position",
                    "center",
                )

                region = obj.get("region")

                location = (
                    region
                    if region
                    else position
                )

                descriptions.append(
                    f"one {label} "
                    f"in the {location}"
                )

            else:
                regions = [
                    item.get("region")
                    for item in items
                    if item.get("region")
                ]

                regions = list(
                    dict.fromkeys(regions)
                )

                if len(regions) == 1:
                    descriptions.append(
                        f"{count} {label}s "
                        f"in the {regions[0]}"
                    )

                elif regions:
                    location_text = (
                        ", ".join(regions)
                    )

                    descriptions.append(
                        f"{count} {label}s "
                        f"across {location_text}"
                    )

                else:
                    descriptions.append(
                        f"{count} {label}s"
                    )

        if len(descriptions) == 1:
            return (
                f"I can see "
                f"{descriptions[0]}."
            )

        if len(descriptions) == 2:
            return (
                f"I can see "
                f"{descriptions[0]} "
                f"and "
                f"{descriptions[1]}."
            )

        return (
            "I can see "
            + ", ".join(
                descriptions[:-1]
            )
            + ", and "
            + descriptions[-1]
            + "."
        )


scene_analyzer = SceneAnalyzer()
