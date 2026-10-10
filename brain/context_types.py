"""
JARVIS PRO
Stage 4 - Context Types

Shared data models for the AI Brain.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AIContext:

    # * Current user request
    user_input: str = ""

    # * Permanent profile
    profile: Dict[str, Any] = field(
        default_factory=dict
    )

    # * Recent conversation
    conversation: List[Dict[str, Any]] = field(
        default_factory=list
    )

    # * Retrieved long-term memory
    memories: List[Any] = field(
        default_factory=list
    )

    # * Planner state
    planner: Dict[str, Any] = field(
        default_factory=dict
    )

    # * Active project
    project: Dict[str, Any] = field(
        default_factory=dict
    )

    # * Live screen context
    screen: Dict[str, Any] = field(
        default_factory=dict
    )

    # * Tool information
    tools: Dict[str, Any] = field(
        default_factory=dict
    )
    
    # * Natural Conversation Intelligence
    natural: Dict[str, Any] = field(
        default_factory=dict
    )

    # * Metadata
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )