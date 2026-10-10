import json
from ai.core.service import ai_service
from ai.planner_prompt import SYSTEM_PROMPT
from core.context import get_history
from core.context import get_value

from core.fast_router import fast_route

from core.action_memory import get_memory

from core.action_memory import set_memory

from core.app_resolver import resolve_app
from core.diagnostics import debug_print


# * Commands that already express an operation should continue through the
# * existing deterministic routes or the AI planner. A short input with none
# * of these indicators is an object/topic, not an implicit web-search request.
_ACTION_WORDS = {
    "open", "launch", "go", "show", "visit", "search", "find", "look",
    "tell", "explain", "describe", "what", "who", "where", "when", "why",
    "how", "is", "are", "can", "could", "do", "does", "play", "start",
    "stop", "create", "make", "write", "save", "add", "delete", "remove",
    "edit", "run", "send", "remember", "recall", "get", "turn", "increase",
    "decrease", "mute", "enable", "disable", "set", "read", "list",
}


def _looks_like_bare_topic(command: str) -> bool:
    """Return True for a short topic/object with no requested operation."""

    import re

    text = " ".join((command or "").lower().split())
    if not text or text.endswith(("?", ".", "!")):
        return False

    words = re.findall(r"[a-z0-9][a-z0-9_.+#-]*", text)
    if not 1 <= len(words) <= 3:
        return False

    return not any(word in _ACTION_WORDS for word in words)


