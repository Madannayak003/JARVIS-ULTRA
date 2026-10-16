"""Legacy voice launcher for the online JARVIS runtime.

The primary application uses Gemini Live and does not switch to a second
conversation engine when connectivity fails.
"""


def run():
    print(
        "[VOICE LAUNCHER] "
        "Starting the configured Gemini Live-capable online voice..."
    )

    from voice.online_runner import run as online_run

    return online_run()


if __name__ == "__main__":
    run()
