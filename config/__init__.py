"""JARVIS configuration package."""

from .environment import load_environment


# * Load .env once when the configuration package is first imported.
load_environment()
