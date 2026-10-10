"""
JARVIS PRO
Developer Memory

Memory Builder
"""

from typing import Any


class MemoryBuilder:
    """
    Builds structured Developer Memory.

    Converts information discovered by other
    Developer components into the standard
    memory structure.
    """

    def build(
        self,
        project: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        symbols: dict[str, Any] | None = None,
        dependencies: list[Any] | None = None,
        style: dict[str, Any] | None = None,
        edits: list[Any] | None = None,
        session: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build the complete memory structure.
        """

        return {

            "version": 1,

            "project": project or {},

            "files": files or {},

            "symbols": symbols or {},

            "dependencies": dependencies or [],

            "style": style or {},

            "edits": edits or [],

            "session": session or {},

        }

    # * --------------------------------------------------
    # * Project
    # * --------------------------------------------------

    def add_project(
        self,
        memory: dict[str, Any],
        key: str,
        value: Any,
    ) -> None:
        """
        Add or update project information.
        """

        memory.setdefault(
            "project",
            {},
        )

        memory["project"][key] = value

    # * --------------------------------------------------
    # * File
    # * --------------------------------------------------

    def add_file(
        self,
        memory: dict[str, Any],
        path: str,
        profile: Any,
    ) -> None:
        """
        Add or update a file profile.
        """

        if not path:
            return

        memory.setdefault(
            "files",
            {},
        )

        memory["files"][path] = profile

    # * --------------------------------------------------
    # * Symbol
    # * --------------------------------------------------

    def add_symbol(
        self,
        memory: dict[str, Any],
        name: str,
        record: Any,
    ) -> None:
        """
        Add or update a symbol record.
        """

        if not name:
            return

        memory.setdefault(
            "symbols",
            {},
        )

        memory["symbols"][name] = record

    # * --------------------------------------------------
    # * Dependency
    # * --------------------------------------------------

    def add_dependency(
        self,
        memory: dict[str, Any],
        dependency: Any,
    ) -> None:
        """
        Add a dependency relationship.
        """

        memory.setdefault(
            "dependencies",
            [],
        )

        memory["dependencies"].append(
            dependency,
        )

    # * --------------------------------------------------
    # * Style
    # * --------------------------------------------------

    def update_style(
        self,
        memory: dict[str, Any],
        key: str,
        value: Any,
    ) -> None:
        """
        Add or update a style rule.
        """

        if not key:
            return

        memory.setdefault(
            "style",
            {},
        )

        memory["style"][key] = value

    # * --------------------------------------------------
    # * Edit
    # * --------------------------------------------------

    def add_edit(
        self,
        memory: dict[str, Any],
        edit: Any,
    ) -> None:
        """
        Add an edit record.
        """

        memory.setdefault(
            "edits",
            [],
        )

        memory["edits"].append(
            edit,
        )

    # * --------------------------------------------------
    # * Session
    # * --------------------------------------------------

    def update_session(
        self,
        memory: dict[str, Any],
        key: str,
        value: Any,
    ) -> None:
        """
        Add or update session information.
        """

        if not key:
            return

        memory.setdefault(
            "session",
            {},
        )

        memory["session"][key] = value