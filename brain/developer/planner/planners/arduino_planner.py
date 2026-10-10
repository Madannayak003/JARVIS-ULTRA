"""
JARVIS PRO
Developer Planner

Arduino Planner
"""

from brain.developer.enums import (
    Language,
    Board,
    Workspace,
)

from brain.developer.models.analysis_result import AnalysisResult
from brain.developer.planner.models.execution_plan import ExecutionPlan
from brain.developer.planner.planners.base_planner import BasePlanner


class ArduinoPlanner(BasePlanner):
    """
    Planner for Arduino IDE projects.
    """

    def can_handle(self, analysis: AnalysisResult) -> bool:

        return (

            analysis.workspace == Workspace.ARDUINO

            or analysis.board in (

                    Board.ARDUINO_UNO,
                    Board.ARDUINO_MEGA,
                    Board.ARDUINO_NANO,

                )

            or analysis.language == Language.CPP

        )

    def create_plan(self, analysis: AnalysisResult) -> ExecutionPlan:

        plan = self.create_base_plan(analysis)

        # * -------------------------------------
        # * Arduino IDE uses a flat sketch folder
        # * -------------------------------------

        plan.folders = []

        # * -------------------------------------
        # * Files
        # * -------------------------------------

        import re

        request = analysis.user_request

        # * Remove common words
        name = re.sub(

            r"\b(create|make|build|generate|develop|design|write|an|a|the|arduino|project|sketch)\b",

            "",

            request,

            flags=re.IGNORECASE,

        )

        name = re.sub(r"[^A-Za-z0-9]+", " ", name).title().replace(" ", "")

        if not name:
            name = "ArduinoProject"

        plan.project_name = name
        
        plan.notes.append(

            f"Sketch Name: {name}.ino"

        )

        plan.files = [

            f"{name}.ino",

            "README.md",

            "LICENSE",

            ".gitignore",

        ]

        # * -------------------------------------
        # * Libraries
        # * -------------------------------------

        request = analysis.user_request.lower()

        dependencies: list[str] = []

        if "rfid" in request:
            dependencies.extend([
                "SPI",
                "MFRC522",
            ])

        if "servo" in request:
            dependencies.append("Servo")
            
        if "i2c" in request:
            dependencies.append("LiquidCrystal_I2C")

        if "lcd" in request:
            dependencies.append("LiquidCrystal")

        if "oled" in request:
            dependencies.extend([
                "Adafruit_GFX",
                "Adafruit_SSD1306",
            ])

        if any(

            keyword in request

            for keyword in (

                "wifi",

                "wi-fi",

                "wi fi",

            )

        ):

            dependencies.append("WiFi")

        if any(

            keyword in request

            for keyword in (

                "bluetooth",

                "hc05",

                "hc-05",

                "hc06",

                "hc-06",

            )

        ):

            dependencies.append("SoftwareSerial")

        if "ultrasonic" in request:
            dependencies.append("NewPing")

        if "dht" in request:
            dependencies.append("DHT")

        if "ds18b20" in request:
            dependencies.extend([
                "OneWire",
                "DallasTemperature",
            ])

        if "relay" in request:
            dependencies.append("Relay")

        if "keypad" in request:
            dependencies.append("Keypad")

        if "fingerprint" in request:
            dependencies.append("Adafruit_Fingerprint")

        if "rtc" in request:
            dependencies.append("RTClib")

        if any(

            keyword in request

            for keyword in (

                "sd",

                "sd card",

                "micro sd",

                "microsd",

            )

        ):

            dependencies.append("SD")

        if "blynk" in request:
            dependencies.append("Blynk")

        if "mqtt" in request:
            dependencies.append("PubSubClient")
            
        if "bme280" in request:
            dependencies.append("Adafruit_BME280")

        if "bmp280" in request:
            dependencies.append("Adafruit_BMP280")

        if "mpu6050" in request:
            dependencies.append("MPU6050")

        if "ir" in request:
            dependencies.append("IRremote")

        if "neo6m" in request or "gps" in request:
            dependencies.append("TinyGPSPlus")

        if "nrf24" in request:
            dependencies.append("RF24")

        
        plan.dependencies = sorted(set(dependencies))

        # * -------------------------------------
        # * Tasks
        # * -------------------------------------

        plan.tasks = [

            "Generate Arduino IDE sketch",

            "Configure required hardware",

            "Include official Arduino libraries",

            "Initialize peripherals",

            "Implement setup()",

            "Implement loop()",

            "Prepare Arduino IDE project",

        ]

        # * -------------------------------------

        plan.notes.extend([

            "Generate exactly one Arduino IDE sketch (.ino).",

            "Do not generate custom library source files unless requested.",

            "Use only official Arduino libraries.",

        ])

        return plan