# /Users/nickfox137/Documents/llm-creative-studio/python/main.py
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request, Depends, status
from pydantic import BaseModel, ValidationError  # Import ValidationError

# Corrected imports: No leading dots
from config import DATA_DIR
from llms import Gemini, ChatGPT, Claude
from data import load_metadata, select_relevant_documents, read_file_content
from utils import setup_logging

# --- LangChain Imports ---
#Correct Import, again!
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.chat_message_histories import SQLChatMessageHistory

# --- Setup Logging ---
setup_logging()

# --- FastAPI App ---
app = FastAPI()

# --- LLM Instances ---
gemini = Gemini()
chatgpt = ChatGPT()
claude = Claude()

# --- Database Setup ---
DATABASE_URL = "sqlite:///./chat_history.db"  # Use SQLite
db = SQLDatabase.from_uri(DATABASE_URL, sample_rows_in_table_info=0)

# --- Pydantic Model for Request Body ---
class ChatRequest(BaseModel):
    llm_name: str
    message: str
    user_name: str = "User"  # Optional user name, defaults to "User"
    data_query: str = ""  # Optional data query
    session_id: str = "default_session"  # Add session ID


def get_message_history(session_id: str):
    return SQLChatMessageHistory(session_id=session_id, connection_string=DATABASE_URL)

async def get_llm_response(llm_name: str, prompt: str, history):
    if llm_name == "gemini":
        response_text = await gemini.get_response(prompt, history.messages) #Pass in history
    elif llm_name == "chatgpt":
        response_text = await chatgpt.get_response(prompt, history.messages) #Pass in history
    elif llm_name == "claude":
        response_text = await claude.get_response(prompt, history.messages)
    else:
        raise HTTPException(status_code=400, detail="Invalid LLM name")
    return response_text

@app.post("/chat")
async def chat(chat_request: Request): # Change this line
    try:
        # Manually parse JSON and validate against the model
        data = await chat_request.json()
        chat_request_data = ChatRequest(**data)

        llm_name = chat_request_data.llm_name.lower()
        message = chat_request_data.message
        user_name = chat_request_data.user_name
        data_query = chat_request_data.data_query
        session_id = chat_request_data.session_id # Get the session ID

    except ValidationError as e:
        logging.error(f"Validation Error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
    except Exception as e:
        logging.exception(f"Unexpected error in request parsing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    logging.info(f"Received request: llm_name={llm_name}, message={message}, user_name={user_name}, data_query={data_query}, session_id={session_id}")

    # Document Selection
    metadata = load_metadata()
    relevant_files = await select_relevant_documents(data_query if data_query else message, metadata, Gemini())
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
        
    history = get_message_history(session_id) # Get the history
    history.add_user_message(message) #Record the users message

    try:
        response_text = await get_llm_response(llm_name, final_prompt, history) #Call the llm
        history.add_ai_message(response_text) #record the AIs response
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
