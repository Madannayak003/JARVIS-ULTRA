"""Local registered-face storage for the Vision skill.

The registry deliberately stores only the user-provided face samples under the
project's canonical ``data/faces`` directory.  Recognition models are trained
in memory from those samples and are never written to another database path.
"""

from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Callable, Iterable

from core.paths import FACES


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def sanitize_name(name: str) -> str:
    """Return a safe, human-readable directory name or raise ``ValueError``."""

    if not isinstance(name, str):
        raise ValueError("A face name is required.")

    normalized = unicodedata.normalize("NFKC", name)
    normalized = " ".join(normalized.strip().split())
    normalized = re.sub(r"[^\w .-]", "_", normalized, flags=re.UNICODE)
    normalized = normalized.strip(" .")

    if not normalized or normalized in {".", ".."} or not any(
        character.isalnum() for character in normalized
    ):
        raise ValueError("Please provide a valid face name.")

    return normalized


class FaceRegistry:
    """Discover and save registered samples below one canonical root."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root is not None else FACES
        self.root.mkdir(parents=True, exist_ok=True)

    def identity_path(self, name: str) -> Path:
        safe_name = sanitize_name(name)
        path = (self.root / safe_name).resolve()
        root = self.root.resolve()

        if path.parent != root:
            raise ValueError("Invalid face name.")

        return path

    def ensure_identity(self, name: str) -> Path:
        path = self.identity_path(name)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def identities(self) -> list[str]:
        if not self.root.exists():
            return []

        return sorted(
            path.name
            for path in self.root.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        )

    def samples(self, name: str) -> list[Path]:
        path = self.identity_path(name)
        if not path.exists():
            return []

        return sorted(
            sample
            for sample in path.iterdir()
            if sample.is_file() and sample.suffix.lower() in IMAGE_SUFFIXES
        )

    def all_samples(self) -> Iterable[tuple[str, Path]]:
        for name in self.identities():
            for sample in self.samples(name):
                yield name, sample

    def save_samples(
        self,
        name: str,
        frames: Iterable[object],
        image_writer: Callable[[str, object], bool] | None = None,
    ) -> list[Path]:
        """Save captured frames as sequential ``face_###.jpg`` samples."""

        directory = self.ensure_identity(name)

        if image_writer is None:
            try:
                import cv2
            except ImportError as exc:
                raise RuntimeError("OpenCV is required to save face samples.") from exc

            image_writer = cv2.imwrite

        existing = [
            int(match.group(1))
            for sample in self.samples(name)
            if (match := re.fullmatch(r"face_(\d+)\.[^.]+", sample.name))
        ]
        next_number = max(existing, default=0) + 1
        saved: list[Path] = []

        for frame in frames:
            path = directory / f"face_{next_number:03d}.jpg"
            if not image_writer(str(path), frame):
                raise RuntimeError("A face sample could not be saved.")
            saved.append(path)
            next_number += 1

        return saved

    def delete_identity(self, name: str) -> bool:
        """Delete one registered identity directory, if it exists."""

        path = self.identity_path(name)
        if not path.exists() or not path.is_dir():
            return False
        shutil.rmtree(path)
        return True

    def delete_all(self) -> int:
        """Delete all registered identity directories but keep the root."""

        deleted = 0
        self.root.mkdir(parents=True, exist_ok=True)
        for path in self.root.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                shutil.rmtree(path)
                deleted += 1
        return deleted


face_registry = FaceRegistry()
