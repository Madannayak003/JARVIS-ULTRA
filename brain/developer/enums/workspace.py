"""
Workspace Types
"""

from enum import Enum


class Workspace(str, Enum):
    PYTHON = "Python"
    WEB = "Web"
    HTML = "Html"
    JAVASCRIPT = "Javascript"
    ARDUINO = "Arduino"
    ESP32 = "ESP32"
    GENERAL = "General"
    JARVIS = "jarvis"
    