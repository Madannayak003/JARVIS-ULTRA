"""
JARVIS PRO
Developer

Active Project Resolver
"""

import json

from pathlib import Path

from brain.developer.memory.developer_memory import (
    DeveloperMemory,
)


class ActiveProjectResolver:
    """
    Resolves the currently active Developer project.

    Global state:
        Remembers which project was active across
        JARVIS restarts.

    Project state:
        Actual Developer Memory remains inside
        the project itself.
    """

    # * ==================================================
    # * Global Active Project Storage
    # * ==================================================

    GLOBAL_DIRECTORY = (
        Path.home()
        / ".jarvis_pro"
        / "developer"
    )

    GLOBAL_FILE = (
        GLOBAL_DIRECTORY
        / "active_project.json"
    )

    # * ==================================================
    # * Init
    # * ==================================================

    def __init__(
        self,
        memory: DeveloperMemory | None = None,
    ):

        self.memory = (
            memory
            or DeveloperMemory()
        )

    # * ==================================================
    # * Configure
    # * ==================================================

    def configure(
        self,
        project_path: str,
    ) -> bool:
        """
        Configure and persist the active Developer project.
        """

        if not project_path:

            return False

        path = (
            Path(
                project_path,
            )
            .expanduser()
            .resolve()
        )

        # * ----------------------------------------------
        # * Validate
        # * ----------------------------------------------

        if not path.exists():

            print(
                "[ACTIVE PROJECT] "
                "Project does not exist:",
                path,
            )

            return False

        if not path.is_dir():

            print(
                "[ACTIVE PROJECT] "
                "Project path is not a directory:",
                path,
            )

            return False

        project_path = str(path)

        # * ----------------------------------------------
        # * Configure project memory
        # * ----------------------------------------------

        self.memory.configure(
            project_path,
        )

        self.memory.load()

        self.memory.update_session(
            "project_path",
            project_path,
        )

        self.memory.save()

        # * ----------------------------------------------
        # * Persist global active project
        # * ----------------------------------------------

        if not self._save_active_project(
            project_path,
        ):

            print(
                "[ACTIVE PROJECT] "
                "Failed to save global active project."
            )

            return False

        print(
            "[ACTIVE PROJECT] Configured:",
            project_path,
        )

        return True

    # * ==================================================
    # * Resolve
    # * ==================================================

    def resolve(self) -> str | None:
        """
        Return the active Developer project.

        Resolution order:

            1. Globally persisted active project
            2. Project memory session
            3. Project memory project path
        """

        # * ----------------------------------------------
        # * Global active project
        # * ----------------------------------------------

        project_path = (
            self._load_active_project()
        )

        if project_path:

            path = Path(
                project_path,
            )

            if (
                path.exists()
                and path.is_dir()
            ):

                # * Configure DeveloperMemory so the
                # * rest of Developer can immediately
                # * use this project's memory.

                self.memory.configure(
                    str(path),
                )

                self.memory.load()

                return str(
                    path.resolve(),
                )

            # * ------------------------------------------
            # * Stale project
            # * ------------------------------------------

            print(
                "[ACTIVE PROJECT] "
                "Stored project no longer exists:",
                path,
            )

            self._clear_active_project()

        return None

    # * ==================================================
    # * Save Global Active Project
    # * ==================================================

    def _save_active_project(
        self,
        project_path: str,
    ) -> bool:

        try:

            self.GLOBAL_DIRECTORY.mkdir(
                parents=True,
                exist_ok=True,
            )

            data = {
                "project_path": project_path,
            }

            temporary_file = (
                self.GLOBAL_FILE.with_suffix(
                    ".tmp"
                )
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
                self.GLOBAL_FILE,
            )

            return True

        except OSError as exc:

            print(
                "[ACTIVE PROJECT] "
                "Save failed:",
                exc,
            )

            return False

    # * ==================================================
    # * Load Global Active Project
    # * ==================================================

    def _load_active_project(
        self,
    ) -> str | None:

        if not self.GLOBAL_FILE.exists():

            return None

        try:

            with self.GLOBAL_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(
                    file,
                )

            if not isinstance(
                data,
                dict,
            ):

                return None

            project_path = data.get(
                "project_path",
            )

            if not project_path:

                return None

            return str(
                project_path,
            )

        except (
            json.JSONDecodeError,
            OSError,
        ):

            return None

    # * ==================================================
    # * Clear
    # * ==================================================

    def _clear_active_project(
        self,
    ) -> None:

        try:

            if self.GLOBAL_FILE.exists():

                self.GLOBAL_FILE.unlink()

        except OSError:

            pass