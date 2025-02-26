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

from models import Message, ConversationMode, Role, InvalidLLMError, InvalidRoleError, InvalidConversationModeError
from llm_factory import LLMFactory
from character_manager import CharacterManager
from message_router import MessageRouter
from message_formatter import MessageFormatter


class ConversationManager:
    """
    ConversationManager orchestrates conversations between multiple LLMs.
    
    This class serves as the primary interface for managing multi-LLM conversations
    with different modes (debate, creative, research) and handling turn-taking logic.
    
    Attributes:
        session_id (str): Unique identifier for the conversation session
        conversation_mode (str): Current conversation mode (debate, creative, research, open)
        current_task (str): Current task or topic being discussed
        conversation_history (List[Message]): Complete history of the conversation
        active_roles (Dict[str, str]): Current role assignments for each LLM
        debug (bool): Whether to enable debug logging
    """
    
    def __init__(self, session_id: str, debug: bool = False):
        """
        Initialize a new ConversationManager.
        
        Args:
            session_id (str): Unique identifier for the conversation session
            debug (bool): Whether to enable debug logging
        """
        self.session_id = session_id
        self.debug = debug
        self.conversation_mode = ConversationMode.OPEN.value  # Default mode
        self.current_task = ""
        self.conversation_history: List[Message] = []
        self.active_roles: Dict[str, str] = {}  # Maps agent name to current role
        
        # Initialize component managers
        self.message_router = MessageRouter()
        self.character_manager = CharacterManager()
        
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
            if sender == "user" and self.message_router.is_command(message):
                return await self._handle_command(message)
            
            # Check if this is user input for an active debate
            if sender == "user" and hasattr(self, 'debate_manager') and self.debate_manager.is_waiting_for_user():
                return await self.debate_manager.process_user_input(message)
            
            # Parse message addressing - first check @mentions, then character addressing
            if target_llm is None:
                # First check for @mentions
                target_llm, parsed_message = self.message_router.parse_mentions(message)
                
                # If no @mention was found, check for character addressing
                if target_llm is None:
                    target_llm, parsed_message = self.character_manager.parse_character_addressing(message)
                else:
                    parsed_message = message
            else:
                parsed_message = message
            
            # Create and add message to conversation history
            timestamp = asyncio.get_event_loop().time()
            new_message = Message(
                sender=sender,
                content=parsed_message,
                target=target_llm,
                timestamp=timestamp
            )
            self.conversation_history.append(new_message)
            
            # Determine which LLMs should respond
            responding_llms = self.message_router.determine_recipient_llms(
                target_llm,
                parsed_message,
                self.active_roles
            )
            
            # Get responses from each LLM
            responses = []
            for llm_name in responding_llms:
                llm_response = await self._get_llm_response(llm_name, parsed_message, sender)
                responses.append(MessageFormatter.format_response_message(llm_name, llm_response))
            
            return responses
        except InvalidLLMError as e:
            error_msg = f"Invalid LLM specified: {str(e)}"
            logging.error(error_msg)
            return [MessageFormatter.format_system_message(f"Error: {error_msg}")]
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logging.exception(error_msg)
            return [MessageFormatter.format_system_message(f"Error: {error_msg}")]
    
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
            # Get the LLM instance via factory
            llm = LLMFactory.get_llm(llm_name)
            
            # Check if this LLM has a character assigned
            character = self.character_manager.get_character_for_llm(llm_name)
            character_name = character.character_name if character else None
            
            # Get the current role for this LLM
            role = self.active_roles.get(llm_name, Role.ASSISTANT.value)
            
            # Construct context from conversation history if requested
            if include_history:
                # Convert llm_to_character to a dict for the formatter
                llm_to_character = {llm: char.character_name 
                                    for llm, char in 
                                    ((name, self.character_manager.get_character_for_llm(name)) 
                                     for name in LLMFactory.VALID_LLMS) 
                                    if char is not None}
                
                context = MessageFormatter.build_context_for_llm(
                    conversation_history=self.conversation_history,
                    llm_name=llm_name,
                    conversation_mode=self.conversation_mode,
                    current_task=self.current_task,
                    character_name=character_name,
                    llm_to_character=llm_to_character
                )
                message = f"{context}\n\n{message}"
            
            # Prepare character context if applicable
            elif character_name:
                character_context = f"You are roleplaying as {character_name}. Respond in character."
                message = f"{character_context}\n\n{message}"
            
            # Get response, with thinking mode if requested and available
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
            raise
    
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
            
            # Get character name if assigned
            character = self.character_manager.get_character_for_llm(llm_name)
            
            # Add to conversation history
            timestamp = asyncio.get_event_loop().time()
            response_message = Message(
                sender=character.character_name if character else llm_name,
                content=response,
                target=sender,
                timestamp=timestamp,
                llm=llm_name,
                character_name=character.character_name if character else None
            )
            self.conversation_history.append(response_message)
            
            return response
            
        except Exception as e:
            error_msg = f"Error getting response from {llm_name}: {str(e)}"
            logging.exception(error_msg)
            logging.error(traceback.format_exc())
            return f"Error: Failed to get response from {llm_name}. {str(e)}"
    
    async def _handle_command(self, command: str) -> List[Dict[str, Any]]:
        """
        Handle special commands starting with /.
        
        Args:
            command (str): Command string starting with /
            
        Returns:
            List[Dict[str, Any]]: Response messages
        """
        try:
            cmd, args = self.message_router.parse_command(command)
            
            if cmd == "/debate":
                # Start a collaborative debate with the fixed format
                # Usage: /debate [topic]
                topic = " ".join(args) if args else "General discussion"
                
                # Initialize the debate manager if not exists
                if not hasattr(self, 'debate_manager'):
                    from debate_manager import DebateManager
                    self.debate_manager = DebateManager(self)
                
                return await self.debate_manager.start_debate(topic)
            
            elif cmd == "/role":
                # Assign roles to LLMs
                if len(args) < 2:
                    return [MessageFormatter.format_system_message("Usage: /role [llm] [role]")]
                
                llm = args[0].lower()
                role = args[1].lower()
                return await self._assign_role(llm, role)
            
            elif cmd == "/mode":
                # Switch conversation mode
                if len(args) < 1:
                    return [MessageFormatter.format_system_message("Usage: /mode [debate|creative|research]")]
                
                mode = args[0].lower()
                return await self._set_conversation_mode(mode)
            
            elif cmd == "/character":
                # Assign a character to an LLM
                if len(args) < 2:
                    return [MessageFormatter.format_system_message("Usage: /character [llm] [character_name]")]
                
                llm = args[0].lower()
                character_name = " ".join(args[1:])
                return self._assign_character(llm, character_name)
            
            elif cmd == "/clear_characters":
                # Clear all character assignments
                self.character_manager.clear_characters()
                return [MessageFormatter.format_system_message("All character assignments cleared.")]
            
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
                        return [MessageFormatter.format_system_message("Debate is already complete. Start a new debate with /debate.")]
                else:
                    return [MessageFormatter.format_system_message("No active debate found. Start a new debate with /debate.")]
                
            elif cmd == "/help":
                # Show available commands and mention syntax
                characters_dict = {char.character_name: char.llm_name 
                                 for char in self.character_manager.get_all_characters()}
                help_text = MessageFormatter.format_help_text(characters_dict)
                return [MessageFormatter.format_system_message(help_text)]
            
            # Default response for unknown command
            return [MessageFormatter.format_system_message(
                f"Unknown command: {cmd}\nType /help to see available commands."
            )]
            
        except Exception as e:
            error_msg = f"Error processing command {command}: {str(e)}"
            logging.exception(error_msg)
            return [MessageFormatter.format_system_message(f"Error: {error_msg}")]
    
    async def _assign_role(self, llm: str, role: str) -> List[Dict[str, Any]]:
        """
        Assign a specific role to an LLM.
        
        Args:
            llm (str): LLM to assign role to
            role (str): Role to assign
            
        Returns:
            List[Dict[str, Any]]: Confirmation message
        """
        try:
            # Validate LLM name
            if llm not in LLMFactory.VALID_LLMS:
                raise InvalidLLMError(
                    f"Unknown LLM: {llm}. Available options: {', '.join(LLMFactory.VALID_LLMS)}"
                )
            
            # Validate role
            valid_roles = [r.value for r in Role]
            if role not in valid_roles:
                raise InvalidRoleError(
                    f"Invalid role: {role}. Available options: {', '.join(valid_roles)}"
                )
            
            # Update the role
            self.active_roles[llm] = role
            
            # Get character name if assigned
            character = self.character_manager.get_character_for_llm(llm)
            character_display = f" (as {character.character_name})" if character else ""
            
            return [MessageFormatter.format_system_message(
                f"Assigned role '{role}' to {llm.capitalize()}{character_display}"
            )]
            
        except (InvalidLLMError, InvalidRoleError) as e:
            return [MessageFormatter.format_system_message(f"Error: {str(e)}")]
    
    async def _set_conversation_mode(self, mode: str) -> List[Dict[str, Any]]:
        """
        Set the conversation mode.
        
        Args:
            mode (str): Mode to set (debate, creative, research, open)
            
        Returns:
            List[Dict[str, Any]]: Confirmation message
        """
        try:
            # Validate mode
            valid_modes = [m.value for m in ConversationMode]
            if mode not in valid_modes:
                raise InvalidConversationModeError(
                    f"Invalid mode: {mode}. Valid options: {', '.join(valid_modes)}"
                )
            
            old_mode = self.conversation_mode
            self.conversation_mode = mode
            
            # If switching to creative mode and we have characters, remind the user
            character_info = ""
            characters = self.character_manager.get_all_characters()
            if mode == ConversationMode.CREATIVE.value and characters:
                character_names = [f"{char.character_name} ({char.llm_name})" for char in characters]
                character_info = f"\n\nActive characters: {', '.join(character_names)}"
            
            return [MessageFormatter.format_system_message(
                f"Switched from {old_mode} mode to {mode} mode{character_info}"
            )]
            
        except InvalidConversationModeError as e:
            return [MessageFormatter.format_system_message(f"Error: {str(e)}")]
    
    def _assign_character(self, llm: str, character_name: str) -> List[Dict[str, Any]]:
        """
        Assign a character to an LLM for roleplay.
        
        Args:
            llm (str): LLM to assign the character to
            character_name (str): Name of the character to assign
            
        Returns:
            List[Dict[str, Any]]: Confirmation message
        """
        try:
            # Use character manager to assign character
            character = self.character_manager.assign_character(llm, character_name)
            
            return [MessageFormatter.format_system_message(
                f"Assigned character '{character.character_name}' to {llm.capitalize()}"
            )]
            
        except InvalidLLMError as e:
            return [MessageFormatter.format_system_message(f"Error: {str(e)}")]
