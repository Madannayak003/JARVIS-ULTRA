"""
JARVIS PRO
Developer Analyzer

Board Rules
"""

from brain.developer.enums import Board


BOARD_RULES = {

    Board.ARDUINO_UNO: [
        "arduino uno",
        "uno",
    ],

    Board.ARDUINO_MEGA: [
        "arduino mega",
        "mega",
    ],

    Board.ESP32: [
        "esp32",
    ],

    Board.ESP8266: [
        "esp8266",
    ],

    Board.NODEMCU: [
        "nodemcu",
        "node mcu",
    ],

    Board.RASPBERRY_PI: [
        "raspberry",
        "raspberrypi",
        "raspberry pi",
    ],
}