"""
Tests for the MessageRouter class.
"""

import pytest
from unittest.mock import MagicMock, patch
import logging

from message_router import MessageRouter
from models import InvalidLLMError

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


class TestMessageRouter:
    """Tests for the MessageRouter class."""

    @pytest.fixture
    def message_router(self):
        """Create a message router for testing."""
        return MessageRouter()

    def test_initialization(self, message_router):
        """Test that the message router initializes correctly."""
        assert "@a" in message_router.mention_map
        assert "@c" in message_router.mention_map
        assert "@g" in message_router.mention_map
        assert "@claude" in message_router.mention_map
        assert "@chatgpt" in message_router.mention_map
        assert "@gemini" in message_router.mention_map

    def test_parse_mentions(self, message_router):
        """Test parsing mentions in messages."""
        # Test with @a mention
        llm, message = message_router.parse_mentions("@a hello there")
        assert llm == "claude"
        assert message == "hello there"
        
        # Test with @claude mention
        llm, message = message_router.parse_mentions("@claude what's up?")
        assert llm == "claude"
        assert message == "what's up?"  # Now the longer mention "@claude" is matched before "@c"
        
        # Test with @c mention
        llm, message = message_router.parse_mentions("@c help me with this")
        assert llm == "claude"  # This should be "claude" as per the mentions map
        assert message == "help me with this"
        
        # Test with @chatgpt mention
        llm, message = message_router.parse_mentions("@chatgpt write some code")
        assert llm == "chatgpt"
        assert message == "write some code"
        
        # Test with @g mention
        llm, message = message_router.parse_mentions("@g explain this concept")
        assert llm == "gemini"
        assert message == "explain this concept"
        
        # Test with @gemini mention
        llm, message = message_router.parse_mentions("@gemini what's new?")
        assert llm == "gemini"
        assert message == "what's new?"
        
        # Test with no mention
        llm, message = message_router.parse_mentions("Hello everyone")
        assert llm is None
        assert message == "Hello everyone"

    def test_determine_recipient_llms_with_target(self, message_router):
        """Test determining recipient LLMs with a specific target."""
        active_roles = {"claude": "assistant", "chatgpt": "researcher"}
        
        # When target is specified, only that LLM should be returned
        recipients = message_router.determine_recipient_llms("claude", "message", active_roles)
        assert recipients == ["claude"]
        
        # Test with a different target
        recipients = message_router.determine_recipient_llms("gemini", "message", active_roles)
        assert recipients == ["gemini"]

    def test_determine_recipient_llms_with_active_roles(self, message_router):
        """Test determining recipient LLMs from active roles."""
        active_roles = {"claude": "assistant", "chatgpt": "researcher"}
        
        # When no target is specified, all LLMs with active roles should be returned
        recipients = message_router.determine_recipient_llms(None, "message", active_roles)
        assert set(recipients) == {"claude", "chatgpt"}

    def test_determine_recipient_llms_with_defaults(self, message_router):
        """Test determining recipient LLMs with default values."""
        # When no target and no active roles, should return default LLMs
        recipients = message_router.determine_recipient_llms(None, "message", {})
        assert set(recipients) == {"claude", "chatgpt", "gemini"}
        
        # Test with custom defaults
        recipients = message_router.determine_recipient_llms(
            None, "message", {}, ["claude", "chatgpt"]
        )
        assert set(recipients) == {"claude", "chatgpt"}

    def test_is_command(self, message_router):
        """Test checking if a message is a command."""
        assert message_router.is_command("/help") is True
        assert message_router.is_command("/debate topic") is True
        assert message_router.is_command("Hello everyone") is False
        assert message_router.is_command("This is not a /command") is False

    def test_parse_command(self, message_router):
        """Test parsing a command into its name and arguments."""
        # Test simple command
        cmd, args = message_router.parse_command("/help")
        assert cmd == "/help"
        assert args == []
        
        # Test command with single argument
        cmd, args = message_router.parse_command("/mode creative")
        assert cmd == "/mode"
        assert args == ["creative"]
        
        # Test command with multiple arguments
        cmd, args = message_router.parse_command("/character claude John Lennon")
        assert cmd == "/character"
        assert args == ["claude", "John", "Lennon"]
        
        # Test command with quoted arguments (quotes should be preserved)
        cmd, args = message_router.parse_command('/debate "Is AI consciousness possible?"')
        assert cmd == "/debate"
        assert args == ['"Is', 'AI', 'consciousness', 'possible?"']