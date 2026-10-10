import re

class Intent:

    def __init__(self, action="", target="", data=None):
        self.action = action
        self.target = target
        self.data = data or {}

    def __repr__(self):
        return f"Intent(action={self.action}, target={self.target}, data={self.data})"

def extract_intents(query):

    query = query.lower().strip()

    intents = []

    # * split multi-command
    commands = re.split(
        r"\b(?:then|and then|after that|next)\b|,",
        query
    )

    for cmd in commands:

        cmd = cmd.strip()

        if not cmd:
            continue

        # * Browser
        if "open" in cmd:

            intents.append(
                Intent(
                    action="open",
                    target=cmd.replace("open", "").strip()
                )
            )
            continue

        # * Search
        if "search" in cmd:

            intents.append(
                Intent(
                    action="search",
                    target=cmd
                )
            )
            continue

        # * Play
        if "play" in cmd:

            intents.append(
                Intent(
                    action="play",
                    target=cmd
                )
            )
            continue

        # * WhatsApp
        if "whatsapp" in cmd:

            intents.append(
                Intent(
                    action="whatsapp",
                    target=cmd
                )
            )
            continue

        intents.append(
            Intent(
                action="unknown",
                target=cmd
            )
        )

    return intents