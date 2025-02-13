# /Users/nickfox137/Documents/llm-creative-studio/python/llms.py
import anthropic
import google.generativeai as genai
import openai
from config import OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY, CHATGPT_MODEL, GEMINI_MODEL, CLAUDE_MODEL #Notice the change here.
import logging
from fastapi import HTTPException

# --- LLM Clients ---
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# --- LLM Classes ---
class LLM:
    def __init__(self, name):
        self.name = name.lower()
        self.history = []

    async def get_response(self, prompt):
        raise NotImplementedError("Subclasses must implement get_response")

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})


class ChatGPT(LLM):
    def __init__(self, model=CHATGPT_MODEL):
        super().__init__("ChatGPT")
        self.model = model

    async def get_response(self, prompt):
        self.add_message("user", prompt)
        try:
            response = openai_client.chat.completions.create(
                model=self.model, messages=self.history
            )
            response_text = response.choices[0].message.content.strip()
            self.add_message("assistant", response_text)
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
            logging.exception(f"Unexpected ChatGPT Error: {e}") #Logs the entire call stack
            raise HTTPException(status_code=500, detail=f"Unexpected ChatGPT Error: {e}")


class Gemini(LLM):
    def __init__(self, model=GEMINI_MODEL):
        super().__init__("Gemini")
        self.model_name = model
        self.model = genai.GenerativeModel(model_name=self.model_name)

    async def get_response(self, prompt):
        self.add_message("user", prompt)
        try:
            contents = []
            for message in self.history:
                role = message["role"]
                if role == "user":
                    contents.append({"role": "user", "parts": [message["content"]]})
                else:  # Assume "assistant"
                    contents.append({"role": "model", "parts": [message["content"]]})
            response = await self.model.generate_content_async(contents)

            response_text = ""
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    response_text += part.text
            response_text = response_text.strip()

            self.add_message("assistant", response_text)
            return response_text

        except google.api_core.exceptions.GoogleAPIError as e:
            logging.error(f"Gemini API Error: {e}")
            raise HTTPException(status_code=500, detail=f"Gemini API Error: {e}")
        except Exception as e:
            logging.exception(f"Unexpected Gemini Error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected Gemini Error: {e}")



class Claude(LLM):
    def __init__(self, model=CLAUDE_MODEL):
        super().__init__("Claude")
        self.model = model

    async def get_response(self, prompt):
        self.add_message("user", prompt)
        try:
            response = anthropic_client.messages.create(
                model=self.model,
                max_tokens=1024,  # You might want to adjust this for Haiku
                messages=self.history,
            )
            response_text = response.content[0].text.strip()
            self.add_message("assistant", response_text)
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
