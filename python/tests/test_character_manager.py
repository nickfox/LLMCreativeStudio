"""
Tests for the CharacterManager class.
"""

import pytest
from unittest.mock import MagicMock, patch
import logging

from character_manager import CharacterManager
from models import Character, InvalidLLMError

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


class TestCharacterManager:
    """Tests for the CharacterManager class."""

    @pytest.fixture
    def character_manager(self):
        """Create a character manager for testing."""
        return CharacterManager()

    def test_initialization(self, character_manager):
        """Test that the character manager initializes correctly."""
        assert character_manager.characters == {}
        assert character_manager.llm_to_character == {}

    def test_assign_character(self, character_manager):
        """Test assigning a character to an LLM."""
        character = character_manager.assign_character("claude", "John Lennon", "Beatles member")
        
        assert character.character_name == "John Lennon"
        assert character.llm_name == "claude"
        assert character.background == "Beatles member"
        
        assert character_manager.characters["John Lennon"] == character
        assert character_manager.llm_to_character["claude"] == "John Lennon"

    def test_assign_character_with_invalid_llm(self, character_manager):
        """Test assigning a character to an invalid LLM."""
        with pytest.raises(InvalidLLMError):
            character_manager.assign_character("invalid_llm", "Character Name")

    def test_assign_character_replaces_existing_character_name(self, character_manager):
        """Test that assigning a new character with the same name replaces the old one."""
        character_manager.assign_character("claude", "John Lennon")
        character_manager.assign_character("gemini", "John Lennon")
        
        # The character name should now be assigned to gemini
        assert character_manager.characters["John Lennon"].llm_name == "gemini"
        assert "claude" not in character_manager.llm_to_character
        assert character_manager.llm_to_character["gemini"] == "John Lennon"

    def test_assign_character_replaces_existing_llm_assignment(self, character_manager):
        """Test that assigning a new character to an LLM replaces its old character."""
        character_manager.assign_character("claude", "John Lennon")
        character_manager.assign_character("claude", "Paul McCartney")
        
        # Claude should now be assigned to Paul McCartney
        assert "John Lennon" not in character_manager.characters
        assert character_manager.characters["Paul McCartney"].llm_name == "claude"
        assert character_manager.llm_to_character["claude"] == "Paul McCartney"

    def test_get_character_for_llm(self, character_manager):
        """Test getting the character assigned to an LLM."""
        character = character_manager.assign_character("claude", "John Lennon")
        
        retrieved_character = character_manager.get_character_for_llm("claude")
        assert retrieved_character == character
        
        # Test with no character assigned
        assert character_manager.get_character_for_llm("gemini") is None

    def test_get_llm_for_character(self, character_manager):
        """Test getting the LLM assigned to a character."""
        character_manager.assign_character("claude", "John Lennon")
        
        llm = character_manager.get_llm_for_character("John Lennon")
        assert llm == "claude"
        
        # Test with case insensitivity
        llm = character_manager.get_llm_for_character("john lennon")
        assert llm == "claude"
        
        # Test with non-existent character
        assert character_manager.get_llm_for_character("Paul McCartney") is None

    def test_clear_characters(self, character_manager):
        """Test clearing all character assignments."""
        character_manager.assign_character("claude", "John Lennon")
        character_manager.assign_character("gemini", "Paul McCartney")
        
        character_manager.clear_characters()
        
        assert character_manager.characters == {}
        assert character_manager.llm_to_character == {}

    def test_get_all_characters(self, character_manager):
        """Test getting all characters."""
        char1 = character_manager.assign_character("claude", "John Lennon")
        char2 = character_manager.assign_character("gemini", "Paul McCartney")
        
        all_characters = character_manager.get_all_characters()
        
        assert len(all_characters) == 2
        assert char1 in all_characters
        assert char2 in all_characters

    def test_parse_character_addressing(self, character_manager):
        """Test parsing character addressing in messages."""
        character_manager.assign_character("claude", "John")
        character_manager.assign_character("gemini", "Paul")
        
        # Test with character at beginning with comma
        llm, message = character_manager.parse_character_addressing("John, hello there")
        assert llm == "claude"
        assert message == "hello there"
        
        # Test with character at beginning with space
        llm, message = character_manager.parse_character_addressing("Paul what do you think?")
        assert llm == "gemini"
        assert message == "what do you think?"
        
        # Test with case insensitivity
        llm, message = character_manager.parse_character_addressing("john, hello there")
        assert llm == "claude"
        assert message == "hello there"
        
        # Test with no character addressing
        llm, message = character_manager.parse_character_addressing("Hello everyone")
        assert llm is None
        assert message == "Hello everyone"