"""
JARVIS PRO
Screen Context Manager

Stores the latest useful understanding of the user's
computer screen.

This module does NOT:
- capture screenshots
- call AI providers
- control the screen
- modify conversation state

It only stores and manages screen context.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class ScreenContextManager:
    """
    Stores the latest screen understanding.
    """

    def __init__(self):

        self._context: Optional[Dict[str, Any]] = None

    # * ==================================================
    # * Set Context
    # * ==================================================

    def set_context(
        self,
        context: Dict[str, Any],
    ) -> None:
        """
        Store the latest screen context.
        """

        if not isinstance(context, dict):

            raise TypeError(
                "Screen context must be a dictionary."
            )

        self._context = dict(context)

        self._context.setdefault(
            "analyzed_at",
            datetime.now().isoformat(
                timespec="seconds"
            ),
        )

    # * ==================================================
    # * Get Context
    # * ==================================================

    def get_context(
        self,
    ) -> Optional[Dict[str, Any]]:
        """
        Return the latest screen context.

        Returns:
            dict or None
        """

        if self._context is None:

            return None

        return dict(self._context)

    # * ==================================================
    # * Has Context
    # * ==================================================

    def has_context(
        self,
    ) -> bool:
        """
        Check whether screen context exists.
        """

        return self._context is not None

    # * ==================================================
    # * Clear
    # * ==================================================

    def clear(
        self,
    ) -> None:
        """
        Remove the current screen context.
        """

        self._context = None

    # * ==================================================
    # * Information
    # * ==================================================

    def info(
        self,
    ) -> Dict[str, Any]:
        """
        Return diagnostics about the current context.
        """

        return {
            "available": self.has_context(),
            "context": self.get_context(),
        }


# * ======================================================
# * Shared Screen Context
# * ======================================================

screen_context = ScreenContextManager()