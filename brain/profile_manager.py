"""
JARVIS PRO
Stage 4 - Profile Manager

Stores permanent user profile and preferences.

Author: Madan
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict


DEFAULT_PROFILE = {
    "profile_version": 1,

    "name": "",

    "preferred_language": "English",

    "response_style": "Detailed",

    "coding_language": "Python",

    "preferred_ai": "Ollama",

    "ide": "VS Code",

    "current_project": "",

    "github": "",

    "website": "",

    "location": "",

    "hardware": {
        "laptop": "",
        "boards": []
    },

    "preferences": {},

    "created_at": "",

    "updated_at": ""
}


class ProfileManager:

    def __init__(self, profile_path="data/profile.json"):

        self.profile_path = Path(profile_path)

        self.profile_path.parent.mkdir(parents=True, exist_ok=True)

        self.profile: Dict[str, Any] = {}

        self.load()

    # * --------------------------------------------------

    def _timestamp(self):

        return datetime.now().isoformat(timespec="seconds")

    # * --------------------------------------------------

    def create_default(self):

        self.profile = DEFAULT_PROFILE.copy()

        now = self._timestamp()

        self.profile["created_at"] = now
        self.profile["updated_at"] = now

        self.save()

    # * --------------------------------------------------

    def load(self):

        if not self.profile_path.exists():

            self.create_default()

            return

        with open(self.profile_path, "r", encoding="utf8") as f:

            self.profile = json.load(f)

    # * --------------------------------------------------

    def save(self):

        self.profile["updated_at"] = self._timestamp()

        with open(self.profile_path, "w", encoding="utf8") as f:

            json.dump(
                self.profile,
                f,
                indent=4,
                ensure_ascii=False
            )

    # * --------------------------------------------------

    def get(self, key, default=None):

        return self.profile.get(key, default)

    # * --------------------------------------------------

    def set(self, key, value):

        self.profile[key] = value

        self.save()

    # * --------------------------------------------------

    def update(self, values: Dict[str, Any]):

        self.profile.update(values)

        self.save()

    # * --------------------------------------------------

    def reset(self):

        self.create_default()

    # * --------------------------------------------------

    def as_dict(self):

        return self.profile.copy()

    # * --------------------------------------------------

    def exists(self):

        return self.profile_path.exists()

    # * --------------------------------------------------

    def __contains__(self, key):

        return key in self.profile

    # * --------------------------------------------------

    def __repr__(self):

        return f"<ProfileManager user='{self.get('name','Unknown')}'>"