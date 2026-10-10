from core.file_selection_memory import get_files


def file_selection_route(command):

    pending = get_files()

    if not pending:
        return None

    command = command.lower().strip()

    files = pending.get("files", [])
    purpose = pending.get("purpose", "search")

    if not files:
        return None

    # * -------------------------------------------------
    # * File index
    # * -------------------------------------------------

    mapping = {
        "first": 0,
        "first one": 0,
        "1": 0,

        "second": 1,
        "second one": 1,
        "2": 1,

        "third": 2,
        "third one": 2,
        "3": 2,

        "fourth": 3,
        "fourth one": 3,
        "4": 3,

        "fifth": 4,
        "fifth one": 4,
        "5": 4,

        "sixth": 5,
        "sixth one": 5,
        "6": 5,

        "seventh": 6,
        "seventh one": 6,
        "7": 6,

        "eighth": 7,
        "eighth one": 7,
        "8": 7,

        "ninth": 8,
        "ninth one": 8,
        "9": 8,

        "tenth": 9,
        "tenth one": 9,
        "10": 9,
    }

    # * -------------------------------------------------
    # * Selected file
    # * -------------------------------------------------

    if command in mapping:

        index = mapping[command]

        if index >= len(files):
            return None

        path = str(files[index])

        # * ---------------------------------------------
        # * Normal file search
        # * ---------------------------------------------

        if purpose == "search":

            return [{
                "action": "open_file",
                "path": path
            }]

        # * ---------------------------------------------
        # * WhatsApp selection
        # * ---------------------------------------------

        if purpose == "whatsapp":

            return [{
                "action": "whatsapp_send_selected_file",
                "index": index
            }]

        return None

    # * -------------------------------------------------
    # * WhatsApp-specific selections
    # * -------------------------------------------------

    if purpose == "whatsapp":

        if "latest" in command:

            return [{
                "action": "whatsapp_send_latest_selected_file"
            }]

        if "oldest" in command:

            return [{
                "action": "whatsapp_send_oldest_selected_file"
            }]

        if "pdf" in command:

            return [{
                "action": "whatsapp_send_pdf"
            }]

        if "docx" in command:

            return [{
                "action": "whatsapp_send_docx"
            }]

    return None