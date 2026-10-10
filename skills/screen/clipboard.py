"""
JARVIS PRO
Clipboard Skill

Provides clipboard reading and optional AI-powered
summary/explanation.
"""

import pyperclip

from core.registry import register
from voice.manager import speak

from ai.core.service import ai_service


# * =========================================================
# * Clipboard
# * =========================================================

def clipboard(data=None):
    """
    Read or process the current clipboard contents.

    Supported modes:

        read
        summary
        explain
    """

    if data is None:
        data = {}

    try:
        text = pyperclip.paste()

    except Exception as e:

        print(f"[CLIPBOARD ERROR] Unable to read clipboard: {e}")

        speak(
            "I couldn't access the clipboard."
        )

        return False

    # * -----------------------------------------------------
    # * Empty clipboard
    # * -----------------------------------------------------

    if not text or not text.strip():

        speak(
            "Your clipboard is empty."
        )

        return True

    mode = str(
        data.get("mode", "read")
    ).strip().lower()

    # * =====================================================
    # * READ
    # * =====================================================

    if mode == "read":

        content = text.strip()

        # * Keep voice response reasonably short.
        if len(content) > 500:
            content = content[:500] + "..."

        speak(content)

        print(
            f"[CLIPBOARD] Read {len(text)} characters"
        )

        return True

    # * =====================================================
    # * SUMMARY / EXPLAIN
    # * =====================================================

    if mode in ("summary", "summarize", "explain"):

        if mode in ("summary", "summarize"):

            system_prompt = (
                "Summarize the clipboard content clearly "
                "and concisely. Give the important points "
                "in natural language."
            )

        else:

            system_prompt = (
                "Explain the clipboard content clearly "
                "in simple natural language. "
                "Help the user understand what it means."
            )

        try:

            response = ai_service.generate(

                prompt=text,

                system_prompt=system_prompt,

                capability="conversation",

            )

        except Exception as e:

            print(
                f"[CLIPBOARD AI ERROR] {e}"
            )

            speak(
                "I couldn't process the clipboard with AI."
            )

            return False

        # * -------------------------------------------------
        # AI failure
        # * -------------------------------------------------

        if not response.success:

            print(
                "[CLIPBOARD AI] Generation failed:",
                response.error,
            )

            speak(
                "I couldn't process that clipboard content."
            )

            return False

        # * -------------------------------------------------
        # * Diagnostics
        # * -------------------------------------------------

        print(
            "[CLIPBOARD AI] Provider:",
            response.provider,
        )

        print(
            "[CLIPBOARD AI] Model:",
            response.model,
        )

        # * -------------------------------------------------
        # * Response
        # * -------------------------------------------------

        if not response.text:

            speak(
                "I didn't get a useful response from the AI."
            )

            return False

        speak(
            response.text
        )

        return True

    # * =====================================================
    # * Unknown mode
    # * =====================================================

    print(
        f"[CLIPBOARD] Unknown mode: {mode}"
    )

    speak(
        "I don't know how to process the clipboard that way."
    )

    return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "clipboard",
    clipboard,
)