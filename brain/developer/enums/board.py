"""
Development Boards
"""

from enum import Enum


class Board(str, Enum):
    ARDUINO_UNO = "Arduino Uno"
    ARDUINO_MEGA = "Arduino Mega"
    ESP32 = "ESP32"
    ESP8266 = "ESP8266"
    NODEMCU = "NodeMCU"
    RASPBERRY_PI = "Raspberry Pi"
    NONE = "None"