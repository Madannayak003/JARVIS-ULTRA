MEDIA = {

    # * ---------- Volume ----------

    "volume up": {
        "action": "volume",
        "direction": "up"
    },

    "increase volume": {
        "action": "volume",
        "direction": "up"
    },

    "raise volume": {
        "action": "volume",
        "direction": "up"
    },

    "volume down": {
        "action": "volume",
        "direction": "down"
    },

    "decrease volume": {
        "action": "volume",
        "direction": "down"
    },

    "lower volume": {
        "action": "volume",
        "direction": "down"
    },

    "mute": {
        "action": "volume",
        "direction": "mute"
    },

    "mute volume": {
        "action": "volume",
        "direction": "mute"
    },

    # * ---------- Clipboard ----------

    "read clipboard": {
        "action": "clipboard",
        "mode": "read"
    },

    "show clipboard": {
        "action": "clipboard",
        "mode": "read"
    },

    "explain clipboard": {
        "action": "clipboard",
        "mode": "explain"
    },

    "summarize clipboard": {
        "action": "clipboard",
        "mode": "summary"
    },

    # * ---------- Screenshot ----------

    "analyze screenshot": {
        "action": "screenshot_ai"
    },

    "describe screenshot": {
        "action": "screenshot_ai"
    }

}


def media_route(command):

    command = command.lower().strip()

    # * -------------------------------------------------
    # * Exact media commands
    # * -------------------------------------------------

    if command in MEDIA:
        return [MEDIA[command]]

    # * -------------------------------------------------
    # * Image generation
    # * -------------------------------------------------

    image_prefixes = (
        "create an image of ",
        "create image of ",
        "create an image ",
        "create image ",
        "create image of ",
        "generate an image of ",
        "generate image of ",
        "generate an image ",
        "generate image ",
        "make an image of ",
        "make image of ",
        "make an image ",
        "make image ",
        "draw an image of ",
        "draw image of ",
        "draw an image ",
        "draw image ",
    )

    for prefix in image_prefixes:

        if command.startswith(prefix):

            prompt = command[
                len(prefix):
            ].strip()

            if not prompt:
                return None

            return [
                {
                    "action": "create_image",
                    "prompt": prompt,
                }
            ]

    return None