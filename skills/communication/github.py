from core.registry import register
from voice.manager import speak
from skills.browser.browser_controller import browser
from core.action_memory import set_memory
from core.action_memory import dump


def ai_github(data):

    query = data.get("query", "").strip()

    if not query:
        return False

    speak(f"Searching GitHub for {query}")

    browser.search_github(query)

    set_memory("site", "github")
    set_memory("search_platform", "github")
    set_memory("search", query)
    set_memory("action", "github_search")

    print("[MEMORY]", dump())

    return True


register("github_search", ai_github)