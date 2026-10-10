"""Read-only Workspace / Project Center services for the local HUD.

This module intentionally sits beside the developer workspace engine.  It only
discovers existing projects and owns static preview servers started by the HUD.
It does not create, edit, move, or delete project files.
"""

from __future__ import annotations

import functools
import http.server
import os
import platform
import socket
import shutil
import subprocess
import threading
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    # * Keep the developer configuration authoritative when the full runtime is
    # * available.  The fallback also keeps this read-only HUD module usable in
    # * lightweight diagnostics where optional runtime dependencies are absent.
    from brain.developer.config import WORKSPACE_ROOT
except (ImportError, OSError):
    WORKSPACE_ROOT = Path(__file__).resolve().parents[1] / "workspace"


_IGNORED_NAMES = {".git", ".venv", "venv", "node_modules", "__pycache__"}
_CATEGORY_NAMES = {"arduino", "esp32", "general", "html", "javascript", "python", "web", "jarvis"}


def _safe_modified(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return ""


def _files(path: Path, limit: int = 250) -> list[Path]:
    result: list[Path] = []
    try:
        for item in path.rglob("*"):
            if len(result) >= limit:
                break
            if any(part in _IGNORED_NAMES for part in item.parts):
                continue
            if item.is_file():
                result.append(item)
    except OSError:
        pass
    return result


def _detect_type(path: Path, category: str) -> tuple[str, str]:
    files = _files(path)
    names = {item.name.casefold() for item in files}
    suffixes = {item.suffix.casefold() for item in files}
    if "platformio.ini" in names or ".ino" in suffixes:
        return ("ESP32" if "platformio.ini" in names else "Arduino", "")
    entry = next((item for item in files if item.name.casefold() == "index.html"), None)
    if entry:
        return ("HTML", str(entry.relative_to(path)))
    if "package.json" in names or suffixes & {".js", ".jsx", ".ts", ".tsx"}:
        return ("JavaScript", "")
    if suffixes & {".html", ".htm", ".css"}:
        return ("HTML", "")
    if "pyproject.toml" in names or "requirements.txt" in names or ".py" in suffixes:
        return ("Python", "")
    category_map = {"html": "HTML", "javascript": "JavaScript", "python": "Python", "arduino": "Arduino", "esp32": "ESP32", "web": "Web", "general": "General"}
    return (category_map.get(category.casefold(), "General"), "")


def _project_id(path: Path) -> str:
    return str(path.resolve())


def _resolve_project(project_id: str, workspace_root: Path) -> Path | None:
    candidate = Path(project_id).resolve()
    root = workspace_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.is_dir() else None


class _Preview:
    def __init__(self, root: Path, server: http.server.ThreadingHTTPServer, thread: threading.Thread):
        self.root, self.server, self.thread = root, server, thread
        self.url = f"http://127.0.0.1:{server.server_port}/"


class WorkspaceCenter:
    def __init__(self, workspace_root: Path | str | None = None):
        self.workspace_root = Path(workspace_root or WORKSPACE_ROOT).resolve()
        self._previews: dict[str, _Preview] = {}
        self._lock = threading.RLock()

    def _roots(self) -> list[tuple[Path, str]]:
        if not self.workspace_root.is_dir():
            return []
        roots: list[tuple[Path, str]] = []
        try:
            children = sorted(self.workspace_root.iterdir(), key=lambda item: item.name.casefold())
        except OSError:
            return []
        for child in children:
            if not child.is_dir() or child.name.casefold() in _IGNORED_NAMES:
                continue
            if child.name.casefold() in _CATEGORY_NAMES:
                try:
                    roots.extend((item, child.name) for item in sorted(child.iterdir(), key=lambda item: item.name.casefold()) if item.is_dir())
                except OSError:
                    continue
            else:
                roots.append((child, "General"))
        return roots

    def _resolve(self, project_id: str) -> Path | None:
        return _resolve_project(project_id, self.workspace_root)

    def _payload(self, path: Path, category: str) -> dict[str, Any]:
        project_type, entry = _detect_type(path, category)
        with self._lock:
            preview = self._previews.get(_project_id(path))
        return {
            "id": _project_id(path), "name": path.name, "type": project_type,
            "location": str(path), "last_modified": _safe_modified(path),
            "entry_file": entry, "preview_available": project_type == "HTML" and bool(entry),
            "preview_running": bool(preview and preview.thread.is_alive()),
            "preview_url": preview.url if preview and preview.thread.is_alive() else "",
        }

    def list_projects(self) -> dict[str, Any]:
        projects = [self._payload(path, category) for path, category in self._roots()]
        return {"ok": True, "workspace": str(self.workspace_root), "projects": projects}

    def detail(self, project_id: str) -> dict[str, Any] | None:
        project = self._resolve(project_id)
        if not project:
            return None
        category = project.parent.name
        return self._payload(project, category)

    def start_preview(self, project_id: str, open_external: bool = False) -> dict[str, Any]:
        project = self._resolve(project_id)
        if not project:
            return {"ok": False, "error": "Project folder is no longer available."}
        data = self._payload(project, project.parent.name)
        if not data["preview_available"]:
            return {"ok": False, "error": "HTML preview is not available for this project."}
        key = _project_id(project)
        with self._lock:
            existing = self._previews.get(key)
            if existing and existing.thread.is_alive():
                data.update(preview_running=True, preview_url=existing.url)
                if open_external:
                    self._open(existing.url)
                return {"ok": True, "project": data}
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(project))
            try:
                server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            except OSError:
                return {"ok": False, "error": "No local preview port is available."}
            thread = threading.Thread(target=server.serve_forever, name=f"jarvis-preview-{project.name}", daemon=True)
            preview = _Preview(project, server, thread)
            self._previews[key] = preview
            thread.start()
        if open_external:
            self._open(preview.url)
        data.update(preview_running=True, preview_url=preview.url)
        return {"ok": True, "project": data}

    def _open(self, url: str) -> None:
        try:
            from skills.browser.browser_controller import browser
            browser.open(url)
        except Exception:
            webbrowser.open(url)

    def open_externally(self, project_id: str) -> dict[str, Any]:
        project = self._resolve(project_id)
        if not project:
            return {"ok": False, "error": "Project folder is no longer available."}
        with self._lock:
            preview = self._previews.get(_project_id(project))
        if not preview or not preview.thread.is_alive():
            return {"ok": False, "error": "Start the local preview before opening it externally."}
        self._open(preview.url)
        return {"ok": True, "preview_url": preview.url}

    def stop_preview(self, project_id: str) -> dict[str, Any]:
        key = _project_id(Path(project_id).resolve())
        with self._lock:
            preview = self._previews.pop(key, None)
        if preview:
            preview.server.shutdown()
            preview.server.server_close()
        project = self._resolve(project_id)
        return {"ok": True, "project": self._payload(project, project.parent.name) if project else {"preview_running": False, "preview_url": ""}}

    def open_folder(self, project_id: str) -> dict[str, Any]:
        project = self._resolve(project_id)
        if not project:
            return {"ok": False, "error": "Project folder is no longer available."}
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(project))
            else:
                return {"ok": False, "error": "Windows Explorer is unavailable."}
        except OSError:
            return {"ok": False, "error": "Unable to open the project folder."}
        return {"ok": True, "location": str(project)}

    def open_in_vscode(self, project_id: str) -> dict[str, Any]:
        """Open one recognized workspace project in VS Code."""

        project = self._resolve(project_id)
        if project is None:
            return {"ok": False, "error": "Project folder is no longer available."}

        listed_projects = {path.resolve() for path, _ in self._roots()}
        if project not in listed_projects:
            return {"ok": False, "error": "Only recognized workspace projects can be opened."}

        abs_folder = str(project.resolve())
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
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except OSError:
            return {"ok": False, "error": "Unable to open the project in VS Code."}

        return {"ok": True, "location": abs_folder}

    def delete_project(self, project_id: str) -> dict[str, Any]:
        """Delete one listed project after strict workspace validation."""

        raw_candidate = Path(str(project_id)).expanduser()
        project = self._resolve(raw_candidate.as_posix())
        root = self.workspace_root.resolve()

        if project is None or project == root:
            return {"ok": False, "error": "Project is outside the configured workspace."}

        try:
            project.relative_to(root)
        except ValueError:
            return {"ok": False, "error": "Project is outside the configured workspace."}

        # Only a project currently exposed by Workspace Center may be deleted.
        listed_projects = {path.resolve() for path, _ in self._roots()}
        if project not in listed_projects:
            return {"ok": False, "error": "Only recognized workspace projects can be deleted."}

        # Reject symlinked targets/components so a client cannot redirect the
        # deletion outside the configured workspace.
        raw_absolute = raw_candidate.absolute()
        try:
            relative_parts = raw_absolute.relative_to(root).parts
        except ValueError:
            return {"ok": False, "error": "Project is outside the configured workspace."}
        current = root
        for part in relative_parts:
            current = current / part
            if current.is_symlink():
                return {"ok": False, "error": "Symlinked project paths cannot be deleted."}

        try:
            from brain.developer.integration.active_project import ActiveProjectResolver

            active_project = ActiveProjectResolver().resolve()
        except Exception:
            active_project = None

        if active_project and Path(active_project).resolve() == project:
            return {"ok": False, "error": "Active project cannot be deleted."}

        self.stop_preview(str(project))

        try:
            shutil.rmtree(project)
        except OSError:
            return {"ok": False, "error": "Unable to delete the project directory."}

        return {"ok": True, "deleted": str(project)}


workspace_center = WorkspaceCenter()