def create_plan(command, stop_event):

    # * command = command.strip().lower()
    
    # * if stop_event.is_set():
    # * return None
    
    # * print("[PLANNER] Command:", command)
    
    # * plan = fast_route(command)
    
    # * =========================================================
    # * Preserve original command
    # * =========================================================

    original_command = command.strip()

    command = original_command.lower()

    if stop_event.is_set():
        return None

    debug_print("[PLANNER] Command:", command)


    # * =========================================================
    # * Natural Notes Routing
    # * =========================================================

    import re


    # * ---------------------------------------------------------
    # * Create note
    # * ---------------------------------------------------------

    note_patterns = [
        r"^(?:take|make|write|save|create|add)\s+(?:a\s+)?note(?:\s+(?:that|to|about|for|saying))?\s+(.+)$",

        r"^note\s+(?:that|to|about|for|saying)?\s*(.+)$",

        r"^write\s+this\s+down\s*[:\-]?\s*(.+)$",

        r"^save\s+this\s+as\s+a\s+note\s*[:\-]?\s*(.+)$",
    ]


    for pattern in note_patterns:

        match = re.match(
            pattern,
            original_command,
            re.IGNORECASE,
        )

        if match:

            note_text = match.group(1).strip()

            # * Remove accidental leading filler words
            note_text = re.sub(
                r"^(?:that|to|about|for)\s+",
                "",
                note_text,
                flags=re.IGNORECASE,
            ).strip()

            if note_text:

                debug_print(
                    "[NOTES ROUTER] Creating note:",
                    note_text,
                )

                return [{
                    "action": "create_note",
                    "text": note_text,
                }]


    # * ---------------------------------------------------------
    # * List notes
    # * ---------------------------------------------------------

    if re.fullmatch(
        r"(?:show|list|read|display)\s+(?:my\s+)?notes?",
        command,
    ):

        debug_print("[NOTES ROUTER] Listing notes")

        return [{
            "action": "list_notes"
        }]


    if re.fullmatch(
        r"(?:what\s+are|what's|whats)\s+(?:my\s+)?notes?",
        command,
    ):

        debug_print("[NOTES ROUTER] Listing notes")

        return [{
            "action": "list_notes"
        }]


    # * ---------------------------------------------------------
    # * Clear notes
    # * ---------------------------------------------------------

    if re.fullmatch(
        r"(?:clear|delete|remove)\s+(?:all\s+)?(?:my\s+)?notes?",
        command,
    ):

        debug_print("[NOTES ROUTER] Clearing notes")

        return [{
            "action": "clear_notes"
        }]


    # * =========================================================
    # * Existing Fast Router
    # * =========================================================

    plan = fast_route(command)

    debug_print("[PLANNER] Fast Route:", plan)
    
    if plan:
        return plan

    # ! Do not guess an action for a standalone topic. This prevents the AI
    # * planner from treating an object such as "esp32" as a Google search while
    # * preserving explicit commands and informational questions.
    if _looks_like_bare_topic(command):
        return [{
            "action": "clarify",
            "question": f"What would you like me to do with {original_command}?",
            "context": {
                "subject": original_command,
                "type": "generic_action",
            },
        }]
    
    # * -------------------------------
    # * Smart Search Platform Memory V2
    # * -------------------------------

    if command.startswith("search "):

        query = command.replace("search", "", 1).strip()

        # * ---------------- Explicit platform ----------------

        PLATFORM_MAP = {
            "youtube": "youtube_search",
            "google": "google_search",
            "github": "github_search",
            "chatgpt": "chatgpt_search"
        }

        for platform, action in PLATFORM_MAP.items():

            if (
                f" on {platform}" in query
                or f" in {platform}" in query
                or query.endswith(f" {platform}")
            ):

                clean_query = (
                    query.replace(f" on {platform}", "")
                        .replace(f" in {platform}", "")
                        .strip()
                )

                if clean_query.endswith(f" {platform}"):
                    clean_query = clean_query[
                        :-len(platform)
                    ].strip()

                return [{
                    "action": action,
                    "query": clean_query
                }]

        # * ---------------- Use remembered platform ----------------

        platform = get_memory("search_platform")

        if platform:

            debug_print(f"[SMART SEARCH] Using {platform}")

            if platform == "youtube":

                return [{
                    "action": "youtube_search",
                    "query": query
                }]

            elif platform == "google":

                return [{
                    "action": "google_search",
                    "query": query
                }]

            elif platform == "github":

                return [{
                    "action": "github_search",
                    "query": query
                }]

            elif platform == "chatgpt":

                return [{
                    "action": "chatgpt_search",
                    "query": query
                }]

        # * ---------------- Ask first time ----------------

        return [{
            "action": "clarify",
            "question": "Where would you like me to search? Google, YouTube, GitHub or ChatGPT?",
            "context": {
                "pending_search": query,
                "accepted_answers": list(
                    PLATFORM_MAP
                ),
            }
        }]
    
    # * ---------- Simple browser shortcuts -----------

    if command.startswith("open google search"):
        return fast_route(command)

    if command.startswith("open youtube search"):
        return fast_route(command)

    if command.startswith("search google"):
        return fast_route(command)

    if command.startswith("search youtube"):
        return fast_route(command)
    
    # * ---------- Fast System Commands ----------

    if "shutdown" in command:
        return [{"action": "shutdown"}]

    if "restart" in command:
        return [{"action": "restart"}]

    if "sleep" in command:
        return [{"action": "sleep"}]

    if "lock" in command:
        return [{"action": "lock"}]

    
    # * -------------------------------
    # * Smart App Resolver
    # * -------------------------------

    app = resolve_app(command)

    if app:

        debug_print(f"[SMART APP] {app}")

        return [{
            "action": "open",
            "app": app
        }]
    
    # * -------- Incomplete Commands --------

    if command == "open":
        return [{
            "action": "clarify",
            "question": "What would you like me to open?"
        }]

    if command == "play":
        return [{
            "action": "clarify",
            "question": "What would you like me to play?"
        }]

    if command == "search":
        return [{
            "action": "clarify",
            "question": "What would you like me to search for?"
        }]

    # * Continue with Ollama
    if stop_event.is_set():
        return None
    
    history = get_history()

    current_app = get_value("current_app")

    history_text = ""

    for item in history[-10:]:

        history_text += f"{item['role']}: {item['text']}\n"

    prompt = f"""
    Current App:
    {current_app}

    Conversation:
    {history_text}

    User Command:
    {command}
    """
    # * ---------------------------------------
    # AI Model System
    # * ---------------------------------------

    response = ai_service.generate(

        prompt=prompt,

        system_prompt=SYSTEM_PROMPT,

        capability="planning",

    )

    if stop_event.is_set():
        return None

    if not response.success:

        debug_print(
            "[PLANNER AI ERROR]",
            response.error
        )

        return [
            {
                "action": "clarify",
                "question": (
                    f"I couldn't process "
                    f"'{command}' right now."
                ),
                "context": {
                    "subject": command,
                    "type": "ai_generation_error",
                    "error": response.error,
                }
            }
        ]

    answer = response.text

    answer = answer.strip()

    if answer.startswith("```"):
        answer = (
            answer.replace("```json", "")
                .replace("```", "")
                .strip()
        )

    debug_print("\n========== AI PLAN ==========")
    debug_print(answer)
    debug_print("=============================\n")

    try:

        return json.loads(answer)

    except Exception as e:

        print("Planner Error:", e)

        return [
            {
                "action": "clarify",
                "question": f"What would you like to do with '{command}'?",
                "context": {
                    "subject": command,
                    "type": "generic_action"
                }
            }
        ]
