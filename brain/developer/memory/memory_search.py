"""
JARVIS PRO
Developer Memory

Memory Search
"""

from typing import Any


class MemorySearch:
    """
    Searches indexed Developer Memory.

    Current implementation uses simple
    case-insensitive keyword matching.
    """

    def __init__(self, indexer=None):

        self.indexer = indexer

    # * --------------------------------------------------
    # * Configure
    # * --------------------------------------------------

    def set_indexer(
        self,
        indexer,
    ) -> None:
        """
        Set the memory indexer.
        """

        self.indexer = indexer

    # * --------------------------------------------------
    # * Search
    # * --------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search indexed memory.

        Returns records ranked by
        simple keyword match score.
        """

        if not query or self.indexer is None:
            return []

        query = query.lower().strip()

        if not query:
            return []

        words = set(
            query.split()
        )

        results = []

        for category, records in self.indexer.index.items():

            if not isinstance(records, dict):
                continue

            for key, value in records.items():

                text = self._to_text(
                    key,
                    value,
                ).lower()

                score = self._score(
                    words,
                    text,
                )

                if score <= 0:
                    continue

                results.append(

                    {

                        "category": category,

                        "key": key,

                        "value": value,

                        "score": score,

                    }

                )

        results.sort(

            key=lambda item: (

                -item["score"],

                item["category"],

                item["key"],

            )

        )

        return results[:limit]

    # * --------------------------------------------------
    # * Score
    # * --------------------------------------------------

    def _score(
        self,
        words: set[str],
        text: str,
    ) -> int:
        """
        Calculate a simple keyword score.
        """

        score = 0

        for word in words:

            if word in text:

                score += 1

        return score

    # * --------------------------------------------------
    # * Convert To Text
    # * --------------------------------------------------

    def _to_text(
        self,
        key: str,
        value: Any,
    ) -> str:
        """
        Convert a memory record into searchable text.
        """

        return (
            f"{key} {value}"
        )