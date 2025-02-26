"""
Character Manager Module

This module provides functionality for managing character assignments to LLMs.
"""

import logging
from typing import Dict, List, Optional, Tuple

from models import Character, InvalidLLMError
from llm_factory import LLMFactory


class CharacterManager:
    """
    Manages character assignments to different LLM systems.
    
    This class handles adding, removing, and retrieving character assignments
    for different LLMs in the system.
    
    Attributes:
        characters (Dict[str, Character]): Maps character names to Character objects
        llm_to_character (Dict[str, str]): Maps LLM names to character names
    """
    
    def __init__(self):
        """Initialize a new CharacterManager."""
        self.characters: Dict[str, Character] = {}
        self.llm_to_character: Dict[str, str] = {}
        logging.info("CharacterManager initialized")
    
    def assign_character(self, llm_name: str, character_name: str, background: str = "") -> Character:
        """
        Assign a character to an LLM.
        
        Args:
            llm_name (str): LLM to assign the character to
            character_name (str): Name of the character
            background (str, optional): Background story for the character
            
        Returns:
            Character: The created Character object
            
        Raises:
            InvalidLLMError: If the LLM is not valid
        """
        llm_name = llm_name.lower()
        
        # Validate LLM name
        if llm_name not in LLMFactory.VALID_LLMS:
            raise InvalidLLMError(
                f"Unknown LLM: {llm_name}. Available options: {', '.join(LLMFactory.VALID_LLMS)}"
            )
        
        # Clear any existing assignment for this character name
        for existing_char in list(self.characters.keys()):
            if existing_char.lower() == character_name.lower():
                self._remove_character(existing_char)
                break
        
        # Clear any existing character for this LLM
        if llm_name in self.llm_to_character:
            old_character = self.llm_to_character[llm_name]
            self._remove_character(old_character)
        
        # Create and assign the new character
        character = Character(
            character_name=character_name,
            llm_name=llm_name,
            background=background
        )
        
        self.characters[character_name] = character
        self.llm_to_character[llm_name] = character_name
        
        logging.info(f"Assigned character '{character_name}' to {llm_name}")
        return character
    
    def get_character_for_llm(self, llm_name: str) -> Optional[Character]:
        """
        Get the character assigned to an LLM.
        
        Args:
            llm_name (str): Name of the LLM
            
        Returns:
            Optional[Character]: The character assigned to the LLM, or None if no character is assigned
        """
        character_name = self.llm_to_character.get(llm_name.lower())
        if character_name:
            return self.characters.get(character_name)
        return None
    
    def get_llm_for_character(self, character_name: str) -> Optional[str]:
        """
        Get the LLM assigned to a character.
        
        Args:
            character_name (str): Name of the character
            
        Returns:
            Optional[str]: The LLM assigned to the character, or None if character does not exist
        """
        # Look for case-insensitive match
        for name, character in self.characters.items():
            if name.lower() == character_name.lower():
                return character.llm_name
        return None
    
    def _remove_character(self, character_name: str) -> None:
        """
        Remove a character assignment.
        
        Args:
            character_name (str): Name of the character to remove
        """
        if character_name in self.characters:
            llm_name = self.characters[character_name].llm_name
            del self.characters[character_name]
            
            # Also remove from llm_to_character mapping
            if llm_name in self.llm_to_character and self.llm_to_character[llm_name] == character_name:
                del self.llm_to_character[llm_name]
    
    def clear_characters(self) -> None:
        """Clear all character assignments."""
        self.characters.clear()
        self.llm_to_character.clear()
        logging.info("All character assignments cleared")
    
    def get_all_characters(self) -> List[Character]:
        """
        Get all characters.
        
        Returns:
            List[Character]: List of all Character objects
        """
        return list(self.characters.values())
    
    def parse_character_addressing(self, message: str) -> Tuple[Optional[str], str]:
        """
        Parse character addressing in messages.
        
        Args:
            message (str): Original message with possible character addressing
            
        Returns:
            Tuple[Optional[str], str]: (llm_name, cleaned_message)
        """
        # Check if message starts with a character name (case insensitive)
        for character_name, character in self.characters.items():
            if (message.lower().startswith(character_name.lower() + ",") or
                message.lower().startswith(character_name.lower() + " ")):
                # Remove the character name from the beginning of the message
                cleaned = message[len(character_name):].lstrip(" ,")
                return character.llm_name, cleaned
        
        # No character addressing found
        return None, message