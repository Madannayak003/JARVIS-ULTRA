"""
Runtime Types
"""

from enum import Enum


class Runtime(str, Enum):
    DESKTOP = "Desktop"
    WEB = "Web"
    EMBEDDED = "Embedded"
    MOBILE = "Mobile"
    SERVER = "Server"
    UNKNOWN = "Unknown"