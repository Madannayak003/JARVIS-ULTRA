"""
JARVIS PRO
News Router

Routes explicit user-requested news commands.

Important:
Morning Brief ON/OFF controls automatic startup news only.
Explicit news requests always remain available.
"""

from core.registry import has_skill


NEWS_COMMANDS = {
    "news",
    "the news",

    "tell me the news",
    "give me the news",
    "show me the news",

    "today's news",
    "todays news",
    "today news",

    "today's top news",
    "todays top news",
    "today top news",

    "latest news",
    "latest headlines",

    "today's headlines",
    "todays headlines",

    "top news",
    "top headlines",

    "what's the news",
    "whats the news",
    "what is the news",

    "what's happening today",
    "whats happening today",
}


def news_route(command):

    command = command.lower().strip()

    if command in NEWS_COMMANDS:

        if not has_skill("get_news"):

            print(
                "[NEWS ROUTER] "
                "get_news skill is not registered."
            )

            return None

        print(
            "[NEWS ROUTER] "
            "Explicit news request detected."
        )

        return [
            {
                "action": "get_news",
            }
        ]

    return None