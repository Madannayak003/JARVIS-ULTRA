"""
JARVIS PRO
Developer Repair

Repair Parser
"""

from brain.developer.generator.parsers.response_parser import (
    ResponseParser,
)


class RepairParser(ResponseParser):
    """
    Reuses the Generator ResponseParser
    because the repair response uses the
    same  # * FILE: format.
    """

    pass