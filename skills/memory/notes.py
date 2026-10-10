"""
JARVIS PRO
Notes Skill

Handles quick personal notes.
"""

import json
from pathlib import Path

from core.registry import register
from voice.manager import speak


# * =========================================================
# * Storage
# * =========================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

NOTES_FILE = DATA_DIR / "notes.json"


# * =========================================================
# * Storage Helpers
# * =========================================================

def _load_notes():

    if not NOTES_FILE.exists():
        return []

    try:

        with open(
            NOTES_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if isinstance(data, list):
            return data

    except Exception as e:

        print(
            f"[NOTES ERROR] Load failed: {e}"
        )

    return []


def _save_notes(notes):

    try:

        with open(
            NOTES_FILE,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                notes,
                f,
                indent=4,
                ensure_ascii=False,
            )

        return True

    except Exception as e:

        print(
            f"[NOTES ERROR] Save failed: {e}"
        )

        return False


# * =========================================================
# * Create Note
# * =========================================================

def create_note(data=None):

    data = data or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:

        speak(
            "What would you like me to note?"
        )

        return False

    notes = _load_notes()

    notes.append(
        {
            "text": text,
        }
    )

    if not _save_notes(notes):

        speak(
            "I couldn't save that note."
        )

        return False

    print(
        f"[NOTES] Saved: {text}"
    )

    speak(
        "I've saved that note."
    )

    return True


# * =========================================================
# * List Notes
# * =========================================================

def list_notes(data=None):

    notes = _load_notes()

    if not notes:

        speak(
            "You don't have any saved notes."
        )

        return True

    print("\n[NOTES]")

    for index, note in enumerate(
        notes,
        start=1,
    ):

        print(
            f"{index}. {note.get('text', '')}"
        )

    speak(
        f"You have {len(notes)} saved notes."
    )

    return True


def get_latest_note():
    """Return the most recently stored note without speaking.

    Notes currently have no timestamp field, so append order is the existing
    source of truth for which note is latest.
    """
    notes = _load_notes()
    for note in reversed(notes):
        if isinstance(note, dict) and str(note.get("text", "")).strip():
            return note
    return None


# * =========================================================
# * Clear Notes
# * =========================================================

def clear_notes(data=None):

    if not _save_notes([]):

        speak(
            "I couldn't clear your notes."
        )

        return False

    speak(
        "All notes have been cleared."
    )

    return True


# * =========================================================
# * Registry
# * =========================================================

register(
    "create_note",
    create_note,
)

register(
    "list_notes",
    list_notes,
)

register(
    "clear_notes",
    clear_notes,
)
