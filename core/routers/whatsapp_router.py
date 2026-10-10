import re

from services.whatsapp_parser import (
    parse_whatsapp,
    parse_whatsapp_call,
    parse_whatsapp_video_call,
    parse_scheduled_whatsapp,
    parse_list_scheduled_whatsapp,
    parse_cancel_scheduled_whatsapp,
    parse_reschedule_scheduled_whatsapp,
)

def whatsapp_route(command):

    command = command.lower().strip()

    # * =================================================
    # * Open / Close
    # * =================================================

    if command in (
        "open whatsapp",
        "launch whatsapp",
        "start whatsapp",
    ):

        return [
            {
                "action": "whatsapp_open"
            }
        ]

    if command in (
        "close whatsapp",
        "exit whatsapp",
    ):

        return [
            {
                "action": "whatsapp_close"
            }
        ]

    # * =================================================
    # * Latest Photo
    # * =================================================

    match = re.fullmatch(

        r"(?:send|share)\s+"
        r"(?:the\s+)?"
        r"(?:latest|last)\s+"
        r"(?:photo|picture|image)\s+"
        r"(?:to|with)\s+(.+)",

        command,

        re.IGNORECASE,
    )

    if match:

        return [
            {
                "action": "whatsapp_send_latest_photo",
                "contact": match.group(1).strip(),
            }
        ]

    # * =================================================
    # * Latest Screenshot
    # * =================================================

    match = re.fullmatch(

        r"(?:send|share)\s+"
        r"(?:the\s+)?"
        r"(?:latest|last)\s+"
        r"screenshot\s+"
        r"(?:to|with)\s+(.+)",

        command,

        re.IGNORECASE,
    )

    if match:

        return [
            {
                "action": "whatsapp_send_latest_screenshot",
                "contact": match.group(1).strip(),
            }
        ]    

    # * =================================================
    # * Scheduled WhatsApp Message
    # * =================================================

    scheduled = parse_scheduled_whatsapp(command)

    if scheduled:

        print(
            "[WHATSAPP SCHEDULER ROUTER] Creating scheduled message:",
            scheduled,
        )

        return [
            {
                "action": "schedule_whatsapp_message",

                "contact": scheduled["contact"],

                "message": scheduled["message"],

                "send_at": scheduled["send_at"],
            }
        ]
        
     # * =================================================
    # * Scheduled WhatsApp Management
    # * =================================================

    # * -------------------------------------------------
    # * List scheduled messages
    # * -------------------------------------------------

    if parse_list_scheduled_whatsapp(command):

        print(
            "[WHATSAPP SCHEDULER ROUTER] Listing scheduled messages"
        )

        return [
            {
                "action": "list_scheduled_whatsapp"
            }
        ]


    # * -------------------------------------------------
    # * Cancel scheduled message
    # * -------------------------------------------------

    scheduled_id = parse_cancel_scheduled_whatsapp(
        command
    )

    if scheduled_id is not None:

        print(
            "[WHATSAPP SCHEDULER ROUTER] "
            f"Cancelling scheduled message #{scheduled_id}"
        )

        return [
            {
                "action": "cancel_scheduled_whatsapp",
                "id": scheduled_id,
            }
        ]


    # * -------------------------------------------------
    # * Reschedule scheduled message
    # * -------------------------------------------------

    reschedule = parse_reschedule_scheduled_whatsapp(
        command
    )

    if reschedule:

        print(
            "[WHATSAPP SCHEDULER ROUTER] "
            f"Rescheduling message #{reschedule['id']} "
            f"-> {reschedule['send_at']}"
        )

        return [
            {
                "action": "reschedule_scheduled_whatsapp",
                "id": reschedule["id"],
                "send_at": reschedule["send_at"],
            }
        ]      
        
    # * -------------------------------------------------
    # * WhatsApp Video Call
    # * -------------------------------------------------

    result = parse_whatsapp_video_call(command)

    if result:

        print(
            "[WHATSAPP CALL ROUTER] "
            f"Video call: {result['contact']}"
        )

        return [
            {
                "action": "whatsapp_video_call",
                "contact": result["contact"],
            }
        ]


    # * -------------------------------------------------
    # * WhatsApp Voice Call
    # * -------------------------------------------------

    result = parse_whatsapp_call(command)

    if result:

        print(
            "[WHATSAPP CALL ROUTER] "
            f"Voice call: {result['contact']}"
        )

        return [
            {
                "action": "whatsapp_call",
                "contact": result["contact"],
            }
        ]    

    # * =================================================
    # * Normal WhatsApp Message
    # * =================================================

    result = parse_whatsapp(command)

    if result:

        return [
            {
                "action": "whatsapp_send_message",

                "contact": result["contact"],

                "message": result["message"],
            }
        ]

    # * =================================================
    # * Start WhatsApp conversation
    #
    # ! IMPORTANT:
    # * Only explicit WhatsApp wording is accepted.
    #
    # * "send whatsapp to John"
    # * "message John on whatsapp"
    #
    # * Generic "tell John" is NOT accepted.
    # * =================================================

    match = re.fullmatch(
        r"send\s+whatsapp\s+to\s+(.+)",
        command,
        re.IGNORECASE,
    )

    if match:

        contact = match.group(1).strip()

        if contact:

            return [
                {
                    "action": "whatsapp_wait_message",
                    "contact": contact,
                }
            ]

    # * -------------------------------------------------
    # * Explicit "message ... on whatsapp"
    # * -------------------------------------------------

    match = re.fullmatch(
        r"message\s+(.+?)\s+on\s+whatsapp",
        command,
        re.IGNORECASE,
    )

    if match:

        contact = match.group(1).strip()

        if contact:

            return [
                {
                    "action": "whatsapp_wait_message",
                    "contact": contact,
                }
            ]

    # * -------------------------------------------------
    # * "message John" remains supported ONLY when
    # * explicitly followed by "on whatsapp" is absent?
    #
    # ! We intentionally do NOT route generic:
    #
    # * message John
    #
    # * because "message" can have other meanings.
    # * -------------------------------------------------

    # * =================================================
    # * Send File
    # * =================================================

    match = re.fullmatch(

        r"send\s+(.+?)\s+to\s+(.+)",

        command,

        re.IGNORECASE,
    )

    if match:

        filename = match.group(1).strip()
        contact = match.group(2).strip()

        # * ---------------------------------------------
        # ! Don't steal normal message commands
        # * ---------------------------------------------

        blocked = (
            "message",
            "whatsapp",
            "whatsapp message",
            "text",
        )

        if filename.lower() not in blocked:

            return [
                {
                    "action": "whatsapp_send_file",
                    "filename": filename,
                    "contact": contact,
                }
            ]

    # * =================================================
    # * No WhatsApp match
    # * =================================================

    return None