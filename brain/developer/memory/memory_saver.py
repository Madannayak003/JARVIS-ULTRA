"""
JARVIS PRO
Developer Memory

Memory Saver
"""

from typing import Any

from brain.developer.memory.memory_store import (
    MemoryStore,
)


class MemorySaver:
    """
    Saves Developer Memory to persistent storage.
    """

    def __init__(
        self,
        store: MemoryStore | None = None,
    ):
        self.store = store or MemoryStore()

    # * --------------------------------------------------
    # * Configure
    # * --------------------------------------------------

    def configure(
        self,
        project_path: str,
    ) -> None:
        """
        Configure the saver for a project.
        """

        self.store.configure(
            project_path,
        )

    # * --------------------------------------------------
    # * Save
    # * --------------------------------------------------

    def save(
        self,
        memory: dict[str, Any],
    ) -> bool:
        """
        Save the complete memory database.
        """

        if not isinstance(memory, dict):
            return False

        return self.store.save(
            memory,
        )

    # * --------------------------------------------------
    # * Update
    # * --------------------------------------------------

    def update(
        self,
        key: str,
        value: Any,
    ) -> bool:
        """
        Load memory, update one top-level key,
        and save it again.
        """

        if not key:
            return False

        memory = self.store.load()

        memory[key] = value

        return self.store.save(
            memory,
        )