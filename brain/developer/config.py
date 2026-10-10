"""
JARVIS PRO
Developer

Configuration
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WORKSPACE_ROOT = PROJECT_ROOT / "workspace"

AUTO_SAVE = True

OVERWRITE_EXISTING = False

CREATE_BACKUP = False

DEFAULT_AI_MODEL = "jarvis"