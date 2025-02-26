"""
Tests for the MessageFormatter class.
"""

import pytest
import logging
from typing import Dict, List

from message_formatter import MessageFormatter
from models import Message

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


class TestMessageFormatter:
    """Tests for the MessageFormatter class."""

    @pytest.fixture
    def sample_messages(self) -> List[Message]:
        """Create a list of sample messages for testing."""
        return [
            Message(
                sender="user",
                content="Hello, how are you?",
                timestamp=1.0
            ),
            Message(
                sender="claude",
                content="I'm doing well, thank you!",
                target="user",
                timestamp=2.0
            ),
            Message(
                sender="user",
                content="@chatgpt what about you?",
                timestamp=3.0
            ),
            Message(
                sender="chatgpt",
                content="I'm also doing great!",
                target="user",
                timestamp=4.0
            )
        ]

    def test_build_context_for_llm_basic(self, sample_messages):
        """Test building basic context for an LLM."""
        context = MessageFormatter.build_context_for_llm(
            conversation_history=sample_messages,
            llm_name="claude",
            conversation_mode="open",
            current_task="General conversation"
        )
        
        # Check for required elements in the context
        assert "Conversation mode: Open" in context
        assert "Current topic: General conversation" in context
        assert "Recent conversation:" in context
        
        # Check for message content in the context
        assert "user: Hello, how are you?" in context
        assert "claude (to user): I'm doing well, thank you!" in context
        assert "user: @chatgpt what about you?" in context
        assert "chatgpt (to user): I'm also doing great!" in context

    def test_build_context_for_llm_with_character(self, sample_messages):
        """Test building context for an LLM with a character assigned."""
        context = MessageFormatter.build_context_for_llm(
            conversation_history=sample_messages,
            llm_name="claude",
            conversation_mode="creative",
            current_task="Role playing",
            character_name="John Lennon"
        )
        
        # Check for character information in the context
        assert "You are roleplaying as John Lennon. Respond in character." in context

    def test_build_context_for_llm_with_llm_to_character_mapping(self, sample_messages):
        """Test building context with character name mappings."""
        llm_to_character = {
            "claude": "John Lennon",
            "chatgpt": "Paul McCartney"
        }
        
        context = MessageFormatter.build_context_for_llm(
            conversation_history=sample_messages,
            llm_name="claude",
            conversation_mode="creative",
            current_task="Role playing",
            character_name="John Lennon",
            llm_to_character=llm_to_character
        )
        
        # Check that character names are used in the context
        assert "John Lennon (to user): I'm doing well, thank you!" in context
        assert "Paul McCartney (to user): I'm also doing great!" in context

    def test_build_context_for_llm_with_targeting(self):
        """Test building context where messages target specific recipients."""
        messages = [
            Message(
                sender="user",
                content="Hello everyone",
                timestamp=1.0
            ),
            Message(
                sender="claude",
                content="Hi there!",
                target="user",
                timestamp=2.0
            ),
            Message(
                sender="user",
                content="Claude, can you help me?",
                target="claude",
                timestamp=3.0
            ),
            Message(
                sender="claude",
                content="Of course, I'd be happy to help.",
                target="user",
                timestamp=4.0
            )
        ]
        
        llm_to_character = {"claude": "John"}
        
        context = MessageFormatter.build_context_for_llm(
            conversation_history=messages,
            llm_name="claude",
            conversation_mode="open",
            current_task="Help session",
            llm_to_character=llm_to_character
        )
        
        # Check that targeting is shown in the context
        assert "user: Hello everyone" in context
        assert "John (to user): Hi there!" in context
        assert "user (to John): Claude, can you help me?" in context
        assert "John (to user): Of course, I'd be happy to help." in context

    def test_format_help_text_no_characters(self):
        """Test formatting help text without characters."""
        help_text = MessageFormatter.format_help_text()
        
        # Check that help text contains key sections
        assert "LLMCreativeStudio Commands" in help_text
        assert "Directing Messages" in help_text
        assert "Special Commands" in help_text
        assert "/debate" in help_text
        assert "/role" in help_text
        assert "/mode" in help_text
        assert "/character" in help_text
        assert "/clear_characters" in help_text
        assert "/help" in help_text
        
        # Check that there is no Current Characters section
        assert "Current Characters" not in help_text

    def test_format_help_text_with_characters(self):
        """Test formatting help text with characters."""
        characters = {
            "John Lennon": "claude",
            "Paul McCartney": "chatgpt"
        }
        
        help_text = MessageFormatter.format_help_text(characters)
        
        # Check that help text contains key sections
        assert "LLMCreativeStudio Commands" in help_text
        
        # Check that Current Characters section is present
        assert "Current Characters" in help_text
        assert "- John Lennon (claude)" in help_text
        assert "- Paul McCartney (chatgpt)" in help_text

    def test_format_system_message(self):
        """Test formatting a system message."""
        message = "This is a system message"
        formatted = MessageFormatter.format_system_message(message)
        
        assert formatted["llm"] == "system"
        assert formatted["response"] == message
        assert formatted["referenced_message_id"] is None
        assert formatted["message_intent"] == "system"

    def test_format_response_message(self):
        """Test formatting a response message."""
        llm_name = "claude"
        response = "This is a response from Claude"
        formatted = MessageFormatter.format_response_message(llm_name, response)
        
        assert formatted["llm"] == llm_name
        assert formatted["response"] == response
        assert formatted["referenced_message_id"] is None
        assert formatted["message_intent"] == "response"