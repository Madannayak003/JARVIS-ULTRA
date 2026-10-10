"""
JARVIS PRO
Developer Memory

Memory Loader
"""

from typing import Any

from brain.developer.memory.memory_store import (
    MemoryStore,
)


class MemoryLoader:
    """
    Loads Developer Memory from persistent storage.

    The loader provides a higher-level interface
    over MemoryStore.
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
        Configure the loader for a project.
        """

        self.store.configure(
            project_path,
        )

    # * --------------------------------------------------
    # * Load
    # * --------------------------------------------------

    def load(self) -> dict[str, Any]:
        """
        Load all persistent memory.
        """

        data = self.store.load()

        if not data:
            return self._default_memory()

        return data

    # * --------------------------------------------------
    # * Default Memory
    # * --------------------------------------------------

    def _default_memory(self) -> dict[str, Any]:
        """
        Return the initial memory structure.
        """

        return {

            "version": 1,

            "project": {},

            "files": {},

            "symbols": {},

            "dependencies": [],

            "style": {},

            "edits": [],

            "session": {},

        }