"""
JARVIS PRO
Screen Follow-up Context

Determines whether a new user request is a natural
follow-up to the most recently analyzed screen.

This does NOT capture the screen.
This does NOT call vision AI.

It only decides whether existing screen context
should be used by the normal conversational pipeline.
"""

from brain.screen_context import screen_context


# * =========================================================
# * Follow-up Detection
# * =========================================================

SCREEN_REFERENCES = (

    # * Direct screen references
    "this screen",
    "the screen",
    "my screen",
    "on screen",

    # * Visual references
    "this image",
    "the image",
    "this picture",
    "the picture",
    "this photo",
    "the photo",

    # * Visible content
    "what is this",
    "what are they",
    "who are they",
    "who is this",
    "what is happening",
    "what happened",

    # * Screen/application
    "what app",
    "which app",
    "what application",
    "which application",
    "what window",
    "which window",

    # * Visible information
    "what does it show",
    "what is shown",
    "what is displayed",
    "what is visible",
    "what can you see",

    # * Image information
    "image resolution",
    "image size",
    "file size",
    "what resolution",
)

# * =========================================================
# * Screen Data Follow-ups
# * =========================================================
#
# * These are short requests that refer to information
# * visible on the currently analyzed screen.
#
# * Example:
#
# * Screen context:
# * Tata Consumer Products
#
# * User:
# * "today low price"
#
# * This should continue the current screen conversation
# * instead of going to screenshot_ai.
#

SCREEN_DATA_FOLLOWUPS = (

    # * -----------------------------------------------------
    # * Stock / Financial
    # * -----------------------------------------------------

    "today low",
    "today's low",
    "todays low",
    "low price",
    "lowest price",
    "today high",
    "today's high",
    "todays high",
    "high price",
    "highest price",

    "current price",
    "current rate",
    "latest price",
    "market price",

    "price change",
    "percentage change",
    "percent change",
    "change today",
    "changed today",

    "how much is it up",
    "how much is it down",
    "how much did it move",

    # * -----------------------------------------------------
    # * Stock identity
    # * -----------------------------------------------------

    "which stock",
    "what stock",
    "stock name",
    "which company",
    "what company",

    # * -----------------------------------------------------
    # * Visible numeric information
    # * -----------------------------------------------------

    "what is the price",
    "what's the price",
    "what is the value",
    "what's the value",

)


FOLLOW_UP_WORDS = (

    "what",
    "who",
    "which",
    "where",
    "when",
    "why",
    "how",
    "is",
    "are",
    "does",
    "do",
    "can",
)


# * =========================================================
# * Has Active Screen Context
# * =========================================================

def has_screen_context():

    try:

        return screen_context.has_context()

    except Exception as e:

        print(
            f"[SCREEN FOLLOWUP ERROR] "
            f"Context check failed: {e}"
        )

        return False


# * =========================================================
# * Detect Screen Follow-up
# * =========================================================

def is_screen_followup(command):

    if not command:
        return False

    if not has_screen_context():
        return False

    command = command.strip().lower()

    if not command:
        return False

    # * -----------------------------------------------------
    # * Explicit screen/image references
    # * -----------------------------------------------------

    for phrase in SCREEN_REFERENCES:

        if phrase in command:

            print(
                "[SCREEN FOLLOWUP] "
                f"Explicit reference: {phrase}"
            )

            return True

    # * -----------------------------------------------------
    # * Screen data follow-ups
    #
    # * Example:
    #
    # * "today low price"
    # * "current price"
    # * "percentage change"
    # * "which stock"
    #
    # * These refer to information contained in the
    # * currently active screen context.
    # * -----------------------------------------------------

    for phrase in SCREEN_DATA_FOLLOWUPS:

        if phrase in command:

            print(
                "[SCREEN FOLLOWUP] "
                f"Screen data follow-up: {phrase}"
            )

            return True

    # * -----------------------------------------------------
    # * Short natural follow-up questions
    # * -----------------------------------------------------

    words = command.split()

    if len(words) <= 12:

        first_word = words[0]

        if first_word in FOLLOW_UP_WORDS:

            print(
                "[SCREEN FOLLOWUP] "
                "Natural short follow-up detected."
            )

            return True

    return False

# * =========================================================
# * Info
# * =========================================================

def info():

    try:

        return {
            "screen_context_available":
                has_screen_context(),

            "reference_count":
                len(SCREEN_REFERENCES),

            "follow_up_word_count":
                len(FOLLOW_UP_WORDS),
        }

    except Exception:

        return {
            "screen_context_available": False
        }