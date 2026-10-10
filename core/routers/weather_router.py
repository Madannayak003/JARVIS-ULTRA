"""
JARVIS PRO
Weather Router

Routes weather-related commands to the
existing weather skill.
"""


def weather_route(command):

    if not command:
        return None

    command = str(command).strip().lower()

    if not command:
        return None

    # * -----------------------------------------------------
    # * Current Weather
    # * -----------------------------------------------------

    if command in [
        "weather",
        "current weather",
        "check weather",
        "check the weather",
        "what is the weather",
        "what's the weather",
    ]:
        return [
            {
                "action": "weather"
            }
        ]

    # * -----------------------------------------------------
    # * Weather For Specific Location
    # * -----------------------------------------------------

    for prefix in [
        "weather in ",
        "weather for ",
        "current weather in ",
        "current weather for ",
        "check weather in ",
        "check weather for ",
    ]:

        if command.startswith(prefix):

            location = command[
                len(prefix):
            ].strip()

            if location:

                return [
                    {
                        "action": "weather",
                        "location": location,
                    }
                ]

            return None

    return None