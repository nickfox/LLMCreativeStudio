# /Users/nickfox137/Documents/llm-creative-studio/python/main.py

import asyncio
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, status
from pydantic import BaseModel, ValidationError
from config import DATA_DIR
from llms import Gemini, ChatGPT, Claude
from data import select_relevant_documents, read_file_content
from utils import setup_logging
from data_access import DataAccess
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
DATABASE_URL = "sqlite:///./chat_history.db"
db = SQLDatabase.from_uri(DATABASE_URL, sample_rows_in_table_info=0)
data_access = DataAccess()

class ChatRequest(BaseModel):
    llm_name: str
    message: str
    user_name: str = "User"
    data_query: str = ""
    session_id: str = "default_session"
    conversation_mode: str = "open"
    referenced_message_id: Optional[str] = None
    context: List[dict] = []

def get_message_history(session_id: str):
    return SQLChatMessageHistory(session_id=session_id, connection_string=DATABASE_URL)

async def get_llm_response(llm_name: str, prompt: str, history, context):
    if llm_name == "gemini":
        response_text = await gemini.get_response(prompt, history.messages, context)
    elif llm_name == "chatgpt":
        response_text = await chatgpt.get_response(prompt, history.messages, context)
    elif llm_name == "claude":
        response_text = await claude.get_response(prompt, history.messages, context)
    else:
        raise HTTPException(status_code=400, detail="Invalid LLM name")
    return response_text

@app.post("/chat")
async def chat(chat_request: Request):
    try:
        data = await chat_request.json()
        chat_request_data = ChatRequest(**data)

        llm_name = chat_request_data.llm_name.lower()
        message = chat_request_data.message
        user_name = chat_request_data.user_name
        data_query = chat_request_data.data_query
        session_id = chat_request_data.session_id
        conversation_mode = chat_request_data.conversation_mode
        context = chat_request_data.context

    except ValidationError as e:
        logging.error(f"Validation Error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
    except Exception as e:
        logging.exception(f"Unexpected error in request parsing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    logging.info(f"Received request: llm_name={llm_name}, message={message}, user_name={user_name}, data_query={data_query}, session_id={session_id}, conversation_mode={conversation_mode}")

    # Document Selection
    metadata = data_access.get_all_documents()
    metadata_str = ""
    for item in metadata:
        metadata_str += str(item)
    relevant_files = await select_relevant_documents(data_query if data_query else message, metadata_str, Gemini())
    logging.info(f"Relevant files: {relevant_files}")

    # Load Document Content
    context_docs = ""
    for file_path in relevant_files:
        content = read_file_content(file_path)
        if content:
            context_docs += f"--- Begin {file_path} ---\n{content}\n--- End {file_path} ---\n"

    # Construct Prompt
    if context_docs:
        final_prompt = f"Here is some context:\n{context_docs}\n\nNow answer the following: {message}"
    else:
        final_prompt = message
        
    history = get_message_history(session_id)
    history.add_user_message(message)

    try:
        if llm_name == "all":
            responses = await asyncio.gather(
                gemini.get_response(final_prompt, history.messages, context),
                chatgpt.get_response(final_prompt, history.messages, context),
                claude.get_response(final_prompt, history.messages, context),
                return_exceptions=True
            )
            
            results = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logging.error(f"Error from LLM: {response}")
                else:
                    llm_names = ["Gemini", "ChatGPT", "Claude"]
                    referenced_id = chat_request_data.referenced_message_id
                    message_intent = "response"  # You might want to analyze the response to determine intent
                    
                    results.append({
                        "response": response,
                        "llm": llm_names[i],
                        "user": user_name,
                        "referenced_message_id": referenced_id,
                        "message_intent": message_intent
                    })
                    history.add_ai_message(f"{llm_names[i]}: {response}")

            return results

        else:
            response_text = await get_llm_response(llm_name, final_prompt, history, context)
            history.add_ai_message(response_text)
            
            referenced_id = chat_request_data.referenced_message_id
            message_intent = "response"  # You might want to analyze the response to determine intent
            
            logging.info(f"Sending response: {response_text}")
            return {
                "response": response_text,
                "llm": llm_name,
                "user": user_name,
                "referenced_message_id": referenced_id,
                "message_intent": message_intent
            }

    except Exception as e:
        logging.exception(f"Unexpected error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Multi-LLM Chat API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
