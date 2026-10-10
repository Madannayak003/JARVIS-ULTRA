"""
JARVIS PRO
Developer Workspace

Workspace Resolver
"""

from pathlib import Path


class WorkspaceResolver:
    """
    Resolves the correct workspace directory
    based on the analyzed workspace.
    """

    ROOT = Path("workspace")

    MAP = {

        "PYTHON": "Python",

        "HTML": "Html",

        "JAVASCRIPT": "Javascript",

        "WEBSITE": "Web",

        "REACT": "Web",

        "NEXTJS": "Web",

        "ESP32": "ESP32",

        "ARDUINO": "Arduino",

    }

    def resolve(self, workspace) -> Path:

        key = str(workspace).split(".")[-1].upper()

        folder = self.MAP.get(

            key,

            "General",

        )

        return self.ROOT / folder