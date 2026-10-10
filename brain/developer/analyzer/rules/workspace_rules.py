"""
JARVIS PRO
Developer Analyzer

Workspace Rules
"""

from brain.developer.enums import Workspace

WORKSPACE_RULES = {

    Workspace.PYTHON: [
        "python",
        "flask",
        "django",
        "fastapi",
    ],

    Workspace.HTML: [
        "html",
        "css",
    ],

    Workspace.JAVASCRIPT: [
        "javascript",
        "typescript",
        "react",
        "vue",
        "angular",
        "nextjs",
        "express",
    ],

    Workspace.ARDUINO: [
        "arduino",
        "uno",
        "mega",
        "nano",
    ],

    Workspace.ESP32: [
        "esp32",
        "esp8266",
        "nodemcu",
    ],

    Workspace.WEB: [
        "website",
        "web",
        "portfolio",
        "landing",
        "dashboard",
    ],
}