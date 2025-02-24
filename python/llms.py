# /Users/nickfox137/Documents/llm-creative-studio/python/llms.py

import anthropic
import google.generativeai as genai
import openai
import logging
import autogen
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from config import OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY, CHATGPT_MODEL, GEMINI_MODEL, CLAUDE_MODEL
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import google.api_core.exceptions

# --- LLM Clients ---
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class LLM:
    """
    Base class for LLM implementations.
    
    This provides common functionality for all LLM types, including
    context formatting and response generation.
    """
    def __init__(self, name: str):
        """
        Initialize an LLM instance.
        
        Args:
            name (str): Name identifier for this LLM
        """
        self.name = name.lower()
        # Set up AutoGen config (will be implemented in subclasses)
        self.autogen_config = None
        self.autogen_agent = None
        
    async def get_response(self, prompt: str, history: List, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Get a response from the LLM.
        
        Args:
            prompt (str): The prompt to send to the LLM
            history (List): Conversation history
            context (Optional[List[Dict]]): Additional context
            
        Returns:
            str: The LLM's response
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement get_response")
    
    async def autogen_response(self, prompt: str, role: str = "assistant") -> str:
        """
        Get a response using AutoGen.
        
        Args:
            prompt (str): The prompt to send to the LLM
            role (str): The role this LLM should adopt
            
        Returns:
            str: The LLM's response
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement autogen_response")

    def format_context_prompt(self, context: Optional[List[Dict[str, Any]]], current_prompt: str) -> str:
        """
        Creates a natural prompt that includes conversation context.
        
        Args:
            context (Optional[List[Dict]]): List of previous messages with metadata
            current_prompt (str): The current prompt/question
            
        Returns:
            str: Formatted prompt with context
        """
        if not context:
            return current_prompt
            
        context_summary = []
        for msg in context:
            sender_name = msg.get('senderName', 'Someone')
            text = msg.get('text', '')
            intent = msg.get('messageIntent', '')
            
            if intent == 'question':
                context_summary.append(f"{sender_name} asked: {text}")
            elif intent == 'agreement':
                context_summary.append(f"{sender_name} agreed, noting: {text}")
            elif intent == 'disagreement':
                context_summary.append(f"{sender_name} had a different view: {text}")
            else:
                context_summary.append(f"{sender_name} said: {text}")
                
        context_text = "\n".join(context_summary)
        return f"""Recent conversation context:
{context_text}

Given this context, please respond to: {current_prompt}

Remember to acknowledge and reference previous speakers naturally when appropriate."""

    def get_role_prompt(self, role: str) -> str:
        """
        Get role-specific prompt guidance.
        
        Args:
            role (str): The role (assistant, debater, creative, researcher)
            
        Returns:
            str: Role-specific prompt guidance
        """
        if role == "debater":
            return """You are participating in a structured debate.
Present logical arguments supported by evidence.
Address counterarguments directly and respectfully.
Be concise but thorough in your reasoning."""
        
        elif role == "creative":
            return """You are in a creative collaboration session.
Think outside the box and offer unique perspectives.
Build on others' ideas and suggest innovative combinations.
Use rich language, metaphors, and expressive descriptions."""
        
        elif role == "researcher":
            return """You are analyzing and discussing research materials.
Prioritize accuracy and cite specific sections when possible.
Consider methodological strengths and limitations.
Connect findings to broader scientific context."""
        
        else:  # Default assistant role
            return """You are a helpful assistant in a group conversation.
Provide clear, accurate information tailored to the query.
When appropriate, acknowledge points made by others in the conversation.
Maintain a natural, conversational tone."""


class ChatGPT(LLM):
    """
    ChatGPT implementation using OpenAI's API.
    
    Supports both LangChain and AutoGen interfaces.
    """
    def __init__(self, model: str = CHATGPT_MODEL):
        """
        Initialize ChatGPT.
        
        Args:
            model (str): OpenAI model to use
        """
        super().__init__("ChatGPT")
        self.model = model
        
        # LangChain setup
        self.prompt_template = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}")
        ])
        self.llm = ChatOpenAI(model=self.model, openai_api_key=OPENAI_API_KEY)
        self.chain = self.prompt_template | self.llm
        
        # AutoGen setup
        self.autogen_config = {
            "config_list": [
                {
                    "model": self.model,
                    "api_key": OPENAI_API_KEY
                }
            ],
            "temperature": 0.7
        }
        
    async def get_response(self, prompt: str, history: List, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Get a response from ChatGPT using LangChain.
        
        Args:
            prompt (str): The prompt to send
            history (List): Conversation history
            context (Optional[List[Dict]]): Additional context
            
        Returns:
            str: ChatGPT's response
            
        Raises:
            HTTPException: For API errors
        """
        try:
            formatted_prompt = self.format_context_prompt(context, prompt)
            response = await self.chain.ainvoke({
                "input": formatted_prompt,
                "history": history
            })
            response_text = response.content.strip()
            return response_text
        except openai.APIConnectionError as e:
            logging.error(f"ChatGPT Connection Error: {e}")
            raise HTTPException(status_code=500, detail=f"ChatGPT Connection Error: {e}")
        except openai.RateLimitError as e:
            logging.error(f"ChatGPT Rate Limit Error: {e}")
            raise HTTPException(status_code=429, detail=f"ChatGPT Rate Limit Error: {e}")
        except openai.APIStatusError as e:
            logging.error(f"ChatGPT API Status Error: {e}")
            raise HTTPException(status_code=e.status_code, detail=f"ChatGPT API Status Error: {e}")
        except Exception as e:
            logging.exception(f"Unexpected ChatGPT Error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected ChatGPT Error: {e}")
    
    async def autogen_response(self, prompt: str, role: str = "assistant") -> str:
        """
        Get a response using AutoGen.
        
        Args:
            prompt (str): The prompt to send
            role (str): Role to adopt
            
        Returns:
            str: ChatGPT's response
        """
        try:
            # Create a temporary agent if needed
            if not self.autogen_agent:
                role_prompt = self.get_role_prompt(role)
                system_message = f"You are ChatGPT. {role_prompt}"
                
                self.autogen_agent = autogen.AssistantAgent(
                    name="ChatGPT",
                    llm_config=self.autogen_config,
                    system_message=system_message
                )
            
            # Use direct API call for now since we're not in a conversation yet
            # Later we'll implement full AutoGen conversation flow
            config_list = self.autogen_config["config_list"]
            client = openai.OpenAI(api_key=config_list[0]["api_key"])
            
            role_prompt = self.get_role_prompt(role)
            messages = [
                {"role": "system", "content": f"You are ChatGPT. {role_prompt}"},
                {"role": "user", "content": prompt}
            ]
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logging.exception(f"Error getting AutoGen response from ChatGPT: {e}")
            return f"Error: Failed to get response from ChatGPT. {str(e)}"


class Gemini(LLM):
    """
    Gemini implementation using Google's API.
    
    Note: AutoGen doesn't directly support Gemini as of this writing,
    so we implement a custom solution.
    """
    def __init__(self, model: str = GEMINI_MODEL):
        """
        Initialize Gemini.
        
        Args:
            model (str): Gemini model to use
        """
        super().__init__("Gemini")
        self.model_name = model
        self.model = genai.GenerativeModel(model_name=self.model_name)
        self.prompt_template = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}")
        ])

    async def get_response(self, prompt: str, history: List, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Get a response from Gemini.
        
        Args:
            prompt (str): The prompt to send
            history (List): Conversation history
            context (Optional[List[Dict]]): Additional context
            
        Returns:
            str: Gemini's response
            
        Raises:
            HTTPException: For API errors
        """
        try:
            formatted_prompt = self.format_context_prompt(context, prompt)
            
            contents = []
            for message in history:
                if isinstance(message, HumanMessage):
                    contents.append({"role": "user", "parts": [message.content]})
                elif isinstance(message, AIMessage):
                    contents.append({"role": "model", "parts": [message.content]})

            contents.append({"role": "user", "parts": [formatted_prompt]})

            response = await self.model.generate_content_async(contents)

            response_text = ""
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    response_text += part.text
            response_text = response_text.strip()

            return response_text

        except google.api_core.exceptions.GoogleAPIError as e:
            logging.error(f"Gemini API Error: {e}")
            if isinstance(e, google.api_core.exceptions.ResourceExhausted):
                raise HTTPException(status_code=429, detail=f"Gemini Resource Exhausted: {e}")
            else:
                raise HTTPException(status_code=500, detail=f"Gemini API Error: {e}")
        except Exception as e:
            logging.exception(f"Unexpected Gemini Error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected Gemini Error: {e}")
    
    async def autogen_response(self, prompt: str, role: str = "assistant") -> str:
        """
        Get a response that simulates AutoGen for Gemini.
        
        Args:
            prompt (str): The prompt to send
            role (str): Role to adopt
            
        Returns:
            str: Gemini's response
        """
        try:
            role_prompt = self.get_role_prompt(role)
            full_prompt = f"""You are Gemini.
{role_prompt}

{prompt}"""

            # Use the direct API
            response = await self.model.generate_content_async(full_prompt)
            
            response_text = ""
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    response_text += part.text
            
            return response_text.strip()
            
        except Exception as e:
            logging.exception(f"Error getting AutoGen response from Gemini: {e}")
            return f"Error: Failed to get response from Gemini. {str(e)}"


class Claude(LLM):
    """
    Claude implementation using Anthropic's API.
    
    Supports both LangChain and AutoGen interfaces.
    """
    def __init__(self, model: str = CLAUDE_MODEL):
        """
        Initialize Claude.
        
        Args:
            model (str): Claude model to use
        """
        super().__init__("Claude")
        self.model = model
        
        # LangChain setup
        self.prompt_template = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}")
        ])
        self.llm = ChatAnthropic(model_name=self.model, anthropic_api_key=ANTHROPIC_API_KEY)
        self.chain = self.prompt_template | self.llm
        
        # AutoGen setup
        self.autogen_config = {
            "config_list": [
                {
                    "model": self.model,
                    "api_key": ANTHROPIC_API_KEY,
                    "base_url": "https://api.anthropic.com",
                }
            ],
            "temperature": 0.7
        }

    async def get_response(self, prompt: str, history: List, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Get a response from Claude using LangChain.
        
        Args:
            prompt (str): The prompt to send
            history (List): Conversation history
            context (Optional[List[Dict]]): Additional context
            
        Returns:
            str: Claude's response
            
        Raises:
            HTTPException: For API errors
        """
        try:
            formatted_prompt = self.format_context_prompt(context, prompt)
            response = await self.chain.ainvoke({
                "input": formatted_prompt,
                "history": history
            })
            response_text = response.content.strip()
            return response_text
        except anthropic.APIConnectionError as e:
            logging.error(f"Claude Connection Error: {e}")
            raise HTTPException(status_code=500, detail=f"Claude Connection Error: {e}")
        except anthropic.RateLimitError as e:
            logging.error(f"Claude Rate Limit Error: {e}")
            raise HTTPException(status_code=429, detail=f"Claude Rate Limit Error: {e}")
        except anthropic.APIStatusError as e:
            logging.error(f"Claude API Status Error: {e}")
            raise HTTPException(status_code=e.status_code, detail=f"Claude API Status Error: {e}")
        except Exception as e:
            logging.exception(f"Unexpected Claude Error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected Claude Error: {e}")
    
    async def autogen_response(self, prompt: str, role: str = "assistant") -> str:
        """
        Get a response using AutoGen.
        
        Args:
            prompt (str): The prompt to send
            role (str): Role to adopt
            
        Returns:
            str: Claude's response
        """
        try:
            # Create Anthropic client
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            
            role_prompt = self.get_role_prompt(role)
            system_prompt = f"You are Claude. {role_prompt}"
            
            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logging.exception(f"Error getting AutoGen response from Claude: {e}")
            return f"Error: Failed to get response from Claude. {str(e)}"
