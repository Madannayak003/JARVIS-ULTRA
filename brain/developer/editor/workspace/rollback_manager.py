"""
JARVIS PRO
Developer Editor

Rollback Manager
"""

from pathlib import Path
import shutil


class RollbackManager:
    """
    Restores project files from backups.
    """

    # * --------------------------------------------------

    def restore(
        self,
        project_path: str,
        backup_path: str,
        target_path: str,
    ) -> bool:

        project = Path(project_path)

        backup = project / backup_path

        target = project / target_path

        if not backup.exists():

            return False

        target.parent.mkdir(

            parents=True,

            exist_ok=True,

        )

        shutil.copy2(

            backup,

            target,

        )

        return True