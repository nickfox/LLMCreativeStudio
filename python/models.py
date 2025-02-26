"""
Models Module

This module defines the core data models and custom exceptions for the application.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Union


class ConversationMode(Enum):
    """Enum representing the various conversation modes available."""
    OPEN = "open"
    DEBATE = "debate"
    CREATIVE = "creative"
    RESEARCH = "research"


class Role(Enum):
    """Enum representing the various roles an LLM can take."""
    ASSISTANT = "assistant"
    DEBATER = "debater"
    CREATIVE = "creative" 
    RESEARCHER = "researcher"


@dataclass
class Message:
    """Represents a single message in a conversation."""
    sender: str
    content: str
    target: Optional[str] = None
    timestamp: Optional[float] = None
    llm: Optional[str] = None
    referenced_message_id: Optional[str] = None
    message_intent: Optional[str] = None
    debate_round: Optional[int] = None
    debate_state: Optional[str] = None
    character_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to a dictionary."""
        return {
            "sender": self.sender,
            "content": self.content,
            "target": self.target,
            "timestamp": self.timestamp,
            "llm": self.llm,
            "referenced_message_id": self.referenced_message_id,
            "message_intent": self.message_intent,
            "debate_round": self.debate_round,
            "debate_state": self.debate_state,
            "character_name": self.character_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from a dictionary."""
        return cls(
            sender=data["sender"],
            content=data["content"],
            target=data.get("target"),
            timestamp=data.get("timestamp"),
            llm=data.get("llm"),
            referenced_message_id=data.get("referenced_message_id"),
            message_intent=data.get("message_intent"),
            debate_round=data.get("debate_round"),
            debate_state=data.get("debate_state"),
            character_name=data.get("character_name")
        )


@dataclass
class Character:
    """Represents a character that an LLM can roleplay as."""
    character_name: str
    llm_name: str
    background: str
    id: Optional[str] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert character to a dictionary."""
        return {
            "character_name": self.character_name,
            "llm_name": self.llm_name,
            "background": self.background,
            "id": self.id,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Create a character from a dictionary."""
        return cls(
            character_name=data["character_name"],
            llm_name=data["llm_name"],
            background=data.get("background", ""),
            id=data.get("id"),
            created_at=data.get("created_at")
        )


# Custom exceptions
class LLMException(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMException):
    """Raised when connection to an LLM service fails."""
    pass


class LLMResponseError(LLMException):
    """Raised when an LLM returns an error response."""
    pass


class InvalidConversationModeError(Exception):
    """Raised when an invalid conversation mode is specified."""
    pass


class InvalidRoleError(Exception):
    """Raised when an invalid role is assigned."""
    pass


class InvalidLLMError(Exception):
    """Raised when an invalid LLM is specified."""
    pass