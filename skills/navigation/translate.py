"""
=============================================================
JARVIS PRO — TRANSLATION SKILL
=============================================================

Provides:
- Google Translate opening
- AI-powered text translation using the existing JARVIS AI
  service and provider routing.

No separate translation API key is required.
"""

import webbrowser

from core.registry import register
from voice.manager import speak
from ai.core.service import ai_service


GOOGLE_TRANSLATE_URL = "https://translate.google.com/"


# * =============================================================
# * OPEN GOOGLE TRANSLATE
# * =============================================================

def translate_open(data=None):
    try:

        opened = webbrowser.open_new_tab(
            GOOGLE_TRANSLATE_URL
        )

        if opened:
            speak("Opening Google Translate.")
            return True

        speak("I could not open Google Translate.")
        return False

    except Exception as error:

        print(
            f"[TRANSLATE ERROR] {error}"
        )

        speak(
            "I could not open Google Translate."
        )

        return False


# * =============================================================
# * TRANSLATE TEXT
# * =============================================================

def translate_text(data=None):
    data = data or {}

    text = str(
        data.get("text", "")
    ).strip()

    target = str(
        data.get("target", "")
    ).strip()

    if not text:
        speak(
            "Please tell me what to translate."
        )
        return False

    if not target:
        speak(
            "Please tell me the target language."
        )
        return False

    # * ---------------------------------------------------------
    # * Log translation request
    # * ---------------------------------------------------------

    print(
        f"[TRANSLATE] Text: {text}"
    )

    print(
        f"[TRANSLATE] Target: {target}"
    )

    # * ---------------------------------------------------------
    # * Translation prompt
    # * ---------------------------------------------------------

    prompt = f"""
Translate the following text into {target}.

Return only the translated text.
Do not add explanations.
Do not add quotation marks.
Do not mention the source language.

Text:
{text}
""".strip()

    # * ---------------------------------------------------------
    # * Use existing JARVIS AI service
    # * ---------------------------------------------------------

    try:

        response = ai_service.generate(
            prompt=prompt,
            capability="conversation",
        )

    except Exception as error:

        print(
            f"[TRANSLATE ERROR] {error}"
        )

        speak(
            "I could not translate that."
        )

        return False

    # * ---------------------------------------------------------
    # * Check AI response
    # * ---------------------------------------------------------

    if not response.success:

        print(
            "[TRANSLATE ERROR]",
            response.error
        )

        speak(
            "I could not translate that."
        )

        return False

    translated_text = str(
        response.text or ""
    ).strip()

    if not translated_text:

        print(
            "[TRANSLATE ERROR] Empty translation result."
        )

        speak(
            "I could not translate that."
        )

        return False

    # * ---------------------------------------------------------
    # * Translation result
    # * ---------------------------------------------------------

    print(
        f"[TRANSLATE RESULT] {translated_text}"
    )

    # * ---------------------------------------------------------
    # * Speak translation
    # * ---------------------------------------------------------

    speak(
        translated_text
    )

    return True


# * =============================================================
# * REGISTRATION
# * =============================================================

register(
    "translate_open",
    translate_open,
)

register(
    "translate_text",
    translate_text,
)