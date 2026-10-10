"""
JARVIS PRO
Developer Editor

Patch Writer
"""

from pathlib import Path

from brain.developer.editor.models.patch import (
    Patch,
)

from brain.developer.editor.workspace.backup_builder import (
    BackupBuilder,
)

from brain.developer.editor.workspace.patch_applier import (
    PatchApplier,
)

from brain.developer.editor.workspace.rollback_manager import (
    RollbackManager,
)


class PatchWriter:
    """
    Applies validated patches to the project.

    Creates backups before modification and
    restores modified files if the write operation
    fails.
    """

    # * --------------------------------------------------

    def __init__(self):

        self.backup_builder = BackupBuilder()

        self.applier = PatchApplier()

        self.rollback = RollbackManager()

    # * --------------------------------------------------

    def write(
        self,
        project_path: str,
        patches: list[Patch],
    ) -> list[str]:

        written = []

        root = Path(project_path)

        # * ------------------------------------------
        # * Track backups
        # * ------------------------------------------

        backups = []

        # * ------------------------------------------
        # * Track newly created files
        # * ------------------------------------------

        new_files = []

        try:

            for patch in patches:

                destination = root / patch.path

                existed = destination.exists()

                # * ----------------------------------
                # * Create folders
                # * ----------------------------------

                destination.parent.mkdir(

                    parents=True,

                    exist_ok=True,

                )

                # * ----------------------------------
                # * Backup existing file
                # * ----------------------------------

                backup_path = (

                    self.backup_builder.backup(

                        project_path,

                        patch.path,

                    )

                )

                if backup_path:

                    backups.append(

                        (
                            backup_path,
                            patch.path,
                        )

                    )

                elif not existed:

                    new_files.append(

                        patch.path

                    )

                # * ----------------------------------
                # * Apply patch
                # * ----------------------------------

                content = self.applier.apply(

                    project_path,

                    patch,

                )

                # * ----------------------------------
                # * Write
                # * ----------------------------------

                destination.write_text(

                    content,

                    encoding="utf-8",

                )

                written.append(

                    str(

                        destination.relative_to(root)

                    ).replace("\\", "/")

                )

            return written

        except Exception as error:

            print(
                "[PATCH WRITER] "
                "Write failed."
            )

            print(
                "[PATCH WRITER] "
                f"Error: {error}"
            )

            # * --------------------------------------
            # * Rollback existing files
            # * --------------------------------------

            for backup_path, target_path in reversed(

                backups

            ):

                restored = self.rollback.restore(

                    project_path,

                    backup_path,

                    target_path,

                )

                if restored:

                    print(

                        "[PATCH WRITER] "
                        f"Restored: {target_path}"

                    )

                else:

                    print(

                        "[PATCH WRITER] "
                        f"Rollback failed: {target_path}"

                    )

            # * --------------------------------------
            # * Remove newly created files
            # * --------------------------------------

            for relative_path in reversed(

                new_files

            ):

                target = root / relative_path

                try:

                    if target.exists():

                        target.unlink()

                        print(

                            "[PATCH WRITER] "
                            f"Removed new file: "
                            f"{relative_path}"

                        )

                except Exception as cleanup_error:

                    print(

                        "[PATCH WRITER] "
                        f"Could not remove new file "
                        f"{relative_path}: "
                        f"{cleanup_error}"

                    )

            # * --------------------------------------
            # * Re-raise
            # * --------------------------------------

            raise