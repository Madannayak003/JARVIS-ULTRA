"""
JARVIS PRO
Phase 11.3.3

Reference Resolver

Resolves conversational references such as:

    it
    this
    that
    these
    those
    the first one
    the second one
    the last one
    the previous one
    the same one

IMPORTANT:

This module does NOT execute commands.

It does NOT modify:
    - Dispatcher
    - Planner
    - Skills
    - IntentEngine
    - Memory
    - Existing confirmation system

It only resolves references against existing
conversation context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


# * ============================================================
# * Reference Resolution Result
# * ============================================================

@dataclass
class ReferenceResolution:

    resolved: bool = False

    reference: Optional[str] = None

    value: Optional[Any] = None

    source: Optional[str] = None

    confidence: float = 0.0

    reason: str = ""


# * ============================================================
# * Reference Resolver
# * ============================================================

class ReferenceResolver:

    def __init__(self):

        # * ----------------------------------------------------
        # * Reference priority
        #
        # * More specific references should be resolved first.
        # * ----------------------------------------------------

        self.reference_priority = {
            
            "the first one": 100,
            
            "the second one": 100,
            
            "the third one": 100,
            
            "the fourth one": 100,
            
            "the fifth one": 100,
            
            "the sixth one": 100,
            
            "the seventh one": 100,
            
            "the eighth one": 100,
            
            "the ninth one": 100,
            
            "the tenth one": 100,

            "the last one": 100,
            
            "the next one": 100,

            "the previous one": 100,

            "the same one": 100,

            "this": 80,

            "that": 80,

            "these": 80,

            "those": 80,

            "it": 70,

            "same": 60,

        }

    # * ========================================================
    # * Public API
    # * ========================================================

    def resolve(
        self,
        reference: str,
        context=None,
    ) -> ReferenceResolution:

        reference = self._normalize(
            reference
        )

        if not reference:

            return ReferenceResolution(
                resolved=False,
                reason="Empty reference.",
            )

        # * ----------------------------------------------------
        # * Extract context values
        # * ----------------------------------------------------

        values = self._get_context_values(
            context
        )

        # * ----------------------------------------------------
        # * Specific list references
        # * ----------------------------------------------------

        # * ----------------------------------------------------
        # * Generic ordinal list references
        #
        # * Supports:
        #
        # * the first one
        # * the second one
        # * the third one
        # * the fourth one
        # * the fifth one
        # * ...
        #
        # * Convert the spoken ordinal into a zero-based
        # * object-list index.
        # * ----------------------------------------------------

        ordinal_indexes = {

            "the first one": 0,
            "the second one": 1,
            "the third one": 2,
            "the fourth one": 3,
            "the fifth one": 4,
            "the sixth one": 5,
            "the seventh one": 6,
            "the eighth one": 7,
            "the ninth one": 8,
            "the tenth one": 9,

        }

        if reference in ordinal_indexes:

            return self._resolve_index(
                reference,
                values,
                ordinal_indexes[
                    reference
                ]
            )

        # * ----------------------------------------------------
        # * Next
        # * ----------------------------------------------------

        if reference == "the next one":

            return self._resolve_relative(
                reference,
                values,
                direction=1,
            )

        # * ----------------------------------------------------
        # * Previous
        # * ----------------------------------------------------

        if reference == "the previous one":

            return self._resolve_relative(
                reference,
                values,
                direction=-1,
            )

        # * ----------------------------------------------------
        # * Last
        # * ----------------------------------------------------

        if reference == "the last one":

            return self._resolve_last(
                reference,
                values
            )

        # * ----------------------------------------------------
        # * Same
        # * ----------------------------------------------------

        if reference in {
            "the same one",
            "same",
        }:

            return self._resolve_same(
                reference,
                values
            )

        # * ----------------------------------------------------
        # * Generic singular references
        # * ----------------------------------------------------

        if reference == "it":

            return self._resolve_it(
                values
            )

        if reference in {
            "this",
            "that",
        }:

            return self._resolve_this_that(
                reference,
                values
            )

        if reference in {
            "these",
            "those",
        }:

            return self._resolve_plural(
                reference,
                values
            )

        # * ----------------------------------------------------
        # * Unknown reference
        # * ----------------------------------------------------

        return ReferenceResolution(
            resolved=False,
            reference=reference,
            confidence=0.0,
            reason=(
                "Reference type is not supported."
            ),
        )

    # * ========================================================
    # * Resolve "it"
    # * ========================================================

    def _resolve_it(
        self,
        values: dict
    ) -> ReferenceResolution:

        # * ----------------------------------------------------
        # * Highest priority:
        # * explicitly referenced object
        # * ----------------------------------------------------

        if values["referenced_object"] is not None:

            return self._success(
                reference="it",
                value=values["referenced_object"],
                source="referenced_object",
                confidence=0.95,
                reason=(
                    "Resolved 'it' using the previous "
                    "referenced object."
                ),
            )

        # * ----------------------------------------------------
        # * Current object
        # * ----------------------------------------------------

        if values["object"] is not None:

            return self._success(
                reference="it",
                value=values["object"],
                source="object",
                confidence=0.90,
                reason=(
                    "Resolved 'it' using the current "
                    "conversation object."
                ),
            )

        # * ----------------------------------------------------
        # * Last result
        # * ----------------------------------------------------

        if values["last_result"] is not None:

            return self._success(
                reference="it",
                value=values["last_result"],
                source="last_result",
                confidence=0.80,
                reason=(
                    "Resolved 'it' using the last result."
                ),
            )

        # * ----------------------------------------------------
        # * No safe resolution
        # * ----------------------------------------------------

        return self._unresolved(
            "it",
            "No suitable object exists in context."
        )

    # * ========================================================
    # * Resolve "this" / "that"
    # * ========================================================

    def _resolve_this_that(
        self,
        reference: str,
        values: dict
    ) -> ReferenceResolution:

        # * ----------------------------------------------------
        # * Explicit referenced object
        # * ----------------------------------------------------

        if values["referenced_object"] is not None:

            return self._success(
                reference=reference,
                value=values["referenced_object"],
                source="referenced_object",
                confidence=0.95,
                reason=(
                    f"Resolved '{reference}' using the "
                    "previous referenced object."
                ),
            )

        # * ----------------------------------------------------
        # * Current object
        # * ----------------------------------------------------

        if values["object"] is not None:

            return self._success(
                reference=reference,
                value=values["object"],
                source="object",
                confidence=0.90,
                reason=(
                    f"Resolved '{reference}' using the "
                    "current conversation object."
                ),
            )

        # * ----------------------------------------------------
        # * Last result
        # * ----------------------------------------------------

        if values["last_result"] is not None:

            return self._success(
                reference=reference,
                value=values["last_result"],
                source="last_result",
                confidence=0.80,
                reason=(
                    f"Resolved '{reference}' using "
                    "the last result."
                ),
            )

        return self._unresolved(
            reference,
            (
                "No suitable contextual object exists "
                "for this reference."
            )
        )

    # * ========================================================
    # * Resolve plural references
    # * ========================================================

    def _resolve_plural(
        self,
        reference: str,
        values: dict
    ) -> ReferenceResolution:

        # * ----------------------------------------------------
        # * Plural object
        # * ----------------------------------------------------

        plural = values.get(
            "objects"
        )

        if plural:

            return self._success(
                reference=reference,
                value=plural,
                source="objects",
                confidence=0.90,
                reason=(
                    f"Resolved '{reference}' using "
                    "the contextual object list."
                ),
            )

        # * ----------------------------------------------------
        # * Last result may itself be a list
        # * ----------------------------------------------------

        if isinstance(
            values["last_result"],
            (list, tuple)
        ):

            return self._success(
                reference=reference,
                value=values["last_result"],
                source="last_result",
                confidence=0.85,
                reason=(
                    f"Resolved '{reference}' using "
                    "the last result list."
                ),
            )

        return self._unresolved(
            reference,
            (
                "No plural object list exists "
                "in conversation context."
            )
        )

    # * ========================================================
    # * Resolve "same"
    # * ========================================================

    def _resolve_same(
        self,
        reference: str,
        values: dict
    ) -> ReferenceResolution:

        if values["referenced_object"] is not None:

            return self._success(
                reference=reference,
                value=values["referenced_object"],
                source="referenced_object",
                confidence=0.95,
                reason=(
                    "Resolved 'same' using the previous "
                    "referenced object."
                ),
            )

        if values["object"] is not None:

            return self._success(
                reference=reference,
                value=values["object"],
                source="object",
                confidence=0.90,
                reason=(
                    "Resolved 'same' using the current "
                    "conversation object."
                ),
            )

        return self._unresolved(
            reference,
            "No previous object exists."
        )

    # * ========================================================
    # * Resolve indexed reference
    # * ========================================================

    def _resolve_index(
        self,
        reference: str,
        values: dict,
        index: int
    ) -> ReferenceResolution:

        objects = values.get(
            "objects"
        )

        # * ----------------------------------------------------
        # * Browser search results
        #
        # * Google/Bing/browser search results live in the
        # * centralized BrowserContext rather than the generic
        # * conversation context.
        #
        # * Use them when the conversational object list is
        # * not available.
        # * ----------------------------------------------------

        if not objects:

            try:

                application = str(
                    values.get(
                        "application"
                    )
                    or ""
                ).strip().lower()

                skill = str(
                    values.get(
                        "skill"
                    )
                    or ""
                ).strip().lower()

                if application in {
                    "google",
                    "bing",
                    "browser",
                    "web",
                } or skill == "browser":

                    from core.browser_context import (
                        browser_context,
                    )

                    objects = (
                        browser_context.last_search_results
                    )

                    if objects:

                        print(
                            "[REFERENCE] Using browser "
                            f"search results: {len(objects)}"
                        )

            except Exception as e:

                print(
                    "[REFERENCE] Browser context lookup "
                    f"failed: {e}"
                )

        # * ----------------------------------------------------
        # * No object list
        # * ----------------------------------------------------

        if not objects:

            return self._unresolved(
                reference,
                (
                    "No object list exists for "
                    "indexed reference resolution."
                )
            )

        # * ----------------------------------------------------
        # * Validate collection
        # * ----------------------------------------------------

        if not isinstance(
            objects,
            (list, tuple)
        ):

            return self._unresolved(
                reference,
                "Context objects are not a list."
            )

        # * ----------------------------------------------------
        # * Boundary protection
        # * ----------------------------------------------------

        if index < 0:

            return self._unresolved(
                reference,
                "Requested object index is invalid."
            )

        if index >= len(objects):

            return self._unresolved(
                reference,
                (
                    "Requested object index does "
                    "not exist."
                )
            )

        # * ----------------------------------------------------
        # * Resolve actual contextual object
        # * ----------------------------------------------------

        return self._success(
            reference=reference,
            value=objects[index],
            source="browser_context"
            if objects
            else "objects",
            confidence=0.96,
            reason=(
                f"Resolved '{reference}' from "
                "the contextual result list."
            ),
        )
        
    # * ========================================================
    # * Resolve Relative
    # * ========================================================

    def _resolve_relative(
        self,
        reference: str,
        values: dict,
        direction: int,
    ) -> ReferenceResolution:

        objects = values.get(
            "objects"
        )

        # * ----------------------------------------------------
        # * Browser / YouTube relative references
        #
        # * Use the centralized BrowserContext when available.
        #
        # * This preserves the authoritative YouTube position
        # * maintained by the browser subsystem.
        # * ----------------------------------------------------

        try:

            application = values.get(
                "application"
            )

            if application == "youtube":

                from core.browser_reference import (
                    browser_reference_resolver,
                )

                if direction > 0:

                    browser_result = (
                        browser_reference_resolver.next_youtube()
                    )

                else:

                    browser_result = (
                        browser_reference_resolver.previous_youtube()
                    )

                if browser_result is not None:

                    return self._success(
                        reference=reference,
                        value=browser_result,
                        source="browser_context.youtube",
                        confidence=0.96,
                        reason=(
                            f"Resolved '{reference}' "
                            "using the active YouTube position."
                        ),
                    )

        except Exception as e:

            print(
                "[REFERENCE] "
                f"YouTube relative resolution failed: {e}"
            )

        # * ----------------------------------------------------
        # * Generic contextual relative resolution
        # * ----------------------------------------------------

        if not isinstance(
            objects,
            (list, tuple)
        ) or not objects:

            return self._unresolved(
                reference,
                (
                    "No object list exists for "
                    "relative reference resolution."
                )
            )

        # * ----------------------------------------------------
        # * Find the current object.
        #
        # * Priority:
        # * 1. explicit referenced object
        # * 2. current object
        # * ----------------------------------------------------

        current = (
            values.get("referenced_object")
            or values.get("object")
        )

        if current is None:

            return self._unresolved(
                reference,
                (
                    "No current contextual object exists "
                    "for relative reference resolution."
                )
            )

        # * ----------------------------------------------------
        # * Locate current object in the contextual list.
        # * ----------------------------------------------------

        try:

            current_index = objects.index(
                current
            )

        except ValueError:

            return self._unresolved(
                reference,
                (
                    "Current contextual object is not "
                    "present in the object list."
                )
            )

        target_index = (
            current_index + direction
        )

        # * ----------------------------------------------------
        # * Boundary protection.
        # * ----------------------------------------------------

        if target_index < 0:

            return self._unresolved(
                reference,
                "Already at the first contextual object."
            )

        if target_index >= len(objects):

            return self._unresolved(
                reference,
                "Already at the last contextual object."
            )

        return self._success(
            reference=reference,
            value=objects[target_index],
            source="objects",
            confidence=0.95,
            reason=(
                f"Resolved '{reference}' relative to "
                f"the current contextual object."
            ),
        )

    # * ========================================================
    # * Resolve Last
    # * ========================================================

    def _resolve_last(
        self,
        reference: str,
        values: dict
    ) -> ReferenceResolution:

        objects = values.get(
            "objects"
        )

        # * ----------------------------------------------------
        # * Object collection
        # * ----------------------------------------------------

        if isinstance(
            objects,
            (list, tuple)
        ) and objects:

            return self._success(
                reference=reference,
                value=objects[-1],
                source="objects",
                confidence=0.95,
                reason=(
                    f"Resolved '{reference}' using "
                    "the last contextual object."
                ),
            )

        # * ----------------------------------------------------
        # * Last result
        #
        # * Only use it if it is itself a collection.
        # * ----------------------------------------------------

        last_result = values.get(
            "last_result"
        )

        if isinstance(
            last_result,
            (list, tuple)
        ) and last_result:

            return self._success(
                reference=reference,
                value=last_result[-1],
                source="last_result",
                confidence=0.90,
                reason=(
                    f"Resolved '{reference}' using "
                    "the last item from the last result."
                ),
            )

        # * ----------------------------------------------------
        # * No safe resolution
        # * ----------------------------------------------------

        return self._unresolved(
            reference,
            (
                "No object collection exists for "
                "the last-item reference."
            )
        )

    # * ========================================================
    # * Context Extraction
    # * ========================================================

    @staticmethod
    def _get_context_values(
        context
    ) -> dict:

        values = {

            "object": None,

            "objects": None,

            "referenced_object": None,

            "last_result": None,

            "task": None,

            "application": None,

            "skill": None,

            "intent": None,

            "action": None,

        }

        if context is None:

            return values

        # * ----------------------------------------------------
        # * ConversationContextManager
        # * ----------------------------------------------------

        if hasattr(
            context,
            "get"
        ):

            for key in values:

                try:

                    values[key] = context.get(
                        key
                    )

                except Exception:

                    pass

            return values

        # * ----------------------------------------------------
        # * ConversationContext dataclass
        # * ----------------------------------------------------

        for key in values:

            try:

                values[key] = getattr(
                    context,
                    key,
                    None
                )

            except Exception:

                pass

        # * ----------------------------------------------------
        # * Dictionary
        # * ----------------------------------------------------

        if isinstance(
            context,
            dict
        ):

            for key in values:

                if key in context:

                    values[key] = context[key]

        return values

    # * ========================================================
    # * Normalize
    # * ========================================================

    @staticmethod
    def _normalize(
        reference: str
    ) -> str:

        return (
            reference
            .lower()
            .strip()
        )

    # * ========================================================
    # * Success
    # * ========================================================

    @staticmethod
    def _success(
        reference,
        value,
        source,
        confidence,
        reason
    ) -> ReferenceResolution:

        return ReferenceResolution(

            resolved=True,

            reference=reference,

            value=value,

            source=source,

            confidence=confidence,

            reason=reason,

        )

    # * ========================================================
    # * Unresolved
    # * ========================================================

    @staticmethod
    def _unresolved(
        reference,
        reason
    ) -> ReferenceResolution:

        return ReferenceResolution(

            resolved=False,

            reference=reference,

            value=None,

            source=None,

            confidence=0.0,

            reason=reason,

        )


# * ============================================================
# * Shared Resolver
# * ============================================================

reference_resolver = ReferenceResolver()


# * ============================================================
# * Convenience Function
# * ============================================================

def resolve_reference(
    reference: str,
    context=None,
) -> ReferenceResolution:

    return reference_resolver.resolve(
        reference=reference,
        context=context,
    )