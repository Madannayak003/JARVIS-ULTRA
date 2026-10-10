"""
JARVIS PRO
Core Package

The core package must NOT automatically import skills.

All skill modules are loaded exclusively through:

    skills.loader.load_all()

This prevents circular imports between:
    core -> skills -> voice.manager -> core
"""
