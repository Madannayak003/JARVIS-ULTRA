"""
JARVIS PRO
Developer Prompt Builder

Instruction Rules
"""

INSTRUCTION_RULES = [

    # * ---------------------------------------
    # * Generation
    # * ---------------------------------------

    "Generate only the requested project.",

    "Generate complete implementations.",

    "Do not omit requested functionality.",

    # * ---------------------------------------
    # * Structure
    # * ---------------------------------------

    "Follow the project structure exactly.",

    "Do not create, rename, or remove files or folders.",

    # * ---------------------------------------
    # * Dependencies
    # * ---------------------------------------

    "Include only required dependencies.",

    # * ---------------------------------------
    # * Restrictions
    # * ---------------------------------------

    "Do not generate Docker, CI/CD, GitHub, hidden configuration, or documentation files unless they are explicitly requested or listed in the project structure.",

]