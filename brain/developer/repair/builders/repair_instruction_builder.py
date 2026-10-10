"""
JARVIS PRO
Developer Repair

Repair Instruction Builder
"""

from .base_builder import BaseBuilder


class RepairInstructionBuilder(BaseBuilder):

    def build(self, request):

        return "\n".join(

            [

                "# Instructions",

                "",

                "Generate ONLY the missing files.",

                "Do NOT regenerate existing files.",

                "Return ONLY valid '# FILE:' blocks.",

                "Do NOT explain anything.",

            ]

        )