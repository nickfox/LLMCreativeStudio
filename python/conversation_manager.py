# /Users/nickfox137/Documents/llm-creative-studio/python/conversation_manager.py
"""
Conversation Manager Module

This module provides the central orchestration for multi-LLM conversations,
handling message routing, conversation modes, and command processing.
"""

import asyncio
import logging
import json
import traceback
from typing import List, Dict, Any, Optional, Tuple, Union, Set

# Import locally when needed to avoid circular imports
# from debate_manager import DebateManager, DebateState

class ConversationManager:
    """
    ConversationManager orchestrates conversations between multiple LLMs.
    
    This class serves as the primary interface for managing multi-LLM conversations
    with different modes (debate, creative, research) and handling turn-taking logic.
    
    Attributes:
        session_id (str): Unique identifier for the conversation session
        conversation_mode (str): Current conversation mode (debate, creative, research, open)
        current_task (str): Current task or topic being discussed
        conversation_history (List[Dict]): Complete history of the conversation
        active_roles (Dict[str, str]): Current role assignments for each LLM
        debug (bool): Whether to enable debug logging
        mention_map (Dict[str, str]): Maps @mentions to LLM names
        characters (Dict[str, str]): Maps character names to LLM names
        llm_to_character (Dict[str, str]): Maps LLM names to character names
    """
    
    # Valid conversation modes
    VALID_MODES = {"open", "debate", "creative", "research"}
    
    # Valid LLM identifiers
    VALID_LLMS = {"claude", "chatgpt", "gemini"}
    
    # Valid roles that can be assigned to LLMs
    VALID_ROLES = {"assistant", "debater", "creative", "researcher"}
    
    def __init__(self, session_id: str, debug: bool = False):
        """
        Initialize a new ConversationManager.
        
        Args:
            session_id (str): Unique identifier for the conversation session
            debug (bool): Whether to enable debug logging
        """
        self.session_id = session_id
        self.debug = debug
        self.conversation_mode = "open"  # Default mode
        self.current_task = ""
        self.conversation_history = []
        self.active_roles = {}  # Maps agent name to current role
        
        # Map short codes to LLM names
        self.mention_map = {
            "@a": "claude",
            "@c": "chatgpt",
            "@g": "gemini",
            "@claude": "claude",
            "@chatgpt": "chatgpt",
            "@gemini": "gemini"
        }
        
        # Character assignments - will be populated when using characters
        self.characters = {}  # Maps character name to LLM
        self.llm_to_character = {}  # Maps LLM to character name
        
        logging.info(f"ConversationManager initialized for session {session_id}")
    
    async def process_message(self, message: str, sender: str, target_llm: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process a new message in the conversation.
        
        This central method handles routing messages to the appropriate LLMs based on
        mentions, processing commands, and managing conversation state.
        
        Args:
            message (str): The message content
            sender (str): Who sent the message (user or an LLM name)
            target_llm (Optional[str]): Specific LLM to target, or None for all
            
        Returns:
            List[Dict[str, Any]]: List of response messages from the LLMs
        """
        try:
            # Check for commands in the message
            if sender == "user" and message.startswith("/"):
                return await self._handle_command(message)
            
            # Check if this is user input for an active debate
            if sender == "user" and hasattr(self, 'debate_manager') and self.debate_manager.is_waiting_for_user():
                return await self.debate_manager.process_user_input(message)
            
            # Parse @mentions or character names if no explicit target is provided
            if target_llm is None:
                target_llm, message = self._parse_addressing(message)
            
            # Add message to conversation history
            self.conversation_history.append({
                "sender": sender,
                "content": message,
                "target": target_llm,
                "timestamp": asyncio.get_event_loop().time()  # Use current time
            })
            
            # Determine which LLMs should respond
            responding_llms = [target_llm] if target_llm else list(self.active_roles.keys())
        
            # If no LLMs have been assigned roles yet, use default set
            if not responding_llms or (len(responding_llms) == 1 and responding_llms[0] is None):
                responding_llms = ["claude", "chatgpt", "gemini"]
            
            # Get responses from each LLM
            responses = []
            for llm_name in responding_llms:
                llm_response = await self._get_llm_response(llm_name, message, sender)
                responses.append({
                    "llm": llm_name,
                    "response": llm_response,
                    "referenced_message_id": None,  # We'll implement this later
                    "message_intent": "response"  # Default intent
                })
            
            return responses
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logging.exception(error_msg)
            return [{"llm": "system", "response": f"Error: {error_msg}"}]
    
    async def generate_llm_response(self, llm_name: str, message: str, include_history: bool = False, use_thinking_mode: bool = False) -> str:
        """
        Generate a response from a specific LLM.
        
        Enhanced version of _get_llm_response that can optionally use thinking mode
        and include or exclude conversation history. Used by debate manager.
        
        Args:
            llm_name (str): Name of the LLM to get response from
            message (str): Message to send to the LLM
            include_history (bool): Whether to include conversation history
            use_thinking_mode (bool): Whether to use Claude's thinking mode (if available)
            
        Returns:
            str: The LLM's response
        """
        logging.info(f"Generating response from {llm_name}, thinking_mode={use_thinking_mode}")
        
        try:
            # Get the LLM instance based on the name
            llm = None
            if llm_name == "claude":
                from llms import Claude
                llm = Claude()
            elif llm_name == "chatgpt":
                from llms import ChatGPT
                llm = ChatGPT()
            elif llm_name == "gemini":
                from llms import Gemini
                llm = Gemini()
            else:
                return f"Error: LLM {llm_name} not found"
            
            # Check if this LLM has a character assigned
            character_name = self.llm_to_character.get(llm_name)
            
            # Get the current role for this LLM
            role = self.active_roles.get(llm_name, "assistant")
            
            # Construct context from conversation history if requested
            context = ""
            if include_history:
                context = self._build_context_for_llm(llm_name)
                message = f"{context}\n\n{message}"
            
            # Prepare character context if applicable
            if character_name:
                character_context = f"You are roleplaying as {character_name}. Respond in character."
                message = f"{character_context}\n\n{message}"
            
            # Get response, with thinking mode if requested and available
            response = ""
            if use_thinking_mode and llm_name == "claude":
                # Only Claude supports thinking mode currently
                response = await llm.autogen_response(message, role, use_thinking=True)
            else:
                response = await llm.autogen_response(message, role)
            
            return response
            
        except Exception as e:
            error_msg = f"Error generating response from {llm_name}: {str(e)}"
            logging.exception(error_msg)
            logging.error(traceback.format_exc())
            return f"Error: Failed to get response from {llm_name}. {str(e)}"
    
    async def _get_llm_response(self, llm_name: str, message: str, sender: str) -> str:
        """
        Get a response from a specific LLM using AutoGen.
        
        Args:
            llm_name (str): Name of the LLM to get response from
            message (str): Message to send to the LLM
            sender (str): Who sent the original message
            
        Returns:
            str: The LLM's response
        """
        logging.info(f"Getting response from {llm_name} for message: {message[:50]}...")
        
        try:
            # Use the generate_llm_response method to get the response
            response = await self.generate_llm_response(llm_name, message)
            
            # Add to conversation history
            character_name = self.llm_to_character.get(llm_name)
            self.conversation_history.append({
                "sender": character_name if character_name else llm_name,
                "content": response,
                "target": sender,
                "timestamp": asyncio.get_event_loop().time(),
                "llm": llm_name  # Store the actual LLM for reference
            })
            
            return response
            
        except Exception as e:
            error_msg = f"Error getting response from {llm_name}: {str(e)}"
            logging.exception(error_msg)
            logging.error(traceback.format_exc())
            return f"Error: Failed to get response from {llm_name}. {str(e)}"
    
    def _build_context_for_llm(self, llm_name: str) -> str:
        """
        Build conversation context for a specific LLM.
        
        This method creates a context string that provides the LLM with information
        about the recent conversation history, current mode, and role assignments.
        
        Args:
            llm_name (str): Name of the LLM to build context for
            
        Returns:
            str: Formatted conversation context
        """
        # Calculate appropriate history length based on conversation length
        # For longer conversations, include more context
        history_length = min(10, max(5, len(self.conversation_history) // 2))
        recent_history = self.conversation_history[-history_length:] if len(self.conversation_history) > history_length else self.conversation_history
        
        # If this LLM has a character, use that in the context
        character_info = ""
        if llm_name in self.llm_to_character:
            character_name = self.llm_to_character[llm_name]
            character_info = f"\nYou are roleplaying as {character_name}. Respond in character.\n"
        
        context_lines = [
            f"Conversation mode: {self.conversation_mode.capitalize()}",
            f"Current topic: {self.current_task}",
            character_info,
            "Recent conversation:"
        ]
        
        for msg in recent_history:
            sender = msg["sender"]
            content = msg["content"]
            target = msg.get("target", "everyone")
            
            # Use character names where appropriate
            display_sender = sender
            if sender in self.llm_to_character:
                display_sender = self.llm_to_character[sender]
            
            display_target = target
            if target in self.llm_to_character:
                display_target = self.llm_to_character[target]
            
            # Format based on who was speaking and to whom
            if target == "everyone" or target is None:
                context_lines.append(f"{display_sender}: {content}")
            else:
                context_lines.append(f"{display_sender} (to {display_target}): {content}")
        
        return "\n".join(context_lines)
    
    def _parse_addressing(self, message: str) -> Tuple[Optional[str], str]:
        """
        Parse addressing in the message to determine target LLM.
        
        This handles both @mentions and character names if character mode is active.
        
        Args:
            message (str): Original message with possible @mentions or character names
            
        Returns:
            Tuple[Optional[str], str]: (target_llm, cleaned_message)
        """
        # First check for @mentions
        for mention, llm in self.mention_map.items():
            if mention in message:
                return llm, message.replace(mention, "").strip()
        
        # Then check for character addressing if characters are defined
        if self.characters:
            # This is a simple approach - would need refinement for real NLP addressing
            for character_name, llm in self.characters.items():
                # Check if message starts with character name (case insensitive)
                if message.lower().startswith(character_name.lower() + ",") or \
                   message.lower().startswith(character_name.lower() + " "):
                    # Remove the character name from the beginning of the message
                    cleaned = message[len(character_name):].lstrip(" ,")
                    return llm, cleaned
        
        # No specific target
        return None, message
    
    async def _handle_command(self, command: str) -> List[Dict[str, Any]]:
        """
        Handle special commands starting with /.
        
        Args:
            command (str): Command string starting with /
            
        Returns:
            List[Dict[str, Any]]: Response messages
        """
        try:
            parts = command.split()
            cmd = parts[0].lower()
            
            if cmd == "/debate":
                # Start a collaborative debate with the fixed format
                # Usage: /debate [topic]
                topic = " ".join(parts[1:]) if len(parts) > 1 else "General discussion"
                
                # Initialize the debate manager if not exists
                if not hasattr(self, 'debate_manager'):
                    from debate_manager import DebateManager
                    self.debate_manager = DebateManager(self)
                
                return await self.debate_manager.start_debate(topic)
            
            elif cmd == "/role":
                # Assign roles to LLMs
                if len(parts) < 3:
                    return [{"llm": "system", "response": "Usage: /role [llm] [role]"}]
                
                llm = parts[1].lower()
                role = parts[2].lower()
                return await self._assign_role(llm, role)
            
            elif cmd == "/mode":
                # Switch conversation mode
                if len(parts) < 2:
                    return [{"llm": "system", "response": "Usage: /mode [debate|creative|research]"}]
                
                mode = parts[1].lower()
                return await self._set_conversation_mode(mode)
            
            elif cmd == "/character":
                # Assign a character to an LLM
                if len(parts) < 3:
                    return [{"llm": "system", "response": "Usage: /character [llm] [character_name]"}]
                
                llm = parts[1].lower()
                character_name = " ".join(parts[2:])
                return self._assign_character(llm, character_name)
            
            elif cmd == "/clear_characters":
                # Clear all character assignments
                self.characters = {}
                self.llm_to_character = {}
                return [{"llm": "system", "response": "All character assignments cleared."}]
            
            elif cmd == "/continue" or cmd == "/continue_debate":
                # Continue a paused debate
                if hasattr(self, 'debate_manager'):
                    from debate_manager import DebateState
                    
                    # Check if we're waiting for user input in a debate
                    if self.debate_manager.is_waiting_for_user():
                        return await self.debate_manager.process_user_input("/continue")
                    
                    # Otherwise, check if debate is active and advance it
                    elif self.debate_manager.state != DebateState.IDLE:
                        return await self.debate_manager.advance_debate()
                    else:
                        return [{"llm": "system", "response": "Debate is already complete. Start a new debate with /debate."}]
                else:
                    return [{"llm": "system", "response": "No active debate found. Start a new debate with /debate."}]
                
            elif cmd == "/help":
                # Show available commands and mention syntax
                return [{"llm": "system", "response": self._get_help_text()}]
            
            # Default response for unknown command
            return [{"llm": "system", "response": f"Unknown command: {cmd}\nType /help to see available commands."}]
            
        except Exception as e:
            error_msg = f"Error processing command {command}: {str(e)}"
            logging.exception(error_msg)
            return [{"llm": "system", "response": f"Error: {error_msg}"}]
    
    async def _start_debate_mode(self, rounds: int, topic: str) -> List[Dict[str, Any]]:
        """
        Start a structured debate on a specific topic.
        
        Args:
            rounds (int): Number of debate rounds
            topic (str): Topic to debate
            
        Returns:
            List[Dict[str, Any]]: Initial responses for the debate
        """
        self.conversation_mode = "debate"
        self.current_task = topic
        
        # For now, return a placeholder response
        return [{
            "llm": "system",
            "response": f"Starting {rounds}-round debate on: {topic}",
            "referenced_message_id": None,
            "message_intent": "system"
        }]
    
    async def _assign_role(self, llm: str, role: str) -> List[Dict[str, Any]]:
        """
        Assign a specific role to an LLM.
        
        Args:
            llm (str): LLM to assign role to
            role (str): Role to assign
            
        Returns:
            List[Dict[str, Any]]: Confirmation message
        """
        # Validate LLM name
        if llm not in self.VALID_LLMS:
            return [{
                "llm": "system",
                "response": f"Unknown LLM: {llm}. Available options: {', '.join(self.VALID_LLMS)}",
                "referenced_message_id": None,
                "message_intent": "system"
            }]
        
        # Validate role
        if role not in self.VALID_ROLES:
            return [{
                "llm": "system",
                "response": f"Invalid role: {role}. Available options: {', '.join(self.VALID_ROLES)}",
                "referenced_message_id": None,
                "message_intent": "system"
            }]
        
        # Update the role
        self.active_roles[llm] = role
        
        # Get character name if assigned
        character_display = ""
        if llm in self.llm_to_character:
            character_display = f" (as {self.llm_to_character[llm]})"
        
        return [{
            "llm": "system",
            "response": f"Assigned role '{role}' to {llm.capitalize()}{character_display}",
            "referenced_message_id": None,
            "message_intent": "system"
        }]
    
    async def _set_conversation_mode(self, mode: str) -> List[Dict[str, Any]]:
        """
        Set the conversation mode.
        
        Args:
            mode (str): Mode to set (debate, creative, research, open)
            
        Returns:
            List[Dict[str, Any]]: Confirmation message
        """
        if mode not in self.VALID_MODES:
            return [{
                "llm": "system",
                "response": f"Invalid mode: {mode}. Valid options: {', '.join(self.VALID_MODES)}",
                "referenced_message_id": None,
                "message_intent": "system"
            }]
        
        old_mode = self.conversation_mode
        self.conversation_mode = mode
        
        # If switching to creative mode and we have characters, remind the user
        character_info = ""
        if mode == "creative" and self.characters:
            character_names = [f"{name} ({llm})" for name, llm in self.characters.items()]
            character_info = f"\n\nActive characters: {', '.join(character_names)}"
        
        return [{
            "llm": "system",
            "response": f"Switched from {old_mode} mode to {mode} mode{character_info}",
            "referenced_message_id": None,
            "message_intent": "system"
        }]
        
    def _assign_character(self, llm: str, character_name: str) -> List[Dict[str, Any]]:
        """
        Assign a character to an LLM for roleplay.
        
        Args:
            llm (str): LLM to assign the character to
            character_name (str): Name of the character to assign
            
        Returns:
            List[Dict[str, Any]]: Confirmation message
        """
        # Validate LLM name
        if llm not in self.VALID_LLMS:
            return [{
                "llm": "system",
                "response": f"Unknown LLM: {llm}. Available options: {', '.join(self.VALID_LLMS)}",
                "referenced_message_id": None,
                "message_intent": "system"
            }]
        
        # Clear any existing assignment for this character name
        for existing_char, existing_llm in list(self.characters.items()):
            if existing_char.lower() == character_name.lower():
                del self.characters[existing_char]
                break
        
        # Clear any existing character for this LLM
        if llm in self.llm_to_character:
            old_character = self.llm_to_character[llm]
            if old_character in self.characters:
                del self.characters[old_character]
        
        # Assign the character
        self.characters[character_name] = llm
        self.llm_to_character[llm] = character_name
        
        return [{
            "llm": "system",
            "response": f"Assigned character '{character_name}' to {llm.capitalize()}",
            "referenced_message_id": None,
            "message_intent": "system"
        }]
    
    def _get_help_text(self) -> str:
        """
        Generate help text explaining available commands and @ designators.
        
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
        if self.characters:
            character_list = "\n### Current Characters\n"
            for character, llm in self.characters.items():
                character_list += f"- {character} ({llm})\n"
            help_text += character_list
            
        return help_text
