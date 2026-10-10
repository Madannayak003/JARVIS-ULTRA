from core.registry import register
from voice.manager import speak
from skills.browser.navigation import navigation
from core.action_memory import set_memory
from core.action_memory import dump


def ai_chatgpt(data):

    query = data.get("query", "")

    speak(f"Opening ChatGPT for {query}")

    navigation.chatgpt(query)

    set_memory("site", "chatgpt")
    set_memory("search_platform", "chatgpt")
    set_memory("search", query)
    set_memory("action", "chatgpt_search")

    print("[MEMORY]", dump())

    return True


register("chatgpt_search", ai_chatgpt)