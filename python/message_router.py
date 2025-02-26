"""
Message Router Module

This module provides functionality for routing messages to the appropriate LLMs
based on mentions, commands, and addressing.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any

from models import Message, InvalidLLMError


class MessageRouter:
    """
    Routes messages to the appropriate LLMs based on mentions and addressing.
    
    This class handles the logic for determining which LLMs should receive a message
    based on direct mentions, character addressing, and default routing.
    
    Attributes:
        mention_map (Dict[str, str]): Maps mention codes to LLM names
    """
    
    def __init__(self):
        """Initialize a new MessageRouter."""
        # Map short codes to LLM names
        self.mention_map = {
            "@a": "claude",
            "@c": "claude",  # Changed from "chatgpt" to "claude"
            "@g": "gemini",
            "@claude": "claude",
            "@chatgpt": "chatgpt",
            "@gemini": "gemini"
        }
        logging.info("MessageRouter initialized")
    
    def parse_mentions(self, message: str) -> Tuple[Optional[str], str]:
        """
        Parse @mentions in the message to determine target LLM.
        
        Args:
            message (str): Original message with possible @mentions
            
        Returns:
            Tuple[Optional[str], str]: (target_llm, cleaned_message)
        """
        # Sort mentions by length (longest first) to avoid partial matches
        # For example, "@claude" should be checked before "@c" to avoid "@claude" being parsed as "@c" + "laude"
        sorted_mentions = sorted(self.mention_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for mention, llm in sorted_mentions:
            if mention in message:
                return llm, message.replace(mention, "").strip()
        
        # No mention found
        return None, message
    
    def determine_recipient_llms(
        self,
        target_llm: Optional[str],
        message: str,
        active_roles: Dict[str, str],
        default_llms: List[str] = None
    ) -> List[str]:
        """
        Determine which LLMs should receive a message.
        
        Args:
            target_llm (Optional[str]): Specific LLM to target
            message (str): Message content
            active_roles (Dict[str, str]): Map of LLM names to their active roles
            default_llms (List[str]): Default LLMs to use if no roles are defined
            
        Returns:
            List[str]: List of LLM names that should receive the message
        """
        if default_llms is None:
            default_llms = ["claude", "chatgpt", "gemini"]
        
        # If there's a specific target, use only that
        if target_llm:
            return [target_llm]
        
        # Use active roles if available
        if active_roles:
            return list(active_roles.keys())
        
        # Fall back to default LLMs
        return default_llms
    
    def is_command(self, message: str) -> bool:
        """
        Check if a message is a command.
        
        Args:
            message (str): Message to check
            
        Returns:
            bool: True if the message is a command, False otherwise
        """
        return message.startswith("/")
    
    def parse_command(self, command: str) -> Tuple[str, List[str]]:
        """
        Parse a command into its command name and arguments.
        
        Args:
            command (str): Full command string with arguments
            
        Returns:
            Tuple[str, List[str]]: (command_name, arguments)
        """
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        return cmd, args