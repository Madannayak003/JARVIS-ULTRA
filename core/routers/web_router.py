"""
JARVIS PRO
Web Router

Routes personal/custom web destinations.

This router does NOT:

- open browsers
- contain URLs
- contain voice logic

It only converts commands into actions.
"""

import re


# * =========================================================
# * Personal Web Targets
# * =========================================================

PERSONAL_WEB_TARGETS = {

    # * -----------------------------------------------------
    # * GitHub
    # * -----------------------------------------------------

    "github": "github",
    "github profile": "github_profile",
    "github repository": "github_repository",
    "github repositories": "github_repository",
    "github repos": "github_repository",

    # * -----------------------------------------------------
    # * Facebook
    # * -----------------------------------------------------

    "facebook": "facebook",
    "facebook profile": "facebook_profile",

    # * -----------------------------------------------------
    # * LinkedIn
    # * -----------------------------------------------------

    "linkedin": "linkedin",
    "linkedin profile": "linkedin_profile",

    # * -----------------------------------------------------
    # * Websites
    # * -----------------------------------------------------

    "website": "website",
    "portfolio": "portfolio",

    "iot": "iot",
    "iot website": "iot_website",
    "iot site": "iot_website",
    
    # * -----------------------------------------------------
    # * JARVIS
    # * -----------------------------------------------------

    "jarvis github": "jarvis_github",
    "jarvis repository": "jarvis_repository",
    "jarvis repo": "jarvis_repository",

    # * -----------------------------------------------------
    # * Projects
    # * -----------------------------------------------------

    "smart parking": "smart_parking",
    "smart parking project": "smart_parking",

    "atmers": "atmers",
    "atmers project": "atmers",
}


# * =========================================================
# * Command Prefixes
# * =========================================================

COMMAND_PREFIXES = [
    r"^open\s+",
    r"^launch\s+",
    r"^go\s+to\s+",
    r"^show\s+",
    r"^visit\s+",
    r"^take\s+me\s+to\s+",
]


WEBSITE_LIST_COMMANDS = {
    "open website list",
    "show website list",
    "show my websites",
    "open my websites",
    "show my links",
    "open my links",
    "personal websites",
    "personal links",
}


# * =========================================================
# * Router
# * =========================================================

def web_route(command):

    if not command:
        return None

    command = str(command).strip().lower()

    if not command:
        return None

    if command in WEBSITE_LIST_COMMANDS:
        return [{"action": "show_personal_links"}]
    
    personal_request = bool(
        re.search(r"\b(?:my|mine)\b", command)
    )

    # * -----------------------------------------------------
    # * Start with original command
    # * -----------------------------------------------------

    target = command

    # * -----------------------------------------------------
    # * Remove command prefix
    # * -----------------------------------------------------

    for pattern in COMMAND_PREFIXES:

        new_target = re.sub(
            pattern,
            "",
            target,
            count=1
        )

        if new_target != target:

            target = new_target.strip()

            break

    # * -----------------------------------------------------
    # * Remove natural ownership words
    # * -----------------------------------------------------

    target = re.sub(
        r"^(?:my|mine)\s+",
        "",
        target
    ).strip()
    
    # * -----------------------------------------------------
    # * Ambiguous destinations
    # * -----------------------------------------------------
    # * Generic commands such as "open github" should go
    # * to the normal browser router.
    #
    # * Personal versions such as "open my github" should
    # * use the personal-link system.

    AMBIGUOUS_PERSONAL_TARGETS = {
        "github",
        "github profile",
        "github repository",
        "github repos",
    }
    
    if target in AMBIGUOUS_PERSONAL_TARGETS and not personal_request:
        return None

    # * -----------------------------------------------------
    # * Direct target match
    # * -----------------------------------------------------

    link_name = PERSONAL_WEB_TARGETS.get(target)

    if link_name:

        return [{
            "action": "open_personal_link",
            "name": link_name
        }]

    return None
