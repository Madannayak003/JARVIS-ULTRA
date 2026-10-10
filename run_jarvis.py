"""Launch JARVIS and preserve startup failures from the windowless shortcut."""

from __future__ import annotations

import runpy
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

from config.settings import get_assistant_display_name


PROJECT_ROOT = Path(__file__).resolve().parent
LOG_PATH = PROJECT_ROOT / "data" / "logs" / "shortcut_startup.log"


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with LOG_PATH.open("a", encoding="utf-8", buffering=1) as log_file:
        log_file.write(
            f"\n[{datetime.now().isoformat(timespec='seconds')}] "
            f"{get_assistant_display_name()} shortcut launched\n"
        )

        with redirect_stdout(log_file), redirect_stderr(log_file):
            try:
                runpy.run_path(str(PROJECT_ROOT / "main.py"), run_name="__main__")
            except SystemExit as error:
                return int(error.code or 0)
            except Exception:
                log_file.write("[SHORTCUT] Startup failed\n")
                traceback.print_exc(file=log_file)
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
