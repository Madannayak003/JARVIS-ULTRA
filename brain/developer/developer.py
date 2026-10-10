"""
JARVIS PRO
Developer

Public API
"""

import os
import platform
import shutil
import subprocess
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from brain.developer.editor.editor import (
    Editor,
)

from brain.developer.memory.developer_memory import (
    DeveloperMemory,
)

from brain.developer.memory.models.edit_record import (
    EditRecord,
)

from brain.developer.pipeline import (
    DeveloperPipeline,
)
from hud.integration import HUDIntegration
from hud.web_bridge import hud_web


def _launch_project_assets(folder_path: str) -> None:
    """
    1. Opens HTML files in default browser.
    3. Conforms sketch folder structure and silently launches Arduino IDE without terminal spam.
    """
    if not folder_path or not os.path.exists(folder_path):
        return

    sys_platform = platform.system()
    abs_folder = os.path.abspath(folder_path)

    # * 1. Collect project files
    html_files = []
    ino_files = []

    for root, _, files in os.walk(abs_folder):
        for file in files:
            full_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            if ext == ".html":
                html_files.append(full_path)
            elif ext == ".ino":
                ino_files.append(full_path)

    # * 2. Launch HTML in browser (prefer index.html)
    if html_files:
        target_html = next(
            (f for f in html_files if os.path.basename(f).lower() == "index.html"),
            html_files[0]
        )
        try:
            webbrowser.open(Path(target_html).as_uri())
        except Exception:
            pass

    # * 3. Launch Arduino / ESP sketch cleanly
    if ino_files:
        target_ino = ino_files[0]
        sketch_name = os.path.splitext(os.path.basename(target_ino))[0]
        parent_dir = os.path.dirname(target_ino)
        parent_name = os.path.basename(parent_dir)

        # * Ensure folder name matches .ino file so Arduino IDE doesn't show moving popup
        if parent_name != sketch_name:
            proper_dir = os.path.join(parent_dir, sketch_name)
            os.makedirs(proper_dir, exist_ok=True)
            new_ino_path = os.path.join(proper_dir, os.path.basename(target_ino))
            shutil.move(target_ino, new_ino_path)
            target_ino = new_ino_path

        if sys_platform == "Windows":
            # * DETACHED_PROCESS (0x00000008) + CREATE_NEW_PROCESS_GROUP (0x00000200)
            DETACHED_FLAGS = 0x00000008 | 0x00000200

            # * Use 'cmd /c start' to launch completely detached from terminal IO
            subprocess.Popen(
                f'cmd.exe /c start "" "{target_ino}"',
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=DETACHED_FLAGS,
                close_fds=True,
            )
        elif sys_platform == "Darwin":
            subprocess.Popen(
                ["open", "-a", "Arduino IDE", target_ino],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                ["arduino", target_ino],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


class Developer:
    """
    Public entry point for the Developer subsystem.
    """

    def __init__(self):
        self.editor = Editor()
        self.pipeline = DeveloperPipeline()
        self.memory = DeveloperMemory()

    def execute(
        self,
        user_request: str,
        project_path: str = "",
    ):
        if not user_request:
            return None

        analysis = self.pipeline.analyzer.analyze(
            user_request,
        )

        intent = getattr(
            analysis,
            "intent",
            None,
        )

        intent_name = getattr(
            intent,
            "name",
            str(intent),
        )

        if intent_name == "CREATE":
            context = self.pipeline.process(
                user_request,
            )

            result = context.workspace_result

            if result is None:
                return None

            if (
                result.success
                and result.project_path
            ):
                project_path = str(
                    result.project_path
                )

                self.memory.configure(
                    project_path,
                )
                self.memory.load()
                self.memory.update_session(
                    "project_path",
                    project_path,
                )
                self.memory.add_project(
                    "name",
                    result.project_name,
                )
                self.memory.add_project(
                    "path",
                    project_path,
                )
                self.memory.save()

                _launch_project_assets(project_path)
                _request_vscode_permission(
                    project_path,
                    result.project_name or os.path.basename(project_path),
                )

            return result

        if not project_path:
            return None

        self.memory.configure(
            project_path,
        )
        self.memory.load()
        self.memory.update_session(
            "project_path",
            project_path,
        )

        result = self.editor.execute(
            user_request,
            project_path,
        )

        files = [
            patch.path
            for patch in result.patches
        ] if result is not None else []

        edit_type = ""
        try:
            edit_type = (
                self.editor.analyzer._detect_action(
                    user_request,
                )
            )
        except Exception:
            edit_type = ""

        record = EditRecord(
            request=user_request,
            edit_type=edit_type,
            files=files,
            timestamp=datetime.now(
                timezone.utc,
            ).isoformat(),
            success=(
                result.success
                if result is not None
                else False
            ),
            notes=(
                result.message
                if result is not None
                else "Developer execution failed."
            ),
        )

        self.memory.add_edit(
            record.__dict__,
        )
        self.memory.save()

        return result


def _request_vscode_permission(folder_path: str, project_name: str) -> None:
    abs_folder = os.path.abspath(folder_path)

    def handle_action(action: str) -> None:
        if action != "open":
            return
        try:
            if platform.system() == "Windows":
                subprocess.Popen(
                    ["cmd.exe", "/c", "code", abs_folder],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                subprocess.Popen(
                    ["code", abs_folder],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            HUDIntegration.system_activity(
                f"Opened {project_name} in VS Code."
            )
        except Exception:
            pass

    action_id = hud_web.register_action(handle_action)
    HUDIntegration.activity_action(
        "Open this project in VS Code?",
        [
            {"id": action_id, "label": "OPEN IN VS CODE", "action": "open"},
            {"id": action_id, "label": "CANCEL", "action": "cancel"},
        ],
    )
