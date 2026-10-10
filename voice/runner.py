"""Legacy voice launcher for the online JARVIS runtime.

The primary application no longer probes connectivity and silently switches
to an offline AI assistant.  Offline modules remain isolated for regression
coverage and explicit maintenance, but they are not an automatic runtime
fallback.
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
