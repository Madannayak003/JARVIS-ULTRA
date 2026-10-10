# * import re


# * def contact_route(command):

# * command = command.strip()

# * # -------------------------------------------------
# * # Remember Contact
# * # -------------------------------------------------

# * match = re.fullmatch(

# * r"remember\s+(.+?)\s+as\s+(.+)",

# * command,

# * re.IGNORECASE

# * )

# * if match:

# * return [

# * {

# * "action": "remember_contact",

# * "alias": match.group(1).strip(),

# * "real_name": match.group(2).strip()

# * }

# * ]

# * # -------------------------------------------------
# * # Forget Contact
# * # -------------------------------------------------

# * match = re.fullmatch(

# * r"forget\s+(.+)",

# * command,

# * re.IGNORECASE

# * )

# * if match:

# * return [

# * {

# * "action": "forget_contact",

# * "alias": match.group(1).strip()

# * }

# * ]

# * # -------------------------------------------------
# * # Show Contacts
# * # -------------------------------------------------

# * if command.lower() in [

# * "list contacts",

# * "show contacts",

# * "my contacts",

# * "who are my contacts",

# * "show my contacts"
        
# * "contact status",
        
# * "contacts status",
        
# * "contact list",
        
# * "contacts",
        
# * "saved contacts",
        
# * "display contacts",
        
# * "show saved contacts"

# * ]:

# * return [

# * {

# * "action": "show_contacts"

# * }

# * ]

# * return None

# * contacts
# * contact
# * show contacts
# * show contact
# * list contacts
# * list contact
# * display contacts
# * display contact
# * my contacts
# * my contact
# * show my contacts
# * list my contacts
# * saved contacts
# * show saved contacts
# * contact status
# * contacts status
# * contact list
# * contacts list
# * display saved contacts

import re


def contact_route(command):

    command = command.strip()

    # * -------------------------------------------------
    # * Remember Contact
    # * -------------------------------------------------

    match = re.fullmatch(

        r"remember\s+(.+?)\s+as\s+(.+)",

        command,

        re.IGNORECASE

    )

    if match:

        return [

            {

                "action": "remember_contact",

                "alias": match.group(1).strip(),

                "real_name": match.group(2).strip()

            }

        ]

    # * -------------------------------------------------
    # * Forget Contact
    # * -------------------------------------------------

    match = re.fullmatch(

        r"forget\s+(.+)",

        command,

        re.IGNORECASE

    )

    if match:

        return [

            {

                "action": "forget_contact",

                "alias": match.group(1).strip()

            }

        ]

    # * -------------------------------------------------
    # * Show Contacts
    # * -------------------------------------------------

    match = re.fullmatch(

        r"(?:show|list|display)?\s*(?:my\s+)?(?:saved\s+)?contacts?(?:\s+(?:status|list))?",

        command,

        re.IGNORECASE

    )

    if match:

        return [

            {

                "action": "show_contacts"

            }

        ]

    return None