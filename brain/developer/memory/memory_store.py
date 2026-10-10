"""
JARVIS PRO
Developer Memory

Memory Store
"""

import json
from pathlib import Path
from typing import Any


class MemoryStore:
    """
    Low-level persistent storage for Developer Memory.

    The store is responsible only for:
        - creating the memory directory
        - reading memory data
        - writing memory data

    It does not decide what the memory means.
    """

    def __init__(
        self,
        project_path: str = "",
    ):
        self.project_path = Path(project_path) if project_path else None

        self.memory_directory = (
            self.project_path / ".jarvis_memory"
            if self.project_path
            else None
        )

        self.memory_file = (
            self.memory_directory / "memory.json"
            if self.memory_directory
            else None
        )

    # * --------------------------------------------------
    # * Configure
    # * --------------------------------------------------

    def configure(
        self,
        project_path: str,
    ) -> None:
        """
        Configure the store for a project.
        """

        self.project_path = Path(project_path)

        self.memory_directory = (
            self.project_path / ".jarvis_memory"
        )

        self.memory_file = (
            self.memory_directory / "memory.json"
        )

    # * --------------------------------------------------
    # * Ensure Storage
    # * --------------------------------------------------

    def ensure_storage(self) -> None:
        """
        Create the memory directory if required.
        """

        if self.memory_directory is None:
            return

        self.memory_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # * --------------------------------------------------
    # * Load
    # * --------------------------------------------------

    def load(self) -> dict[str, Any]:
        """
        Load the complete memory database.

        Returns an empty dictionary when no
        memory exists yet.
        """

        if self.memory_file is None:
            return {}

        if not self.memory_file.exists():
            return {}

        try:

            with self.memory_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            if not isinstance(data, dict):
                return {}

            return data

        except (
            json.JSONDecodeError,
            OSError,
        ):

            return {}

    # * --------------------------------------------------
    # * Save
    # * --------------------------------------------------

    def save(
        self,
        data: dict[str, Any],
    ) -> bool:
        """
        Save the complete memory database.
        """

        if self.memory_file is None:
            return False

        try:

            self.ensure_storage()

            temporary_file = (
                self.memory_file.with_suffix(".tmp")
            )

            with temporary_file.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

            temporary_file.replace(
                self.memory_file
            )

            return True

        except OSError:

            return False

    # * --------------------------------------------------
    # * Exists
    # * --------------------------------------------------

    def exists(self) -> bool:
        """
        Check whether persistent memory exists.
        """

        return (
            self.memory_file is not None
            and self.memory_file.exists()
        )

    # * --------------------------------------------------
    # * Clear
    # * --------------------------------------------------

    def clear(self) -> bool:
        """
        Remove the persistent memory file.
        """

        if self.memory_file is None:
            return False

        if not self.memory_file.exists():
            return True

        try:

            self.memory_file.unlink()

            return True

        except OSError:

            return False