"""
JARVIS PRO
Developer Analyzer

Framework Rules
"""

from brain.developer.enums import Framework


FRAMEWORK_RULES = {

    Framework.FLASK: [
        "flask",
    ],

    Framework.DJANGO: [
        "django",
    ],

    Framework.FASTAPI: [
        "fastapi",
        "fast-api",
    ],

    Framework.REACT: [
        "react",
        "reactjs",
        "react.js",
    ],

    Framework.VUE: [
        "vue",
        "vuejs",
        "vue.js",
    ],

    Framework.ANGULAR: [
        "angular",
    ],

    Framework.NEXTJS: [
        "nextjs",
        "next.js",
    ],

    Framework.EXPRESS: [
        "express",
        "expressjs",
        "express.js",
    ],
}