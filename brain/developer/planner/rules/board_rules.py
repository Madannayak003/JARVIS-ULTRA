"""
JARVIS PRO
Developer Planner

Board Planner Rules
"""

from brain.developer.enums import Board

from brain.developer.planner.planners.arduino_planner import ArduinoPlanner
from brain.developer.planner.planners.esp32_planner import ESP32Planner


BOARD_PLANNER_RULES = {

    Board.ESP32: ESP32Planner,

    Board.ESP8266: ESP32Planner,

    Board.ARDUINO_UNO: ArduinoPlanner,

    Board.ARDUINO_MEGA: ArduinoPlanner,

}