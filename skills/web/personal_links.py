"""
JARVIS PRO
Personal Web Skill

Registers personal web destinations
with the JARVIS action registry.

Execution remains in services.
"""

from core.registry import register
from services.personal_link_service import open_personal_link, show_personal_links


def personal_link_action(data=None):

    data = data or {}

    name = str(
        data.get("name", "")
    ).strip()

    return open_personal_link(name)


register(
    "open_personal_link",
    personal_link_action
)


register(
    "show_personal_links",
    lambda data=None: show_personal_links(),
)
