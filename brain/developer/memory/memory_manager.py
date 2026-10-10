"""
JARVIS PRO
Developer Memory

Memory Manager
"""

from typing import Any

from brain.developer.memory.memory_store import (
    MemoryStore,
)

from brain.developer.memory.memory_loader import (
    MemoryLoader,
)

from brain.developer.memory.memory_saver import (
    MemorySaver,
)

from brain.developer.memory.memory_builder import (
    MemoryBuilder,
)

from brain.developer.memory.memory_indexer import (
    MemoryIndexer,
)

from brain.developer.memory.memory_search import (
    MemorySearch,
)

from brain.developer.memory.memory_context import (
    MemoryContext,
)


class MemoryManager:
    """
    Coordinates the complete Developer Memory system.
    """

    def __init__(
        self,
        project_path: str = "",
    ):

        self.store = MemoryStore(
            project_path,
        )

        self.loader = MemoryLoader(
            self.store,
        )

        self.saver = MemorySaver(
            self.store,
        )

        self.builder = MemoryBuilder()

        self.indexer = MemoryIndexer()

        self.search_engine = MemorySearch(
            self.indexer,
        )

        self.context = MemoryContext(
            self.search_engine,
        )

        self.memory: dict[str, Any] = {}

    # * --------------------------------------------------
    # * Configure
    # * --------------------------------------------------

    def configure(
        self,
        project_path: str,
    ) -> None:
        """
        Configure memory for a project.
        """

        self.store.configure(
            project_path,
        )

        self.loader.configure(
            project_path,
        )

        self.saver.configure(
            project_path,
        )

    # * --------------------------------------------------
    # * Load
    # * --------------------------------------------------

    def load(self) -> dict[str, Any]:
        """
        Load memory and rebuild the index.
        """

        self.memory = self.loader.load()

        self.indexer.build(
            self.memory,
        )

        return self.memory

    # * --------------------------------------------------
    # * Save
    # * --------------------------------------------------

    def save(self) -> bool:
        """
        Save current memory.
        """

        return self.saver.save(
            self.memory,
        )

    # * --------------------------------------------------
    # * Replace
    # * --------------------------------------------------

    def set_memory(
        self,
        memory: dict[str, Any],
    ) -> None:
        """
        Replace current memory and rebuild index.
        """

        if not isinstance(memory, dict):
            return

        self.memory = memory

        self.indexer.build(
            self.memory,
        )

    # * --------------------------------------------------
    # * Project
    # * --------------------------------------------------

    def add_project(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add project memory.
        """

        self.builder.add_project(
            self.memory,
            key,
            value,
        )

        self.indexer.update(
            "project",
            key,
            value,
        )

    # * --------------------------------------------------
    # * File
    # * --------------------------------------------------

    def add_file(
        self,
        path: str,
        profile: Any,
    ) -> None:
        """
        Add file memory.
        """

        self.builder.add_file(
            self.memory,
            path,
            profile,
        )

        self.indexer.update(
            "files",
            path,
            profile,
        )

    # * --------------------------------------------------
    # * Symbol
    # * --------------------------------------------------

    def add_symbol(
        self,
        name: str,
        record: Any,
    ) -> None:
        """
        Add symbol memory.
        """

        self.builder.add_symbol(
            self.memory,
            name,
            record,
        )

        self.indexer.update(
            "symbols",
            name,
            record,
        )

    # * --------------------------------------------------
    # * Dependency
    # * --------------------------------------------------

    def add_dependency(
        self,
        dependency: Any,
    ) -> None:
        """
        Add dependency memory.
        """

        self.builder.add_dependency(
            self.memory,
            dependency,
        )

        self.indexer.build(
            self.memory,
        )

    # * --------------------------------------------------
    # * Style
    # * --------------------------------------------------

    def update_style(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Update style memory.
        """

        self.builder.update_style(
            self.memory,
            key,
            value,
        )

        self.indexer.update(
            "style",
            key,
            value,
        )

    # * --------------------------------------------------
    # * Edit
    # * --------------------------------------------------

    def add_edit(
        self,
        edit: Any,
    ) -> None:
        """
        Add an edit history record.
        """

        self.builder.add_edit(
            self.memory,
            edit,
        )

        self.indexer.build(
            self.memory,
        )

    # * --------------------------------------------------
    # * Session
    # * --------------------------------------------------

    def update_session(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Update session memory.
        """

        self.builder.update_session(
            self.memory,
            key,
            value,
        )

        self.indexer.update(
            "session",
            key,
            value,
        )

    # * --------------------------------------------------
    # * Search
    # * --------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search current memory.
        """

        return self.search_engine.search(
            query,
            limit,
        )

    # * --------------------------------------------------
    # * Context
    # * --------------------------------------------------

    def get_context(
        self,
        query: str = "",
    ) -> dict[str, Any]:
        """
        Build relevant memory context.
        """

        return self.context.build(
            query,
            self.memory,
        )