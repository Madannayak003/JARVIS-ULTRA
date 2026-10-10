"""
Project Types
"""

from enum import Enum


class ProjectType(str, Enum):
    CONSOLE = "Console"
    GUI = "GUI"
    WEBSITE = "Website"
    API = "API"
    IOT = "IoT"
    LIBRARY = "Library"
    AUTOMATION = "Automation"
    SCRIPT = "Script"
    UNKNOWN = "Unknown"