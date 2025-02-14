# /Users/nickfox137/Documents/llm-creative-studio/python/llms.py
import anthropic
import google.generativeai as genai
import openai
from config import OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY, CHATGPT_MODEL, GEMINI_MODEL, CLAUDE_MODEL
import logging
from fastapi import HTTPException

# --- LangChain Imports ---
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic  # Import ChatAnthropic
# Add this import!
import google.api_core.exceptions


# --- LLM Clients ---
# We are creating the clients, but using Langchain to make the calls.
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# --- LLM Classes ---
class LLM:
    def __init__(self, name):
        self.name = name.lower()

    async def get_response(self, prompt, history): #Now takes a history
        raise NotImplementedError("Subclasses must implement get_response")

class ChatGPT(LLM):
    def __init__(self, model=CHATGPT_MODEL):
        super().__init__("ChatGPT")
        self.model = model
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="history"),
                ("user", "{input}"),
            ]
        )
        #Use ChatOpenAI for integration
        self.llm = ChatOpenAI(model=self.model, openai_api_key=OPENAI_API_KEY)
        self.chain = self.prompt_template | self.llm


    async def get_response(self, prompt, history):
        try:
            # Invoke the chain, passing in the history and the current input prompt
            response = await self.chain.ainvoke({"input": prompt, "history": history})
            response_text = response.content.strip() # Get the text from the response
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
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="history"),
                ("user", "{input}"),
            ]
        )

    async def get_response(self, prompt, history):
        try:
            # Convert history to Gemini's format
            contents = []
            for message in history:
                if isinstance(message, HumanMessage):
                    contents.append({"role": "user", "parts": [message.content]})
                elif isinstance(message, AIMessage):
                    contents.append({"role": "model", "parts": [message.content]})

            contents.append({"role": "user", "parts": [prompt]}) #Current message

            response = await self.model.generate_content_async(contents)

            response_text = ""
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    response_text += part.text
            response_text = response_text.strip()

            return response_text

        except google.api_core.exceptions.GoogleAPIError as e:  # Correctly catch Google API errors
            logging.error(f"Gemini API Error: {e}")
            if isinstance(e, google.api_core.exceptions.ResourceExhausted):
                raise HTTPException(status_code=429, detail=f"Gemini Resource Exhausted: {e}") #Specific message
            else:
                raise HTTPException(status_code=500, detail=f"Gemini API Error: {e}")
        except Exception as e:
            logging.exception(f"Unexpected Gemini Error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected Gemini Error: {e}")

class Claude(LLM):
    def __init__(self, model=CLAUDE_MODEL):
        super().__init__("Claude")
        self.model = model
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="history"),
                ("user", "{input}"),
            ]
        )
        # Use ChatAnthropic for integration
        self.llm = ChatAnthropic(model_name=self.model, anthropic_api_key=ANTHROPIC_API_KEY)
        self.chain = self.prompt_template | self.llm

    async def get_response(self, prompt, history):
        try:
            # Invoke the chain, passing in the history and the current input prompt.
            response = await self.chain.ainvoke({"input": prompt, "history": history})
            response_text = response.content.strip() #Get the text from the response.
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
