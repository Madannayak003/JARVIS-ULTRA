"""
JARVIS PRO
Developer Planner

Planner Rules
"""

from .board_rules import BOARD_PLANNER_RULES
from .framework_rules import FRAMEWORK_PLANNER_RULES
from .language_rules import LANGUAGE_PLANNER_RULES

from brain.developer.enums import Workspace

from brain.developer.planner.planners.arduino_planner import ArduinoPlanner

__all__ = [

    "BOARD_PLANNER_RULES",

    "FRAMEWORK_PLANNER_RULES",

    "LANGUAGE_PLANNER_RULES",

]

WORKSPACE_PLANNER_RULES = {

    Workspace.ARDUINO: ArduinoPlanner,

}