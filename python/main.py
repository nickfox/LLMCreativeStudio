# /Users/nickfox137/Documents/llm-creative-studio/python/main.py
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Corrected imports: No leading dots
from config import DATA_DIR
from llms import Gemini, ChatGPT, Claude
from data import load_metadata, select_relevant_documents, read_file_content
from utils import setup_logging, get_cached_response, store_cached_response

# --- Setup Logging ---
setup_logging()

# --- FastAPI App ---
app = FastAPI()


# --- Pydantic Model for Request Body ---
class ChatRequest(BaseModel):
    llm_name: str
    message: str
    user_name: str = "User"  # Optional user name, defaults to "User"
    data_query: str = ""  # Optional data query


@app.post("/chat")
async def chat(chat_request: ChatRequest):
    llm_name = chat_request.llm_name.lower()
    message = chat_request.message
    user_name = chat_request.user_name
    data_query = chat_request.data_query

    logging.info(f"Received request: llm_name={llm_name}, message={message}, user_name={user_name}, data_query={data_query}")

    # Create a cache key
    cache_key = f"{llm_name}:{message}:{data_query}"  # Include data_query in cache key

    # Check cache
    if cached_response := get_cached_response(cache_key):  # Walrus operator!
        return {"response": cached_response["response"], "llm": cached_response["llm"], "user": user_name}

    # Document Selection
    metadata = load_metadata()
    # Always use Gemini for document selection, for now
    relevant_files = await select_relevant_documents(data_query if data_query else message, metadata, Gemini()) #Instantiate Gemini here.
    logging.info(f"Relevant files: {relevant_files}")

    # Load Document Content
    context = ""
    for file_path in relevant_files:
        content = read_file_content(file_path)
        if content:
            context += f"--- Begin {file_path} ---\n{content}\n--- End {file_path} ---\n"

    # Construct Prompt
    if context:
        final_prompt = f"Here is some context:\n{context}\n\nNow answer the following: {message}"
    else:
        final_prompt = message

    try:
        if llm_name == "gemini":
            response_text = await Gemini().get_response(final_prompt) #Instantiate here
        elif llm_name == "chatgpt":
            response_text = await ChatGPT().get_response(final_prompt)
        elif llm_name == "claude":
            response_text = await Claude().get_response(final_prompt)
        else:
            raise HTTPException(status_code=400, detail="Invalid LLM name")

        # Store in cache
        store_cached_response(cache_key, {"response": response_text, "llm": llm_name})

        logging.info(f"Sending response: {response_text}")
        return {"response": response_text, "llm": llm_name, "user": user_name}

    except Exception as e:
        logging.exception(f"Unexpected error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Multi-LLM Chat API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
