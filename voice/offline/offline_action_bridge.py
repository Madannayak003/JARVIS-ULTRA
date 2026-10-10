"""Offline adapter for the shared JARVIS route and action layers.

Offline mode changes providers, not capabilities. This module deliberately
contains no duplicate skills or app/browser implementations; it only decides
whether an existing plan is local, network-dependent, or conversational and
hands local plans to the existing executor.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum

from core.executor import execute_ai_plan
from core.fast_router import fast_route
from core.skill_categories import action_requires_network
from config.settings import get_assistant_aliases, get_assistant_display_name


class OfflineRoute(str, Enum):
    LOCAL_ACTION = "LOCAL_ACTION"
    NETWORK_REQUIRED = "NETWORK_REQUIRED"
    CONVERSATION = "CONVERSATION"


@dataclass
class OfflineDispatchResult:
    route: OfflineRoute
    plan: list[dict] = field(default_factory=list)
    results: list[object] = field(default_factory=list)
    message: str = ""


class OfflineActionBridge:
    """Classify and execute commands through shared JARVIS components."""

    # * These are aliases for capabilities that already exist in the shared
    # * registry but are not currently covered by the fast router.
    LOCAL_COMMAND_PLANS = {
        "what is my cpu usage": [{"action": "taskmanager"}],
        "show my cpu usage": [{"action": "taskmanager"}],
        "show cpu usage": [{"action": "taskmanager"}],
        "what is my memory usage": [{"action": "taskmanager"}],
        "show system information": [{"action": "taskmanager"}],
        "show system status": [{"action": "taskmanager"}],
        "system information": [{"action": "taskmanager"}],
    }

    HUD_STATUS_COMMANDS = {
        *(f"open {alias} hud" for alias in get_assistant_aliases()),
        *(f"open the {alias} hud" for alias in get_assistant_aliases()),
        "open pywebview",
        "open the pywebview window",
    }

    NETWORK_HINTS = (
        "web search",
        "search google",
        "search youtube",
        "search github",
        "search chatgpt",
        "google search",
        "youtube search",
        "online news",
        "latest news",
        "weather",
        "google maps",
        "youtube",
    )

    def classify(self, command: str) -> OfflineDispatchResult:
        text = " ".join(str(command or "").lower().split())

        if text in self.HUD_STATUS_COMMANDS:
            return OfflineDispatchResult(
                route=OfflineRoute.LOCAL_ACTION,
                message=(
                    f"The {get_assistant_display_name()} HUD is already open."
                ),
            )

        plan = self.LOCAL_COMMAND_PLANS.get(text)
        if plan is None:
            plan = fast_route(text) if text else None

        if plan:
            if any(
                action_requires_network(step.get("action"), step)
                for step in plan
            ):
                return OfflineDispatchResult(
                    route=OfflineRoute.NETWORK_REQUIRED,
                    plan=plan,
                    message=(
                        "I can’t complete that because the internet "
                        "is unavailable in offline mode."
                    ),
                )

            return OfflineDispatchResult(
                route=OfflineRoute.LOCAL_ACTION,
                plan=plan,
            )

        if any(hint in text for hint in self.NETWORK_HINTS):
            return OfflineDispatchResult(
                route=OfflineRoute.NETWORK_REQUIRED,
                message=(
                    "I can’t complete that because the internet "
                    "is unavailable in offline mode."
                ),
            )

        return OfflineDispatchResult(route=OfflineRoute.CONVERSATION)

    def execute(self, result: OfflineDispatchResult) -> OfflineDispatchResult:
        """Execute a local plan synchronously with the shared executor."""

        if result.route != OfflineRoute.LOCAL_ACTION or not result.plan:
            return result

        result.results = execute_ai_plan(
            result.plan,
            threading.Event(),
        ) or []
        return result

    def handle(self, command: str) -> OfflineDispatchResult:
        return self.execute(self.classify(command))
