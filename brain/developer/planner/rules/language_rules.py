"""
JARVIS PRO
Developer Planner

Language Planner Rules
"""

from brain.developer.enums import Language

from brain.developer.planner.planners.python_planner import PythonPlanner
from brain.developer.planner.planners.javascript_planner import JavaScriptPlanner
from brain.developer.planner.planners.cpp_planner import CppPlanner


LANGUAGE_PLANNER_RULES = {

    Language.PYTHON: PythonPlanner,

    Language.JAVASCRIPT: JavaScriptPlanner,

    Language.TYPESCRIPT: JavaScriptPlanner,

    Language.CPP: CppPlanner,

    Language.C: CppPlanner,

}