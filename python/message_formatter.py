"""
Message Formatter Module

This module is responsible for formatting messages for different contexts and scenarios.
It formats messages for display, creates context for LLMs, and formats help text.
"""

import logging
from typing import List, Dict, Any, Optional

from models import Message


class MessageFormatter:
    """
    Formats messages for different contexts and scenarios.
    
    This class centralizes message formatting logic for consistent presentation across
    various parts of the application.
    """
    
    @staticmethod
    def build_context_for_llm(
        conversation_history: List[Message],
        llm_name: str,
        conversation_mode: str,
        current_task: str,
        character_name: Optional[str] = None,
        llm_to_character: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build conversation context for a specific LLM.
        
        Args:
            conversation_history (List[Message]): Complete conversation history
            llm_name (str): Name of the LLM to build context for
            conversation_mode (str): Current conversation mode
            current_task (str): Current task or topic
            character_name (Optional[str]): Name of the character this LLM is roleplaying as
            llm_to_character (Optional[Dict[str, str]]): Map of LLM names to character names
            
        Returns:
            str: Formatted conversation context
        """
        logging.debug(f"Building context for {llm_name}, character={character_name}")
        
        # Calculate appropriate history length based on conversation length
        history_length = min(10, max(5, len(conversation_history) // 2))
        recent_history = conversation_history[-history_length:] if conversation_history else []
        
        # Character info for the context
        character_info = ""
        if character_name:
            character_info = f"\nYou are roleplaying as {character_name}. Respond in character.\n"
        
        # Build the context header
        context_lines = [
            f"Conversation mode: {conversation_mode.capitalize()}",
            f"Current topic: {current_task}",
            character_info,
            "Recent conversation:"
        ]
        
        # Empty dictionary if llm_to_character was not provided
        if llm_to_character is None:
            llm_to_character = {}
        
        # Build the conversation history part
        for msg in recent_history:
            sender = msg.sender
            content = msg.content
            target = msg.target
            
            # Use character names where appropriate
            display_sender = sender
            if sender in llm_to_character:
                display_sender = llm_to_character[sender]
            
            display_target = target
            if target in llm_to_character:
                display_target = llm_to_character[target]
            
            # Format based on who was speaking and to whom
            if target is None or target == "everyone":
                context_lines.append(f"{display_sender}: {content}")
            else:
                context_lines.append(f"{display_sender} (to {display_target}): {content}")
        
        # Join the context into a single string
        return "\n".join(context_lines)
    
    @staticmethod
    def format_help_text(characters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate help text explaining available commands and @ designators.
        
        Args:
            characters (Optional[Dict[str, Any]]): Map of character names to LLM names
            
        Returns:
            str: Formatted help text
        """
        help_text = """
## LLMCreativeStudio Commands

### Directing Messages
- `@a` or `@claude` - Direct message to Claude only
- `@c` or `@chatgpt` - Direct message to ChatGPT only
- `@g` or `@gemini` - Direct message to Gemini only
- No @ mention - Message goes to all LLMs
- When using characters, simply address them by name: "John, what do you think about..."

### Special Commands
- `/debate [topic]` - Start a collaborative structured debate on a topic
  Example: `/debate Benefits of artificial intelligence`
  Round 1: Opening statements from all participants (including you)
  Round 2: Defense and cross-examination with questions
  Round 3: Responses to questions and final positions
  Round 4: Weighted consensus voting (percentage allocations)
  Final: Synthesized summary based on consensus scores

  You will be prompted for input after each round.

- `/continue` - Continue the debate without adding your input for the current round

- `/role [llm] [role]` - Assign a specific role to an LLM
  Example: `/role claude researcher` or `/role chatgpt debater`
  Available roles: assistant, debater, creative, researcher

- `/mode [type]` - Switch conversation mode
  Available modes: open, debate, creative, research
  Example: `/mode creative`

- `/character [llm] [character_name]` - Assign a character to an LLM for roleplay
  Example: `/character claude John Lennon` or `/character chatgpt Paul McCartney`

- `/clear_characters` - Remove all character assignments

- `/help` - Show this help message

### Examples
- "@a Can you research quantum computing papers?"
- "John, what do you think about this melody?"
- "/debate Is AI consciousness possible?"
- "/character claude John Lennon" followed by "/character chatgpt Paul McCartney"
"""
        
        # Add character info if any characters are assigned
        if characters and len(characters) > 0:
            character_list = "\n### Current Characters\n"
            for character, llm in characters.items():
                character_list += f"- {character} ({llm})\n"
            help_text += character_list
            
        return help_text
        
    @staticmethod
    def format_system_message(message: str) -> Dict[str, Any]:
        """
        Format a system message.
        
        Args:
            message (str): Message content
            
        Returns:
            Dict[str, Any]: Formatted system message
        """
        return {
            "llm": "system",
            "response": message,
            "referenced_message_id": None,
            "message_intent": "system"
        }
        
    @staticmethod
    def format_response_message(llm_name: str, response: str) -> Dict[str, Any]:
        """
        Format a response message.
        
        Args:
            llm_name (str): Name of the LLM that generated the response
            response (str): Response content
            
        Returns:
            Dict[str, Any]: Formatted response message
        """
        return {
            "llm": llm_name,
            "response": response,
            "referenced_message_id": None,
            "message_intent": "response"
        }