"""Natural, state-based speech for recognized people in Vision scenes."""

from __future__ import annotations

import time

try:
    from config.settings import VISION_SPEECH_COOLDOWN
except Exception:  # * Keep this pure formatting layer importable without extras.
    VISION_SPEECH_COOLDOWN = 5.0


def people_message(objects: list[dict], owner_name: str = "Madan") -> str | None:
    people = [
        item for item in objects or []
        if str(item.get("label", "")).lower() == "person"
    ]
    if not people:
        return None

    names = []
    unknown_count = 0
    for person in people:
        name = person.get("name") if person.get("recognized") else None
        if name and name not in names:
            names.append(name)
        elif not name:
            unknown_count += 1

    labels = [
        f"you, {name}" if name.casefold() == owner_name.casefold() else name
        for name in names
    ]
    if unknown_count == 1:
        labels.append("another person" if labels else "a person")
    elif unknown_count > 1:
        labels.append(f"{unknown_count} other people" if labels else f"{unknown_count} people")

    if len(labels) == 1:
        return f"I see {labels[0]}."
    if len(labels) == 2:
        if "," in labels[0]:
            return f"I see {labels[0]}, and {labels[1]}."
        return f"I see {labels[0]} and {labels[1]}."
    return "I see " + ", ".join(labels[:-1]) + ", and " + labels[-1] + "."


class VisionSpeechState:
    """Allow speech on person enter/change, never on every processed frame."""

    def __init__(self, cooldown: float = VISION_SPEECH_COOLDOWN, clock=None):
        self.cooldown = float(cooldown)
        self.clock = clock or time.monotonic
        self._signature = None
        self._last_nonempty_signature = None
        self._last_spoken = 0.0

    @staticmethod
    def signature(objects: list[dict]) -> tuple:
        people = [
            item for item in objects or []
            if str(item.get("label", "")).lower() == "person"
        ]
        identities = []
        for person in people:
            identities.append(
                person.get("name") if person.get("recognized") else None
            )
        return tuple(sorted(identities, key=lambda value: value or ""))

    def should_speak(self, objects: list[dict]) -> bool:
        current = self.signature(objects)
        if not current:
            self._signature = None
            return False

        changed = current != self._signature
        if not changed and self._signature is not None:
            return False
        now = self.clock()
        if (
            current == self._last_nonempty_signature
            and now - self._last_spoken < self.cooldown
        ):
            self._signature = None
            return False

        self._signature = current
        self._last_nonempty_signature = current
        self._last_spoken = now
        return True

    def reset(self) -> None:
        """Forget the previous scene when a Vision session ends."""

        self._signature = None
        self._last_nonempty_signature = None
        self._last_spoken = 0.0


vision_speech_state = VisionSpeechState()
