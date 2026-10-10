"""
JARVIS PRO
Developer Editor

Backup Builder
"""

from pathlib import Path
from datetime import datetime


class BackupBuilder:
    """
    Creates backups before files
    are modified.
    """

    BACKUP_FOLDER = ".jarvis_backups"

    # * --------------------------------------------------

    def backup(
        self,
        project_path: str,
        relative_path: str,
    ) -> str | None:

        project = Path(project_path)

        source = project / relative_path

        if not source.exists():

            return None

        backup_root = project / self.BACKUP_FOLDER

        backup_root.mkdir(

            parents=True,

            exist_ok=True,

        )

        timestamp = datetime.now().strftime(

            "%Y%m%d_%H%M%S"

        )

        backup_name = (

            relative_path.replace("/", "__")

            + "_"

            + timestamp

        )

        destination = backup_root / backup_name

        destination.parent.mkdir(

            parents=True,

            exist_ok=True,

        )

        destination.write_text(

            source.read_text(

                encoding="utf-8",

            ),

            encoding="utf-8",

        )

        return str(

            destination.relative_to(project)

        ).replace("\\", "/")