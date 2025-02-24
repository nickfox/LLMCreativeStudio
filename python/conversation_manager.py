# /Users/nickfox137/Documents/llm-creative-studio/python/conversation_manager.py

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Tuple

class ConversationManager:
    """
    ConversationManager orchestrates conversations between multiple LLMs using AutoGen.
    
    This class serves as the primary interface for managing multi-LLM conversations
    with different modes (debate, creative, research) and handling turn-taking logic.
    
    Attributes:
        session_id (str): Unique identifier for the conversation session
        agents (Dict[str, Agent]): Dictionary of AutoGen agents for each LLM
        user_agent (UserProxyAgent): AutoGen agent representing the user
        conversation_mode (str): Current conversation mode (debate, creative, research)
        current_task (str): Current task or topic being discussed
        conversation_history (List[Dict]): Complete history of the conversation
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
        self.conversation_mode = "open"  # Default mode
        self.current_task = ""
        self.conversation_history = []
        self.active_roles = {}  # Maps agent name to current role
        
        logging.info(f"ConversationManager initialized for session {session_id}")
    
    async def process_message(self, message: str, sender: str, target_llm: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process a new message in the conversation.
        
        Args:
            message (str): The message content
            sender (str): Who sent the message (user or an LLM name)
            target_llm (Optional[str]): Specific LLM to target, or None for all
            
        Returns:
            List[Dict[str, Any]]: List of response messages from the LLMs
        """
        # Check for commands in the message
        if sender == "user" and message.startswith("/"):
            return await self._handle_command(message)
        
        # Parse @mentions if no explicit target is provided
        if target_llm is None and "@" in message:
            target_llm, message = self._parse_mentions(message)
        
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
        
        # Get the current role for this LLM
        role = self.active_roles.get(llm_name, "assistant")
        
        # Construct context from conversation history
        context = self._build_context_for_llm(llm_name)
        
        # Get response using AutoGen
        try:
            response = await llm.autogen_response(message, role)
        except Exception as e:
            logging.exception(f"Error getting response from {llm_name}: {e}")
            response = f"Error: Failed to get response from {llm_name}. {str(e)}"
        
        # Add to conversation history
        self.conversation_history.append({
            "sender": llm_name,
            "content": response,
            "target": sender,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        return response
    
    def _build_context_for_llm(self, llm_name: str) -> str:
        """
        Build conversation context for a specific LLM.
        
        Args:
            llm_name (str): Name of the LLM to build context for
            
        Returns:
            str: Formatted conversation context
        """
        # Get recent conversation history (last 10 messages)
        recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        
        context_lines = [
            "Recent conversation:",
            f"Current mode: {self.conversation_mode}",
            f"Current topic: {self.current_task}",
            ""
        ]
        
        for msg in recent_history:
            sender = msg["sender"]
            content = msg["content"]
            target = msg.get("target", "everyone")
            
            # Format based on who was speaking and to whom
            if target == "everyone":
                context_lines.append(f"{sender}: {content}")
            else:
                context_lines.append(f"{sender} (to {target}): {content}")
        
        return "\n".join(context_lines)
    
    def _parse_mentions(self, message: str) -> Tuple[Optional[str], str]:
        """
        Parse @mentions in the message to determine target LLM.
        
        Args:
            message (str): Original message with possible @mentions
            
        Returns:
            Tuple[Optional[str], str]: (target_llm, cleaned_message)
        """
        # Simple @mention parsing logic
        if "@a" in message:
            return "claude", message.replace("@a", "").strip()
        elif "@c" in message:
            return "chatgpt", message.replace("@c", "").strip()
        elif "@g" in message:
            return "gemini", message.replace("@g", "").strip()
        
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
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "/debate":
            # Start a debate session
            rounds = int(parts[1]) if len(parts) > 1 else 3
            return await self._start_debate_mode(rounds, " ".join(parts[2:]))
        
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
            
        elif cmd == "/help":
            # Show available commands and mention syntax
            return [{"llm": "system", "response": self._get_help_text()}]
        
        # Default response for unknown command
        return [{"llm": "system", "response": f"Unknown command: {cmd}\nType /help to see available commands."}]
    
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
        valid_llms = ["claude", "chatgpt", "gemini"]
        if llm not in valid_llms:
            return [{
                "llm": "system",
                "response": f"Unknown LLM: {llm}. Available options: {', '.join(valid_llms)}",
                "referenced_message_id": None,
                "message_intent": "system"
            }]
        
        # Update the role
        self.active_roles[llm] = role
        
        return [{
            "llm": "system",
            "response": f"Assigned role '{role}' to {llm.capitalize()}",
            "referenced_message_id": None,
            "message_intent": "system"
        }]
    
    async def _set_conversation_mode(self, mode: str) -> List[Dict[str, Any]]:
        """
        Set the conversation mode.
        
        Args:
            mode (str): Mode to set (debate, creative, research)
            
        Returns:
            List[Dict[str, Any]]: Confirmation message
        """
        valid_modes = ["debate", "creative", "research", "open"]
        if mode not in valid_modes:
            return [{
                "llm": "system",
                "response": f"Invalid mode: {mode}. Valid options: {', '.join(valid_modes)}",
                "referenced_message_id": None,
                "message_intent": "system"
            }]
        
        self.conversation_mode = mode
        
        return [{
            "llm": "system",
            "response": f"Switched to {mode} mode",
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

### Special Commands
- `/debate [rounds] [topic]` - Start a structured debate with specified number of rounds on a topic
  Example: `/debate 3 Benefits of artificial intelligence`

- `/role [llm] [role]` - Assign a specific role to an LLM
  Example: `/role claude researcher` or `/role chatgpt debater`
  Available roles: assistant, debater, creative, researcher

- `/mode [type]` - Switch conversation mode
  Available modes: open, debate, creative, research
  Example: `/mode creative`

- `/help` - Show this help message

### Examples
- "@a Can you research quantum computing papers?"
- "@c What do you think about @g's response?"
- "/debate 2 Climate change solutions"
"""
        return help_text
