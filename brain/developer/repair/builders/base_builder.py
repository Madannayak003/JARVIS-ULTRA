"""
JARVIS PRO
Developer Repair

Base Builder
"""

from abc import ABC, abstractmethod


class BaseBuilder(ABC):

    @abstractmethod
    def build(self, context):
        pass