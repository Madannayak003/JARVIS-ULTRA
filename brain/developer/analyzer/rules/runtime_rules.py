"""
JARVIS PRO
Developer Analyzer

Runtime Rules
"""

from brain.developer.enums import Runtime


RUNTIME_RULES = {

    Runtime.DESKTOP: [
        "desktop",
        "gui",
        "window",
        "tkinter",
        "pyqt",
        "pyside",
    ],

    Runtime.WEB: [
        "website",
        "web",
        "html",
        "css",
        "javascript",
        "react",
        "vue",
        "angular",
        "nextjs",
    ],

    Runtime.SERVER: [
        "api",
        "backend",
        "server",
        "flask",
        "django",
        "fastapi",
        "express",
    ],

    Runtime.EMBEDDED: [
        "arduino",
        "esp32",
        "esp8266",
        "nodemcu",
        "sensor",
        "iot",
        "robot",
    ],

    Runtime.MOBILE: [
        "android",
        "ios",
        "flutter",
        "dart",
        "kotlin",
        "swift",
        "reactnative",
    ],
}