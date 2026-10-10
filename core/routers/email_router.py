import re


def email_route(command):

    command = command.strip()

    # * -------------------------------------------------
    # * Send Email
    # * -------------------------------------------------

    match = re.fullmatch(

        r"(?:send|write|compose)\s+(?:an?\s+)?email\s+to\s+(.+)",

        command,

        re.IGNORECASE

    )

    if match:

        recipient = match.group(1).strip()

        if recipient:

            return [

                {

                    "action": "send_email",

                    "recipient": recipient

                }

            ]

    # * -------------------------------------------------
    # * Remember Email Contact
    # * -------------------------------------------------

    match = re.fullmatch(

        r"(?:remember|save|add)\s+email\s+contact\s+(.+?)\s+(?:as|is)\s+(\S+@\S+)",

        command,

        re.IGNORECASE

    )

    if match:

        alias = match.group(1).strip()

        email = match.group(2).strip()

        if alias and email:

            return [

                {

                    "action": "remember_email_contact",

                    "alias": alias,

                    "email": email

                }

            ]

    # * -------------------------------------------------
    # * Forget Email Contact
    # * -------------------------------------------------

    match = re.fullmatch(

        r"(?:forget|remove|delete)\s+email\s+contact\s+(.+)",

        command,

        re.IGNORECASE

    )

    if match:

        alias = match.group(1).strip()

        if alias:

            return [

                {

                    "action": "forget_email_contact",

                    "alias": alias

                }

            ]

    # * -------------------------------------------------
    # * Show Email Contacts
    # * -------------------------------------------------

    if command.lower() in [

        "show email contacts",

        "list email contacts",

        "show my email contacts",

        "list my email contacts",

        "email contacts",

    ]:

        return [

            {

                "action": "show_email_contacts"

            }

        ]

    # * -------------------------------------------------
    # * Open Gmail
    # * -------------------------------------------------

    if command.lower() in [

        "open gmail",

        "gmail",

        "open email",

        "open mail"

    ]:

        return [

            {

                "action": "gmail_open"

            }

        ]

    return None