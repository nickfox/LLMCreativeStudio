# /Users/nickfox137/Documents/llm-creative-studio/python/llms.py

import anthropic
import google.generativeai as genai
import openai
import logging
from typing import List, Optional
from fastapi import HTTPException
from config import OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY, CHATGPT_MODEL, GEMINI_MODEL, CLAUDE_MODEL
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import google.api_core.exceptions

# --- LLM Clients ---
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class LLM:
    def __init__(self, name):
        self.name = name.lower()

    async def get_response(self, prompt, history, context=None):
        raise NotImplementedError("Subclasses must implement get_response")

    def format_context_prompt(self, context, current_prompt):
        """Creates a natural prompt that includes conversation context."""
        if not context:
            return current_prompt
            
        context_summary = []
        for msg in context:
            sender_name = msg['senderName']
            text = msg['text']
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

class ChatGPT(LLM):
    def __init__(self, model=CHATGPT_MODEL):
        super().__init__("ChatGPT")
        self.model = model
        self.prompt_template = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}")
        ])
        self.llm = ChatOpenAI(model=self.model, openai_api_key=OPENAI_API_KEY)
        self.chain = self.prompt_template | self.llm

    async def get_response(self, prompt, history, context=None):
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

class Gemini(LLM):
    def __init__(self, model=GEMINI_MODEL):
        super().__init__("Gemini")
        self.model_name = model
        self.model = genai.GenerativeModel(model_name=self.model_name)
        self.prompt_template = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}")
        ])

    async def get_response(self, prompt, history, context=None):
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

class Claude(LLM):
    def __init__(self, model=CLAUDE_MODEL):
        super().__init__("Claude")
        self.model = model
        self.prompt_template = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}")
        ])
        self.llm = ChatAnthropic(model_name=self.model, anthropic_api_key=ANTHROPIC_API_KEY)
        self.chain = self.prompt_template | self.llm

    async def get_response(self, prompt, history, context=None):
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
            raise HTTPException(status_code=e.status_code, detail=f"Claude API Status Error: {e}, {e.message}")
        except Exception as e:
            logging.exception(f"Unexpected Claude Error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected Claude Error: {e}")
