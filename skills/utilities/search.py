from core.registry import register
from voice.manager import speak

from services.file_manager import search_files
from core.file_selection_memory import (
    set_files,
    clear_files,
)


def search_action(data):

    data = data or {}

    query = str(
        data.get("query", "")
    ).strip()

    extension = str(
        data.get("extension", "")
    ).strip()

    if not query and not extension:

        speak(
            "What file should I search for?"
        )

        return False

    try:

        results = search_files(
            query,
            extension
        )

    except Exception as e:

        print(
            f"[FILE SEARCH ERROR] {e}"
        )

        clear_files()

        speak(
            "I couldn't search for the file."
        )

        return False

    # * -------------------------------------------------
    # * No Results
    # * -------------------------------------------------

    if not results:

        clear_files()

        speak(
            "No matching files found."
        )

        return True

    # * -------------------------------------------------
    # * Remember Search Results
    # * -------------------------------------------------

    set_files({
        "purpose": "search",
        "files": results,
    })

    # * -------------------------------------------------
    # * Display Results
    # * -------------------------------------------------

    print()
    print("Found Files")
    print()

    for index, path in enumerate(
        results[:10],
        1
    ):

        print(
            f"{index}. {path}"
        )

    print()

    # * -------------------------------------------------
    # * Voice Response
    # * -------------------------------------------------

    if len(results) == 1:

        speak(
            "I found one matching file."
        )

    else:

        speak(
            f"I found {len(results)} matching files."
        )

    return True


register(
    "search_file",
    search_action
)