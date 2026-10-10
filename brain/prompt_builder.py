"""
JARVIS PRO
Stage 4 - Prompt Builder

Builds the final prompt sent to the LLM.

Author: Madan
"""

from __future__ import annotations

from typing import List

from config.settings import get_assistant_display_name
from .context_types import AIContext


class PromptBuilder:

    def __init__(self):

        self.system_prompt = self._build_system_prompt()

    @staticmethod
    def _build_system_prompt() -> str:
        return f"""
You are {get_assistant_display_name()}.

You are an intelligent AI assistant designed to help the user with coding,
automation, planning, research, electronics, IoT, robotics and productivity.

Rules:

- Be accurate.
- Be concise unless detailed explanation is requested.
- Continue conversations naturally.
- Use previous conversation when relevant.
- Use user profile when appropriate.
- Use current screen context when it is relevant to the user's request.
- Never invent facts.
- If information is missing, ask.
""".strip()

    # * --------------------------------------------------

    def _profile_section(
        self,
        context: AIContext
    ) -> str:

        profile = context.profile

        return f"""
========== USER PROFILE ==========

Name: {profile.get("name","")}

Preferred Language: {profile.get("preferred_language","")}

Coding Language: {profile.get("coding_language","")}

IDE: {profile.get("ide","")}

Current Project: {profile.get("current_project","")}

Response Style: {profile.get("response_style","")}
""".strip()

    # * --------------------------------------------------

    def _project_section(
        self,
        context: AIContext
    ) -> str:

        return f"""
========== CURRENT PROJECT ==========

Project:
{context.project.get("name","")}
""".strip()

    # * --------------------------------------------------

    def _screen_section(
        self,
        context: AIContext
    ) -> str:
        """
        Add the latest live screen understanding.

        This section only reads existing screen context.
        It does NOT capture or analyze the screen.
        """

        if not context.screen:

            return ""

        screen = context.screen

        analysis = screen.get(
            "analysis",
            ""
        )

        if not analysis:

            return ""

        return f"""
========== CURRENT SCREEN CONTEXT ==========

The following is the latest understanding of the user's
computer screen from live screen vision.

Analysis:
{analysis}

Provider:
{screen.get("provider", "")}

Model:
{screen.get("model", "")}

Resolution:
{screen.get("resolution", "")}

Source:
{screen.get("source", "")}

Analyzed At:
{screen.get("analyzed_at", "")}
""".strip()

    # * --------------------------------------------------

    def _conversation_section(
        self,
        context: AIContext
    ) -> str:

        if not context.conversation:

            return ""

        lines: List[str] = []

        lines.append(
            "========== RECENT CONVERSATION =========="
        )

        for msg in context.conversation:

            role = msg["role"].capitalize()

            content = msg["content"]

            lines.append(
                f"{role}: {content}"
            )

        return "\n".join(lines)

    # * --------------------------------------------------

    def _memory_section(
        self,
        context: AIContext
    ) -> str:

        if not context.memories:

            return ""

        lines = []

        lines.append(
            "========== RELEVANT MEMORIES =========="
        )

        for memory in context.memories:

            lines.append(
                str(memory)
            )

        return "\n".join(lines)

    # * --------------------------------------------------

    def _planner_section(
        self,
        context: AIContext
    ) -> str:

        if not context.planner:

            return ""

        return f"""
========== PLANNER STATE ==========
{context.planner}
""".strip()

    # * --------------------------------------------------

    def _user_input_section(
        self,
        context: AIContext
    ) -> str:

        return f"""
========== CURRENT REQUEST ==========

{context.user_input}
""".strip()


    # * --------------------------------------------------
    # * Natural Conversation Intelligence
    # * --------------------------------------------------

    def _natural_section(
        self,
        context: AIContext
    ) -> str:
        """
        Add the result of Natural Conversation Intelligence.

        This section tells the LLM what {get_assistant_display_name()} understood
        about the user's request.

        It does NOT execute actions.
        """

        natural = getattr(
            context,
            "natural",
            {}
        )

        if not natural:
            return ""

        lines = [
            "========== NATURAL CONVERSATION INTELLIGENCE ==========",

            f"Intent: {natural.get('intent', '')}",
            f"Mode: {natural.get('mode', '')}",
            f"Confidence: {natural.get('confidence', '')}",
            f"Topic: {natural.get('topic', '')}",
            f"Task: {natural.get('task', '')}",
            f"Subject: {natural.get('object', '')}",
            f"Reference: {natural.get('reference', '')}",
            f"References: {natural.get('references', [])}",
            (
                "Resolved References: "
                f"{natural.get('resolved_references', {})}"
            ),
            f"Application: {natural.get('application', '')}",
            f"Skill: {natural.get('skill', '')}",
            f"Needs AI: {natural.get('needs_ai', False)}",
            f"Needs Action: {natural.get('needs_action', False)}",
            (
                "Needs Clarification: "
                f"{natural.get('needs_clarification', False)}"
            ),
        ]

        instructions = natural.get(
            "instructions",
            ""
        )

        if instructions:

            lines.extend([
                "",
                "Natural handling instructions:",
                instructions,
            ])

        return "\n".join(lines)
    

    # * --------------------------------------------------

    def build(
        self,
        context: AIContext
    ) -> str:

        # * Customize can rename the assistant while the process is running.
        self.system_prompt = self._build_system_prompt()

        sections = [

            self.system_prompt,

            self._profile_section(
                context
            ),

            self._project_section(
                context
            ),

            self._natural_section(
                context
            ),

            self._screen_section(
                context
            ),

            self._conversation_section(
                context
            ),

            self._memory_section(
                context
            ),

            self._planner_section(
                context
            ),

            self._user_input_section(
                context
            )

        ]

        sections = [

            section

            for section in sections

            if section.strip()

        ]

        return "\n\n".join(
            sections
        )
