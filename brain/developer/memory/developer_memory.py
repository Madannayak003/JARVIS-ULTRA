"""
JARVIS PRO
Developer Memory

Developer Memory
"""

from typing import Any

from brain.developer.memory.memory_manager import (
    MemoryManager,
)


class DeveloperMemory:
    """
    Public interface for JARVIS Developer Memory.

    Other Developer components should use this
    class instead of directly accessing the
    internal memory components.
    """

    def __init__(
        self,
        project_path: str = "",
    ):

        self.manager = MemoryManager(
            project_path,
        )

    # * ==================================================
    # * Project
    # * ==================================================

    def configure(
        self,
        project_path: str,
    ) -> None:
        """
        Configure memory for a project.
        """

        self.manager.configure(
            project_path,
        )

    # * ==================================================
    # * Load / Save
    # * ==================================================

    def load(self) -> dict[str, Any]:
        """
        Load project memory.
        """

        return self.manager.load()

    def save(self) -> bool:
        """
        Save current project memory.
        """

        return self.manager.save()

    # * ==================================================
    # * Project Memory
    # * ==================================================

    def add_project(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add project information.
        """

        self.manager.add_project(
            key,
            value,
        )

    # * ==================================================
    # * File Memory
    # * ==================================================

    def add_file(
        self,
        path: str,
        profile: Any,
    ) -> None:
        """
        Add file information.
        """

        self.manager.add_file(
            path,
            profile,
        )

    # * ==================================================
    # * Symbol Memory
    # * ==================================================

    def add_symbol(
        self,
        name: str,
        record: Any,
    ) -> None:
        """
        Add symbol information.
        """

        self.manager.add_symbol(
            name,
            record,
        )

    # * ==================================================
    # * Dependency Memory
    # * ==================================================

    def add_dependency(
        self,
        dependency: Any,
    ) -> None:
        """
        Add dependency information.
        """

        self.manager.add_dependency(
            dependency,
        )

    # * ==================================================
    # * Style Memory
    # * ==================================================

    def update_style(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add or update a style preference.
        """

        self.manager.update_style(
            key,
            value,
        )

    # * ==================================================
    # * Edit History
    # * ==================================================

    def add_edit(
        self,
        edit: Any,
    ) -> None:
        """
        Record an editor operation.
        """

        self.manager.add_edit(
            edit,
        )

    # * ==================================================
    # * Session Memory
    # * ==================================================

    def update_session(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Update session information.
        """

        self.manager.update_session(
            key,
            value,
        )

    # * ==================================================
    # * Search
    # * ==================================================

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search Developer Memory.
        """

        return self.manager.search(
            query,
            limit,
        )

    # * ==================================================
    # * Context
    # * ==================================================

    def get_context(
        self,
        query: str = "",
    ) -> dict[str, Any]:
        """
        Get relevant memory context.
        """

        return self.manager.get_context(
            query,
        )

    # * ==================================================
    # * Raw Memory
    # * ==================================================

    @property
    def memory(self) -> dict[str, Any]:
        """
        Access the current memory structure.

        Prefer the public methods above for modifications.
        """

        return self.manager.memory