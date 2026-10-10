"""
JARVIS PRO
Browser Router

Routes normal browser websites, searches,
and Windows applications.

Personal/custom web destinations are handled
by web_router.py and must not be duplicated here.
"""

import re

# * =========================================================
# * Windows Applications
# * =========================================================

WINDOWS_APPS = [
    "notepad",
    "calculator",
    "calc",
    "paint",
    "cmd",
    "command prompt",
    "powershell",
    "explorer",
    "file explorer",
    "task manager",
    "registry editor",
    "device manager",
    "control panel",
    "settings",
]


# * =========================================================
# * Browser Websites
# * =========================================================

BROWSER_SITES = [
    "google",
    "youtube",
    "chrome",
    "gmail",
    "github",
    "spotify",
    "chatgpt",
]


# * =========================================================
# * Browser Router
# * =========================================================

def browser_route(command):

    if not command:
        return None

    command = str(command).strip().lower()
    
    # * -----------------------------------------------------
    # * Google Maps
    # * -----------------------------------------------------

    if command in [
        "maps",
        "open maps",
        "open google maps",
        "google maps",
    ]:
        return [
            {
                "action": "maps_open"
            }
        ]

    # * -----------------------------------------------------
    # * Google Maps Directions
    # * -----------------------------------------------------
    
    # * -----------------------------------------------------
    # * Google Maps Directions - Origin to Destination
    # * -----------------------------------------------------

    for prefix in [
        "navigate from ",
        "directions from ",
        "route from ",
        "go from ",
    ]:

        if command.startswith(prefix):

            route = command[
                len(prefix):
            ].strip()

            if " to " not in route:
                return None

            origin, destination = route.split(
                " to ",
                1
            )

            origin = origin.strip()
            destination = destination.strip()

            if origin and destination:

                return [
                    {
                        "action": "maps_directions",
                        "origin": origin,
                        "destination": destination,
                    }
                ]

            return None

    for prefix in [
        "navigate to ",
        "directions to ",
        "route to ",
        "go to ",
    ]:

        if command.startswith(prefix):

            destination = command[
                len(prefix):
            ].strip()

            if destination:

                return [
                    {
                        "action": "maps_directions",
                        "destination": destination,
                    }
                ]

            return None
        
    # * -----------------------------------------------------
    # * Google Translate Text
    # * -----------------------------------------------------

    if command.startswith("translate ") and " to " in command:

        translation = command[
            len("translate "):
        ].strip()

        text, target = translation.rsplit(
            " to ",
            1
        )

        text = text.strip()
        target = target.strip()

        if text and target:

            return [
                {
                    "action": "translate_text",
                    "text": text,
                    "target": target,
                }
            ]

        return None
        
    # * -----------------------------------------------------
    # * Google Translate
    # * -----------------------------------------------------

    if command in [
        "translate",
        "open translate",
        "google translate",
        "open google translate",
    ]:
        return [
            {
                "action": "translate_open"
            }
        ]

    if not command:
        return None

    # * -----------------------------------------------------
    # * Open Google Search
    # * -----------------------------------------------------

    if command.startswith("open google search"):

        query = command.replace(
            "open google search",
            "",
            1
        ).strip()

        return [
            {
                "action": "open",
                "app": "google"
            },
            {
                "action": "google_search",
                "query": query
            }
        ]

    # * -----------------------------------------------------
    # * Open YouTube Search
    # * -----------------------------------------------------

    if command.startswith("open youtube search"):

        query = command.replace(
            "open youtube search",
            "",
            1
        ).strip()

        return [
            {
                "action": "open",
                "app": "youtube"
            },
            {
                "action": "youtube_search",
                "query": query
            }
        ]
        
    
    # * -----------------------------------------------------
    # * Google Search
    # * -----------------------------------------------------

    # Natural variants used by the compatibility command path.  Keep the
    # provider explicit here so generic file searches remain file-owned.
    match = re.fullmatch(
        r"(?:google\s+search|search\s+google)\s+(?:for\s+)?(.+)",
        command,
        re.IGNORECASE,
    )

    if match:
        return [{"action": "google_search", "query": match.group(1).strip()}]

    if command.startswith("search google"):

        query = command.replace(
            "search google",
            "",
            1
        ).strip()

        return [
            {
                "action": "google_search",
                "query": query
            }
        ]

    # * -----------------------------------------------------
    # * YouTube Search
    # * -----------------------------------------------------

    if command.startswith("search youtube"):

        query = command.replace(
            "search youtube",
            "",
            1
        ).strip()

        if query.startswith("for "):
            query = query[4:].strip()

        if not query:
            return None

        return [
            {
                "action": "youtube_search",
                "query": query
            }
        ]
        
    # * -----------------------------------------------------
    # * Search <query> on YouTube
    # * -----------------------------------------------------

    if command.startswith("search ") and command.endswith(" on youtube"):

        query = command[
            len("search "):-len(" on youtube")
        ].strip()

        if query:
            return [
                {
                    "action": "youtube_search",
                    "query": query
                }
            ]
            
    # * -----------------------------------------------------
    # * YouTube Play First Video
    # * -----------------------------------------------------

    if command.startswith("play first youtube video for "):

        query = command.replace(
            "play first youtube video for ",
            "",
            1
        ).strip()

        if query:
            return [
                {
                    "action": "youtube_play_first",
                    "query": query
                }
            ]


    if command.startswith("play youtube video for "):

        query = command.replace(
            "play youtube video for ",
            "",
            1
        ).strip()

        if query:
            return [
                {
                    "action": "youtube_play_first",
                    "query": query
                }
            ]


    if command.startswith("play first video for "):

        query = command.replace(
            "play first video for ",
            "",
            1
        ).strip()

        if query:
            return [
                {
                    "action": "youtube_play_first",
                    "query": query
                }
            ]


    # * -----------------------------------------------------
    # * YouTube Play First Video - Current Search
    # * -----------------------------------------------------

    if command in [
        "play youtube",
        "play youtube video",
        "play first youtube video",
        "play first video",
    ]:

        return [
            {
                "action": "youtube_play_first"
            }
        ]


    # * -----------------------------------------------------
    # * YouTube Pause
    # * -----------------------------------------------------

    if command in [
        "pause youtube",
        "pause youtube video",
        "pause video",
        "pause the video",
        "pause",
    ]:

        return [
            {
                "action": "youtube_pause"
            }
        ]


    # * -----------------------------------------------------
    # * YouTube Resume
    # * -----------------------------------------------------

    if command in [
        "resume youtube",
        "resume youtube video",
        "resume the youtube video",
        "resume video",
        "resume the video",
        "continue youtube",
        "continue the youtube video",
        "continue video",
        "continue the video",
        "continue playing",
    ]:

        return [
            {
                "action": "youtube_resume"
            }
        ]


    # * -----------------------------------------------------
    # * YouTube Next
    # * -----------------------------------------------------

    if command in [
        "next youtube",
        "next youtube video",
        "next the youtube video",
        "next video",
        "next the video",
        "play next video",
        "play the next video",
        "play next youtube video",
        "play the next youtube video",
    ]:
        return [
            {
                "action": "youtube_next"
            }
        ]


    # * -----------------------------------------------------
    # * YouTube Previous
    # * -----------------------------------------------------

    if command in [
        "previous youtube",
        "previous youtube video",
        "previous the youtube video",
        "previous video",
        "previous the video",
        "play previous video",
        "play the previous video",
        "play previous youtube video",
        "play the previous youtube video",
    ]:
        return [
            {
                "action": "youtube_previous"
            }
        ]
        
    # * -----------------------------------------------------
    # * Browser Navigation Controls
    # * -----------------------------------------------------

    # * New Tab
    if command in [
        "new tab",
        "open new tab",
        "open a new tab",
        "create new tab",
    ]:
        return [
            {
                "action": "new_tab"
            }
        ]
        
    # * Close Tab
    if command in [
        "close tab",
        "close current tab",
        "close this tab",
    ]:
        return [
            {
                "action": "close_tab"
            }
        ]

    # * Forward
    if command in [
        "forward",
        "go forward",
        "go forwards",
        "go to next page",
        "next page",
    ]:
        return [
            {
                "action": "forward"
            }
        ]

    # * Back
    if command in [
        "back",
        "go back",
        "go backward",
        "go to previous page",
        "previous page",
    ]:
        return [
            {
                "action": "back"
            }
        ]
        
    # * Scroll Down
    if command in [
        "scroll down",
        "scroll down the page",
        "scroll down a little",
    ]:
        return [
            {
                "action": "scroll_down"
            }
        ]

    # * Scroll Up
    if command in [
        "scroll up",
        "scroll up the page",
        "scroll up a little",
    ]:
        return [
            {
                "action": "scroll_up"
            }
        ]
        
    # * Refresh
    if command in [
        "refresh",
        "refresh page",
        "refresh the page",
        "reload",
        "reload page",
        "reload the page",
    ]:
        return [
            {
                "action": "refresh"
            }
        ]
        
    # * Close Browser
    if command in [
        "close chrome",
        "close google",
        "close browser",
        "close jarvis browser",
        "exit chrome",
        "exit browser",
    ]:
        return [
            {
                "action": "close"
            }
        ]

    # * -----------------------------------------------------
    # * Windows Applications
    # * -----------------------------------------------------

    if command.startswith("open "):

        app = command.replace(
            "open ",
            "",
            1
        ).strip()

        if app in WINDOWS_APPS: 

            return [
                {
                    "action": "open",
                    "app": app
                }
            ]

    # * -----------------------------------------------------
    # * Browser Websites
    # * -----------------------------------------------------

    if command.startswith("open "):

        site = command.replace(
            "open ",
            "",
            1
        ).strip()

        if site in BROWSER_SITES:

            return [
                {
                    "action": "open",
                    "app": site
                }
            ]

    # * -----------------------------------------------------
    # * Direct website names
    # * -----------------------------------------------------

    if command in BROWSER_SITES:

        return [
            {
                "action": "open",
                "app": command
            }
        ]

    return None
