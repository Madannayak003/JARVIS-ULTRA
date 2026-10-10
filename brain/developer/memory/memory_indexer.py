"""
JARVIS PRO
Developer Memory

Memory Indexer
"""

from typing import Any


class MemoryIndexer:
    """
    Builds and updates an in-memory index
    of Developer Memory.
    """

    def __init__(self):

        self.index: dict[str, dict[str, Any]] = {}

    # * --------------------------------------------------
    # * Build
    # * --------------------------------------------------

    def build(
        self,
        memory: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """
        Build an index from the complete memory database.
        """

        self.index = {}

        if not isinstance(memory, dict):
            return self.index

        for category, records in memory.items():

            if category == "version":
                continue

            if isinstance(records, dict):

                for key, value in records.items():

                    self._add(
                        category,
                        key,
                        value,
                    )

            elif isinstance(records, list):

                for index, value in enumerate(records):

                    self._add(
                        category,
                        str(index),
                        value,
                    )

        return self.index

    # * --------------------------------------------------
    # * Add
    # * --------------------------------------------------

    def _add(
        self,
        category: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Add one memory item to the index.
        """

        category_index = self.index.setdefault(
            category,
            {},
        )

        category_index[key] = value

    # * --------------------------------------------------
    # * Update
    # * --------------------------------------------------

    def update(
        self,
        category: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Add or update one indexed memory item.
        """

        if not category or not key:
            return

        self._add(
            category,
            key,
            value,
        )

    # * --------------------------------------------------
    # * Get
    # * --------------------------------------------------

    def get(
        self,
        category: str,
        key: str,
    ) -> Any:
        """
        Retrieve one indexed memory item.
        """

        return (
            self.index
            .get(category, {})
            .get(key)
        )

    # * --------------------------------------------------
    # * Category
    # * --------------------------------------------------

    def get_category(
        self,
        category: str,
    ) -> dict[str, Any]:
        """
        Return all records from a category.
        """

        return self.index.get(
            category,
            {},
        )

    # * --------------------------------------------------
    # * Clear
    # * --------------------------------------------------

    def clear(self) -> None:
        """
        Clear the complete index.
        """

        self.index.clear()