from abc import ABC, abstractmethod


class BaseResolver(ABC):
    """
    Base class for all analysis resolvers.
    """

    @abstractmethod
    def resolve(self, analysis):
        """
        Modify the AnalysisResult in-place.
        """
        pass