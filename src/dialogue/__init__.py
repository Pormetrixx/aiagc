"""
Dialogue package initialization
"""

from .dialogue_generator import DialogueGenerator
from .call_flow import CallFlowManager, ConversationPhase

__all__ = [
    "DialogueGenerator",
    "CallFlowManager",
    "ConversationPhase"
]
