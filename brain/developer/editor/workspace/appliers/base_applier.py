"""
JARVIS PRO
Developer Editor

Base Applier
"""

from abc import ABC
from abc import abstractmethod


class BaseApplier(ABC):
    """
    Base class for all language-specific patch appliers.

    Every applier receives:

    - original file contents
    - generated code from the LLM

    and returns the merged file contents.
    """

    # * --------------------------------------------------

    @abstractmethod
    def apply(
        self,
        original: str,
        generated: str,
    ) -> str:
        """
        Merge generated code into the original file.

        Returns
        -------
        str
            Final merged file contents.
        """

        raise NotImplementedError