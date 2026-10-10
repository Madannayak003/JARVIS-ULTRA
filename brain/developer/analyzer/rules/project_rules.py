"""
JARVIS PRO
Developer Analyzer

Project Rules
"""

from brain.developer.enums import ProjectType


PROJECT_RULES = {

    ProjectType.CONSOLE: [
        "console",
        "terminal",
        "cli",
        "command",
    ],

    ProjectType.GUI: [
        "gui",
        "desktop",
        "window",
        "tkinter",
        "pyqt",
        "pyside",
        "qt",
    ],

    ProjectType.WEBSITE: [
        "website",
        "web",
        "portfolio",
        "landing",
        "dashboard",
        "frontend",
        "page",
    ],

    ProjectType.API: [
        "api",
        "backend",
        "server",
        "rest",
    ],

    ProjectType.IOT: [
        "iot",
        "arduino",
        "esp32",
        "esp8266",
        "nodemcu",
        "sensor",
        "robot",
    ],

    ProjectType.LIBRARY: [
        "library",
        "package",
        "module",
        "sdk",
    ],

    ProjectType.AUTOMATION: [
        "automation",
        "bot",
        "scraper",
        "crawler",
        "automation script",
    ],

    ProjectType.SCRIPT: [
        "script",
    ],
}