# /Users/nickfox137/Documents/llm-creative-studio/python/main.py

import asyncio
import logging
from typing import List, Dict, Optional, Union
from fastapi import FastAPI, HTTPException, Request, Depends, status
from pydantic import BaseModel, ValidationError
from config import DATA_DIR
from llms import Gemini, ChatGPT, Claude
from data import select_relevant_documents, read_file_content
from utils import setup_logging
from data_access import DataAccess
from conversation_manager import ConversationManager
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.chat_message_histories import SQLChatMessageHistory

# --- Setup Logging ---
setup_logging()

# --- FastAPI App ---
app = FastAPI()

# --- Database Setup ---
DATABASE_URL = "sqlite:///./chat_history.db"
db = SQLDatabase.from_uri(DATABASE_URL, sample_rows_in_table_info=0)
data_access = DataAccess()

# --- Conversation Managers Dictionary ---
# Tracks active conversation managers by session_id
conversation_managers = {}

class ChatRequest(BaseModel):
    """
    Pydantic model for chat requests with enhanced fields for conversation management.
    """
    llm_name: str
    message: str
    user_name: str = "User"
    data_query: str = ""
    session_id: str = "default_session"
    conversation_mode: str = "open"
    referenced_message_id: Optional[str] = None
    context: List[dict] = []

def get_message_history(session_id: str):
    """
    Get or create a message history for the specified session.
    
    Args:
        session_id (str): Unique identifier for the chat session
        
    Returns:
        SQLChatMessageHistory: Message history for the session
    """
    return SQLChatMessageHistory(session_id=session_id, connection_string=DATABASE_URL)

def get_conversation_manager(session_id: str) -> ConversationManager:
    """
    Get or create a ConversationManager for the specified session.
    
    Args:
        session_id (str): Unique identifier for the conversation session
        
    Returns:
        ConversationManager: Manager for the session
    """
    if session_id not in conversation_managers:
        conversation_managers[session_id] = ConversationManager(session_id)
        logging.info(f"Created new ConversationManager for session {session_id}")
    return conversation_managers[session_id]

@app.post("/chat")
async def chat(chat_request: Request):
    """
    Process an incoming chat message using the ConversationManager.
    
    This endpoint handles:
    - Regular chat messages
    - Commands starting with /
    - Messages with @mentions
    - Document context integration
    
    Args:
        chat_request (Request): FastAPI request containing chat message data
        
    Returns:
        Union[Dict, List[Dict]]: Response(s) from LLM(s)
        
    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        # Parse and validate the request
        data = await chat_request.json()
        chat_request_data = ChatRequest(**data)

        # Extract request parameters
        llm_name = chat_request_data.llm_name.lower()
        message = chat_request_data.message
        user_name = chat_request_data.user_name
        data_query = chat_request_data.data_query
        session_id = chat_request_data.session_id
        
        logging.info(f"Received request: llm_name={llm_name}, message={message}, user_name={user_name}, session_id={session_id}")

    except ValidationError as e:
        logging.error(f"Validation Error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
    except Exception as e:
        logging.exception(f"Unexpected error in request parsing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Get the conversation manager for this session
    conversation_manager = get_conversation_manager(session_id)
    
    # Get message history for this session (for backward compatibility)
    history = get_message_history(session_id)
    history.add_user_message(message)
    
    try:
        # Check if this is a system command (starting with /)
        if message.startswith("/"):
            # Process through conversation manager's command handler
            responses = await conversation_manager.process_message(message, "user")
            
            # Record command responses in history for backward compatibility
            for response in responses:
                history.add_ai_message(f"System: {response['response']}")
                
            return responses
        
        # ----- Document Context Integration -----
        # Find relevant documents if there's a data query or message content
        metadata = data_access.get_all_documents()
        metadata_str = ""
        for item in metadata:
            metadata_str += str(item)
        
        # Use Gemini for document selection (we could refactor this to use the conversation manager later)
        gemini = Gemini()  # Temporary instance for document selection
        relevant_files = await select_relevant_documents(data_query if data_query else message, metadata_str, gemini)
        logging.info(f"Relevant files: {relevant_files}")

        # Load document content
        context_docs = ""
        for file_path in relevant_files:
            content = read_file_content(file_path)
            if content:
                context_docs += f"--- Begin {file_path} ---\n{content}\n--- End {file_path} ---\n"

        # Enhance the message with document context if available
        if context_docs:
            enhanced_message = f"Here is some context from relevant documents:\n{context_docs}\n\nWith this context in mind, please respond to: {message}"
        else:
            enhanced_message = message
        
        # Process the message through the conversation manager
        responses = await conversation_manager.process_message(enhanced_message, "user", llm_name if llm_name != "all" else None)
        
        # Record responses in history for backward compatibility
        for response in responses:
            history.add_ai_message(f"{response['llm'].capitalize()}: {response['response']}")
        
        return responses

    except Exception as e:
        logging.exception(f"Unexpected error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation_modes")
async def get_conversation_modes():
    """
    Get available conversation modes.
    
    Returns:
        Dict: Available conversation modes and descriptions
    """
    return {
        "modes": {
            "open": "Natural conversation with all LLMs",
            "debate": "Structured debate on a topic",
            "creative": "Creative collaboration for writing, music, etc.",
            "research": "Research and analysis mode for papers and documents"
        }
    }

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a conversation session.
    
    Args:
        session_id (str): ID of the session to clear
        
    Returns:
        Dict: Success message
    """
    if session_id in conversation_managers:
        del conversation_managers[session_id]
        logging.info(f"Cleared conversation manager for session {session_id}")
    
    # Also clear the message history
    history = get_message_history(session_id)
    # This is a hack - langchain doesn't provide a clear method
    # We'll use a direct database connection to clear the messages
    try:
        import sqlite3
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM message_store WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
        logging.info(f"Cleared message history for session {session_id}")
    except Exception as e:
        logging.error(f"Error clearing message history: {e}")
    
    return {"message": f"Session {session_id} cleared"}

@app.get("/")
async def read_root():
    """
    Root endpoint with information about the API.
    """
    return {
        "message": "Welcome to the LLMCreativeStudio API!",
        "version": "0.7.0",
        "features": [
            "Multi-LLM conversations with Claude, ChatGPT, and Gemini",
            "AutoGen-powered conversation management",
            "Multiple conversation modes (open, debate, creative, research)",
            "Document context integration",
            "Role-based conversational AI"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
