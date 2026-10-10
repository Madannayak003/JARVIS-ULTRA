from __future__ import annotations

from abc import ABC, abstractmethod


class BaseRouter(ABC):

    @abstractmethod
    def route(self, user_input: str):
        """
        Attempt to handle the request.

        Return a router-specific result.
        """
        raise NotImplementedError