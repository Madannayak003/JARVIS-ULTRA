"""
JARVIS PRO
Developer Editor

Instruction Builder
"""


class InstructionBuilder:
    """
    Builds editing instructions for the LLM.
    """

    def build(self) -> str:

        return "\n".join(

            [

                "# Instructions",

                "",

                "Modify ONLY the selected files.",
                
                "Modify ONLY the code required by the user's request.",

                "Preserve all unrelated functions exactly as they are.",

                "Do NOT rewrite the entire file if only one section changes.",

                "Do NOT invent new functionality.",

                "Do NOT improve unrelated code.",

                "Do NOT remove comments unless requested.",

                "Preserve the existing coding style.",

                "Do not rewrite unrelated code.",

                "Do not modify files that are not listed.",

                "Do not rename files unless explicitly requested.",

                "Do not create new files unless explicitly requested.",

                "Do not delete code unless explicitly requested.",

                "Keep existing formatting unless the request is to format the file.",

                "",

                "# Output Format",

                "",

                "Return ONLY modified files.",
                
                "Return COMPLETE files, not snippets.",

                "For a single HTML file with embedded <style> or <script> content, return the complete HTML file after making the requested focused edit.",

                "Return NOTHING except valid '# FILE:' blocks.",

                "Do not include explanations.",

                "Do not include markdown outside file blocks.",

                "Do not include comments outside the files.",

                "Do not return unchanged files.",

                "",

                "Required format:",

                "",

                "# FILE: <relative_path>",

                "```<language>",

                "<complete modified file contents>",

                "```",

                "",

                "Example:",

                "",

                "# FILE: src/main.py",

                "```python",

                "print('Hello World')",

                "```",

            ]

        )
