"""
JARVIS PRO
Developer Generator

Generator Rules
"""

GENERATOR_RULES = "\n".join(

    [

        "# Output Format",

        "",

        "Return ONLY the requested project files.",

        "Return NOTHING except valid '# FILE:' blocks.",

        "Do not include explanations, markdown text, or comments outside file blocks.",

        "Generate every required file exactly once.",

        "Do not omit requested files.",

        "Do not generate extra files.",

        "Do not rename files.",

        "",

        "Required format:",

        "",

        "# FILE: <relative_path>",

        "```<language>",

        "<complete file contents>",

        "```",

        "",

        "Example:",

        "",

        "# FILE: example.py",

        "```python",

        "print('Hello World')",

        "```",

    ]

)