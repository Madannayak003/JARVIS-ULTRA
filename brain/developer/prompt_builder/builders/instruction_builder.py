"""
JARVIS PRO
Developer Prompt Builder

Instruction Builder
"""

from brain.developer.prompt_builder.builders.base_builder import BaseBuilder

from brain.developer.prompt_builder.models.prompt_context import PromptContext

from brain.developer.prompt_builder.rules.instruction_rules import (
    INSTRUCTION_RULES,
)

from brain.developer.generator.rules.generator_rules import GENERATOR_RULES


class InstructionBuilder(BaseBuilder):
    """
    Builds the implementation instructions.
    """

    def build(self, context: PromptContext) -> str:

        lines = [

            "# Implementation Instructions",

            "",

        ]

        # * ------------------------------------
        # * Standard Instructions
        # * ------------------------------------

        lines.extend(INSTRUCTION_RULES)

        lines.append("")

        # * ------------------------------------
        # * Arduino Instructions
        # * ------------------------------------

        if context.analysis.workspace.name == "ARDUINO":

            lines.extend([

                "# Arduino Rules",

                "",

                "Generate an Arduino IDE project.",

                "Generate exactly ONE Arduino sketch (.ino).",

                "The sketch filename MUST match the project filename.",

                "Do NOT generate .cpp, .c, .h or library source files unless explicitly requested by the user.",

                "Use ONLY official Arduino libraries.",

                "Never generate the source code of existing Arduino libraries.",

                "Include only the required #include statements.",

                "Generate production-ready Arduino code that compiles in Arduino IDE.",

                "Do not invent classes or APIs that do not exist.",

                "Configure all required pins.",

                "Implement setup() and loop().",

                "List every required Arduino library in README.md.",

                "Include wiring connections in README.md.",

                "Do not use PlatformIO structure.",

                "Do not create src/, include/, lib/, libraries/, or test folders.",

                "",

                "Official library examples:",

                "RFID -> SPI.h + MFRC522.h",

                "Servo -> Servo.h",

                "LCD I2C -> Wire.h + LiquidCrystal_I2C.h",

                "OLED SSD1306 -> Wire.h + Adafruit_GFX.h + Adafruit_SSD1306.h",

                "DHT11/DHT22 -> DHT.h",

                "Ultrasonic -> NewPing.h",

                "Bluetooth HC-05 -> SoftwareSerial.h",

                "WiFi ESP8266 -> ESP8266WiFi.h",

                "WiFi ESP32 -> WiFi.h",

                "",

            ])

        # * ------------------------------------
        # * User Request
        # * ------------------------------------

        lines.append("# User Request")

        lines.append("")

        lines.append(context.user_request)

        lines.append("")

        # * ------------------------------------
        # * Output Format
        # * ------------------------------------

        lines.append(GENERATOR_RULES.strip())

        return "\n".join(lines)