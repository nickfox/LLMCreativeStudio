# /Users/nickfox137/Documents/llm-creative-studio/python/main.py
"""
LLMCreativeStudio API

This module provides the FastAPI backend for the LLMCreativeStudio application.
It handles conversation management, project management, and LLM interactions.
"""

import asyncio
import logging
import os
import json
from typing import List, Dict, Optional, Union, Any
from fastapi import FastAPI, HTTPException, Request, Depends, status, File, UploadFile, Form, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError, Field
from datetime import datetime
import uuid

# Import Ollama service
from ollama_service import OllamaService

from config import DATA_DIR
from llms import Gemini, ChatGPT, Claude
from data import select_relevant_documents, read_file_content
from utils import setup_logging
from data_access import DataAccess
from conversation_manager import ConversationManager
from project_manager import ProjectManager, PROJECTS_DIR
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.chat_message_histories import SQLChatMessageHistory

# --- Setup Logging ---
setup_logging()

# --- FastAPI App ---
app = FastAPI(
    title="LLMCreativeStudio API",
    description="API for LLMCreativeStudio, a multi-LLM conversation platform with enhanced debate capabilities",
    version="0.9.0"
)

# --- Database Setup ---
DATABASE_URL = "sqlite:///./chat_history.db"
db = SQLDatabase.from_uri(DATABASE_URL, sample_rows_in_table_info=0)
data_access = DataAccess()

# --- Managers ---
# Conversation managers dictionary - Tracks active conversation managers by session_id
conversation_managers = {}
# Project manager - Handles project operations
project_manager = ProjectManager()

# --- Initialize Ollama Service ---
ollama_service = OllamaService()
try:
    # Create an event loop and check availability
    loop = asyncio.new_event_loop()
    ollama_available = loop.run_until_complete(ollama_service.check_availability())
    if ollama_available:
        logging.info("Ollama service initialized successfully with phi4 and nomic-embed-text models")
    else:
        logging.warning("Ollama service initialized but models not available. RAG functionality will be limited.")
except Exception as e:
    logging.error(f"Failed to initialize Ollama service: {e}")
    ollama_service = None

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    """
    Pydantic model for chat requests with enhanced fields for conversation management.
    """
    llm_name: str
    message: str
    user_name: str = "User"
    data_query: str = ""
    session_id: str = "default_session"
    project_id: Optional[str] = None
    conversation_mode: str = "open"
    referenced_message_id: Optional[str] = None
    context: List[dict] = []

class RAGQueryRequest(BaseModel):
    """
    Pydantic model for RAG queries.
    """
    query: str
    project_id: str
    use_thinking: bool = False

class ProjectCreate(BaseModel):
    """
    Model for creating a new project.
    """
    name: str
    type: str = Field(..., description="Type of project: 'research', 'songwriting', or 'book'")
    description: str = ""
    metadata: Dict[str, Any] = {}

class ProjectUpdate(BaseModel):
    """
    Model for updating an existing project.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CharacterCreate(BaseModel):
    """
    Model for creating a character for roleplay.
    """
    character_name: str
    llm_name: str = Field(..., description="LLM to assign this character to: 'claude', 'chatgpt', or 'gemini'")
    background: str = ""

class SessionSave(BaseModel):
    """
    Model for saving a session state.
    """
    conversation_state: Dict[str, Any]
    active_roles: Dict[str, str]

def get_message_history(session_id: str):
    """
    Get or create a message history for the specified session.
    
    Args:
        session_id (str): Unique identifier for the chat session
        
    Returns:
        SQLChatMessageHistory: Message history for the session
    """
    return SQLChatMessageHistory(session_id=session_id, connection=DATABASE_URL)

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

# --- Chat Endpoints ---

@app.post("/chat")
async def chat(chat_request: Request):
    """
    Process an incoming chat message using the ConversationManager.
    
    This endpoint handles:
    - Regular chat messages
    - Commands starting with /
    - Messages with @mentions
    - Character-based addressing
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
        project_id = chat_request_data.project_id
        
        logging.info(f"Received request: llm_name={llm_name}, message={message}, user_name={user_name}, session_id={session_id}, project_id={project_id}")

    except ValidationError as e:
        logging.error(f"Validation Error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
    except Exception as e:
        logging.exception(f"Unexpected error in request parsing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Get the conversation manager for this session
    conversation_manager = get_conversation_manager(session_id)
    
    # If project ID is provided, load project-specific characters
    if project_id:
        await load_project_characters(project_id, conversation_manager)
    
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
                # Check the format of the response to handle both types
                if "content" in response:
                    # New format from debate manager
                    history.add_ai_message(f"{response.get('sender', 'System')}: {response['content']}")
                elif "response" in response:
                    # Old format
                    history.add_ai_message(f"System: {response['response']}")                
            
            # If project ID is provided, save the conversation state
            if project_id:
                save_project_session(project_id, session_id, conversation_manager)
                
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
        
        # Check for RAG query (message starts with ?)
        if message.startswith("?") and ollama_service and project_id:
            query = message[1:].strip()
            if not query:
                raise HTTPException(status_code=400, detail="RAG query cannot be empty")
            
            # Add user message to history
            user_msg = {
                "sender": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
            conversation_manager.conversation_history.append(user_msg)
            
            # Process the query with Ollama
            result = await ollama_service.answer_with_rag(
                project_id=project_id,
                query=query
            )
            
            # Create response
            response = {
                "sender": "research_assistant",
                "content": result["answer"],
                "timestamp": datetime.now().isoformat(),
                "sources": result["sources"] if "sources" in result else [],
                "metadata": result["metadata"] if "metadata" in result else {}
            }
            
            # Add to conversation history
            conversation_manager.conversation_history.append(response)
            
            # If project ID is provided, save the conversation state
            if project_id:
                save_project_session(project_id, session_id, conversation_manager)
            
            return [response]
            
        # Process the message through the conversation manager
        responses = await conversation_manager.process_message(enhanced_message, "user", llm_name if llm_name != "all" else None)
        
        # Add debate pause information to responses if applicable
        if hasattr(conversation_manager, 'debate_manager') and conversation_manager.debate_manager.is_waiting_for_user():
            # Find the latest response with waiting_for_user=True and add UI indicator
            for response in responses:
                if response.get("waiting_for_user", False):
                    response["waiting_for_user"] = True
                    response["action_required"] = "debate_input"
                    logging.info("Debate is waiting for user input")
        
        # Record responses in history for backward compatibility
        for response in responses:
            # Handle both response formats
            if "content" in response:
                # New format from debate manager
                sender = response.get("sender", response.get("llm", "System"))
                history.add_ai_message(f"{sender.capitalize()}: {response['content']}")
            elif "response" in response:
                # Old format
                llm = response.get("llm", "System")
                history.add_ai_message(f"{llm.capitalize()}: {response['response']}")
        
        # Add debug information if requested in debug mode
        if conversation_manager.debug and hasattr(conversation_manager, 'debate_manager'):
            logging.info(f"Current debate state: {conversation_manager.debate_manager.state if hasattr(conversation_manager, 'debate_manager') else 'No debate'}")
            logging.info(f"Waiting for user: {conversation_manager.debate_manager.is_waiting_for_user() if hasattr(conversation_manager, 'debate_manager') else False}")
        
        # If project ID is provided, save the conversation state
        if project_id:
            save_project_session(project_id, session_id, conversation_manager)
        
        return responses

    except Exception as e:
        logging.exception(f"Unexpected error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Helper functions ---

async def load_project_characters(project_id: str, conversation_manager: ConversationManager):
    """
    Load characters from a project into the conversation manager.
    
    Args:
        project_id (str): Project ID to load characters from
        conversation_manager (ConversationManager): Conversation manager to apply characters to
    """
    try:
        project = project_manager.get_project(project_id)
        if not project:
            logging.warning(f"Project {project_id} not found when loading characters")
            return
            
        # Clear existing characters
        conversation_manager.characters = {}
        conversation_manager.llm_to_character = {}
        
        # Add project characters
        if "characters" in project and project["characters"]:
            for character in project["characters"]:
                conversation_manager.characters[character["character_name"]] = character["llm_name"]
                conversation_manager.llm_to_character[character["llm_name"]] = character["character_name"]
                
            logging.info(f"Loaded {len(project['characters'])} characters for project {project_id}")
    except Exception as e:
        logging.error(f"Error loading project characters: {e}")

def save_project_session(project_id: str, session_id: str, conversation_manager: ConversationManager):
    """
    Save the current conversation state to the project.
    
    Args:
        project_id (str): Project ID
        session_id (str): Session ID
        conversation_manager (ConversationManager): Conversation manager to save state from
    """
    try:
        # Prepare the conversation state to save
        conversation_state = {
            "conversation_history": conversation_manager.conversation_history,
            "conversation_mode": conversation_manager.conversation_mode,
            "current_task": conversation_manager.current_task,
            "characters": {
                "character_map": conversation_manager.characters,
                "llm_to_character": conversation_manager.llm_to_character
            }
        }
        
        # Save to database
        project_manager.save_session(project_id, session_id, conversation_state, conversation_manager.active_roles)
        logging.info(f"Saved conversation state for project {project_id}, session {session_id}")
    except Exception as e:
        logging.error(f"Error saving project session: {e}")

# --- Session Management Endpoints ---

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
async def clear_session(session_id: str, project_id: Optional[str] = None):
    """
    Clear a conversation session.
    
    Args:
        session_id (str): ID of the session to clear
        project_id (Optional[str]): If provided, also remove from project sessions
        
    Returns:
        Dict: Success message
    """
    if session_id in conversation_managers:
        del conversation_managers[session_id]
        logging.info(f"Cleared conversation manager for session {session_id}")
    
    # Clear from project if provided
    if project_id:
        project_manager.delete_session(session_id)
    
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

@app.post("/sessions/{project_id}/restore/{session_id}")
async def restore_session(project_id: str, session_id: str):
    """
    Restore a previous conversation session for a project.
    
    Args:
        project_id (str): Project ID
        session_id (str): Session ID to restore
        
    Returns:
        Dict: Session information and status
    """
    try:
        # Load the session from the database
        session_data = project_manager.load_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Create a new conversation manager with this session's data
        conversation_manager = ConversationManager(session_id)
        
        # Restore the conversation state
        conversation_state = session_data["conversation_state"]
        conversation_manager.conversation_history = conversation_state.get("conversation_history", [])
        conversation_manager.conversation_mode = conversation_state.get("conversation_mode", "open")
        conversation_manager.current_task = conversation_state.get("current_task", "")
        
        # Restore characters if present
        if "characters" in conversation_state:
            character_data = conversation_state["characters"]
            conversation_manager.characters = character_data.get("character_map", {})
            conversation_manager.llm_to_character = character_data.get("llm_to_character", {})
        
        # Restore active roles
        conversation_manager.active_roles = session_data["active_roles"]
        
        # Store the restored conversation manager
        conversation_managers[session_id] = conversation_manager
        
        return {
            "message": f"Session {session_id} restored for project {project_id}",
            "session_id": session_id,
            "conversation_mode": conversation_manager.conversation_mode,
            "current_task": conversation_manager.current_task,
            "message_count": len(conversation_manager.conversation_history),
            "characters": list(conversation_manager.characters.items()),
            "active_roles": conversation_manager.active_roles
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error restoring session: {e}")
        raise HTTPException(status_code=500, detail=f"Error restoring session: {str(e)}")

# --- Project Management Endpoints ---

@app.get("/projects")
async def list_projects():
    """
    List all available projects.
    
    Returns:
        List[Dict]: List of project summaries
    """
    try:
        projects = project_manager.list_projects()
        return {"projects": projects}
    except Exception as e:
        logging.exception(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects", status_code=201)
async def create_project(project: ProjectCreate):
    """
    Create a new project.
    
    Args:
        project (ProjectCreate): Project creation data
        
    Returns:
        Dict: Created project ID and name
    """
    try:
        project_id = project_manager.create_project(
            name=project.name,
            project_type=project.type,
            description=project.description,
            metadata=project.metadata
        )
        
        return {
            "message": "Project created successfully",
            "project_id": project_id,
            "name": project.name
        }
    except Exception as e:
        logging.exception(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """
    Get project details by ID.
    
    Args:
        project_id (str): Project ID
        
    Returns:
        Dict: Project details
    """
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
            
        return {"project": project}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error retrieving project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/projects/{project_id}")
async def update_project(project_id: str, project_update: ProjectUpdate):
    """
    Update an existing project.
    
    Args:
        project_id (str): Project ID to update
        project_update (ProjectUpdate): Fields to update
        
    Returns:
        Dict: Success message
    """
    try:
        success = project_manager.update_project(
            project_id=project_id,
            name=project_update.name,
            description=project_update.description,
            metadata=project_update.metadata
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
            
        return {"message": f"Project {project_id} updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """
    Delete a project and all associated data.
    
    Args:
        project_id (str): Project ID to delete
        
    Returns:
        Dict: Success message
    """
    try:
        success = project_manager.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
            
        return {"message": f"Project {project_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Character Management Endpoints ---

@app.post("/projects/{project_id}/characters", status_code=201)
async def add_character(project_id: str, character: CharacterCreate):
    """
    Add a character to a project for roleplay.
    
    Args:
        project_id (str): Project ID
        character (CharacterCreate): Character details
        
    Returns:
        Dict: Created character ID and success message
    """
    try:
        # Validate that the LLM name is valid
        valid_llms = ["claude", "chatgpt", "gemini"]
        if character.llm_name.lower() not in valid_llms:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid LLM name: {character.llm_name}. Valid options: {', '.join(valid_llms)}"
            )
        
        character_id = project_manager.add_character(
            project_id=project_id,
            character_name=character.character_name,
            llm_name=character.llm_name.lower(),
            background=character.background
        )
        
        if not character_id:
            raise HTTPException(status_code=500, detail="Failed to create character")
            
        return {
            "message": f"Character {character.character_name} added to project {project_id}",
            "character_id": character_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error adding character: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/characters")
async def get_project_characters(project_id: str):
    """
    Get all characters for a project.
    
    Args:
        project_id (str): Project ID
        
    Returns:
        Dict: List of characters
    """
    try:
        characters = project_manager.get_project_characters(project_id)
        return {"characters": characters}
    except Exception as e:
        logging.exception(f"Error getting project characters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}/characters/{character_id}")
async def delete_character(project_id: str, character_id: str):
    """
    Delete a character from a project.
    
    Args:
        project_id (str): Project ID
        character_id (str): Character ID to delete
        
    Returns:
        Dict: Success message
    """
    try:
        success = project_manager.delete_character(character_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Character {character_id} not found")
            
        return {"message": f"Character {character_id} deleted from project {project_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error deleting character: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- File Management Endpoints ---

@app.post("/projects/{project_id}/files", status_code=201)
async def upload_file(project_id: str, file: UploadFile = File(...), 
                      description: str = Form(""), is_reference: bool = Form(False),
                      is_output: bool = Form(False)):
    """
    Upload a file to a project.
    
    Args:
        project_id (str): Project ID
        file (UploadFile): File to upload
        description (str): File description
        is_reference (bool): Whether this is a reference file
        is_output (bool): Whether this is an output file
        
    Returns:
        Dict: File ID and success message
    """
    try:
        # Check that project exists
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Determine subdirectory based on file type
        subdir = "references" if is_reference else "outputs" if is_output else ""
        
        # Create file path within project directory
        filename = file.filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{safe_filename}"
        
        relative_path = os.path.join(subdir, unique_filename) if subdir else unique_filename
        full_path = os.path.join(PROJECTS_DIR, project_id, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Save the file
        with open(full_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Determine file type
        file_ext = os.path.splitext(filename)[1].lower()
        file_type_map = {
            ".pdf": "pdf",
            ".txt": "text",
            ".md": "markdown",
            ".docx": "word",
            ".xlsx": "excel",
            ".csv": "csv",
            ".mid": "midi",
            ".midi": "midi",
            ".mp3": "audio",
            ".wav": "audio",
            ".musicxml": "musicxml",
            ".mxl": "musicxml",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image"
        }
        file_type = file_type_map.get(file_ext, "unknown")
        
        # Add to database
        file_id = project_manager.add_project_file(
            project_id=project_id,
            file_path=relative_path,
            file_type=file_type,
            description=description,
            is_reference=is_reference,
            is_output=is_output
        )
        
        if not file_id:
            raise HTTPException(status_code=500, detail="Failed to register file in database")
        
        return {
            "message": f"File {filename} uploaded to project {project_id}",
            "file_id": file_id,
            "file_path": relative_path,
            "file_type": file_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/files")
async def list_project_files(project_id: str, reference_only: bool = False, output_only: bool = False):
    """
    List all files in a project.
    
    Args:
        project_id (str): Project ID
        reference_only (bool): If True, only return reference files
        output_only (bool): If True, only return output files
        
    Returns:
        Dict: List of files
    """
    try:
        # Get files from database
        all_files = project_manager.get_project_files(project_id)
        
        # Filter if requested
        if reference_only:
            files = [f for f in all_files if f["is_reference"]]
        elif output_only:
            files = [f for f in all_files if f["is_output"]]
        else:
            files = all_files
            
        return {"files": files}
    except Exception as e:
        logging.exception(f"Error listing project files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/files/{file_id}/download")
async def download_file(project_id: str, file_id: str):
    """
    Download a file from a project.
    
    Args:
        project_id (str): Project ID
        file_id (str): File ID to download
        
    Returns:
        FileResponse: The requested file
    """
    try:
        # Get file details from database
        project_files = project_manager.get_project_files(project_id)
        file_info = next((f for f in project_files if f["id"] == file_id), None)
        
        if not file_info:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        # Create full path
        file_path = file_info["file_path"]
        full_path = os.path.join(PROJECTS_DIR, project_id, file_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"File {file_path} not found on disk")
        
        # Get original filename from path
        original_filename = os.path.basename(file_path).split("_", 1)[1] if "_" in os.path.basename(file_path) else os.path.basename(file_path)
        
        return FileResponse(
            path=full_path,
            filename=original_filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}/files/{file_id}")
async def delete_file(project_id: str, file_id: str, delete_physical: bool = True):
    """
    Delete a file from a project.
    
    Args:
        project_id (str): Project ID
        file_id (str): File ID to delete
        delete_physical (bool): Whether to delete the actual file from disk
        
    Returns:
        Dict: Success message
    """
    try:
        success = project_manager.delete_project_file(file_id, delete_physical)
        if not success:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
            
        return {"message": f"File {file_id} deleted from project {project_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- RAG Endpoints ---

@app.post("/rag/query")
async def rag_query(request: RAGQueryRequest):
    """
    Process a RAG query using Ollama to search project documents.
    
    Args:
        request (RAGQueryRequest): RAG query request
        
    Returns:
        Dict: RAG query results
    """
    try:
        if not ollama_service:
            raise HTTPException(status_code=503, detail="Ollama service is not available")
        
        # Process the query with Ollama
        result = await ollama_service.answer_with_rag(
            project_id=request.project_id,
            query=request.query,
            use_thinking=request.use_thinking
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error processing RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_id}/documents/{document_id}/process")
async def process_document_for_rag(project_id: str, document_id: str):
    """
    Process a document for RAG using Ollama.
    
    Args:
        project_id (str): Project ID
        document_id (str): Document ID to process
        
    Returns:
        Dict: Success message
    """
    try:
        if not ollama_service:
            raise HTTPException(status_code=503, detail="Ollama service is not available")
        
        # Get the document content
        content = await data_access.get_document_content(document_id)
        if not content:
            raise HTTPException(status_code=404, detail=f"Document {document_id} content not found")
        
        # Process the document
        success = await ollama_service.process_document(
            project_id=project_id,
            document_id=document_id,
            document_text=content
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to process document")
        
        return {"message": f"Document {document_id} processed successfully for RAG"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error processing document for RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_id}/process_all_documents")
async def process_all_project_documents_for_rag(project_id: str):
    """
    Process all documents in a project for RAG using Ollama.
    
    Args:
        project_id (str): Project ID
        
    Returns:
        Dict: Results of processing all documents
    """
    try:
        if not ollama_service:
            raise HTTPException(status_code=503, detail="Ollama service is not available")
        
        # Check that project exists
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Process all documents
        results = await ollama_service.process_all_project_documents(project_id)
        
        if not results.get("success", False):
            logging.warning(f"Some documents failed processing: {results['message']}")
        
        return {
            "message": results.get("message", "Documents processed with mixed results"),
            "total_documents": results.get("total", 0),
            "processed": results.get("processed", 0),
            "failed": results.get("failed", 0),
            "details": results.get("file_results", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error processing all project documents for RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    """
    Root endpoint with information about the API.
    """
    # Check if Ollama is available
    ollama_status = "Available" if ollama_service else "Not available"
    
    return {
        "message": "Welcome to the LLMCreativeStudio API!",
        "version": "0.10.0",
        "features": [
            "Multi-LLM conversations with Claude, ChatGPT, and Gemini",
            "AutoGen-powered conversation management",
            "Enhanced debate system with active user participation",
            "Multiple conversation modes (open, debate, creative, research)",
            "Project management for persistent work",
            "Character-based roleplay for creative tasks",
            "Document context integration",
            "Role-based conversational AI",
            "Advanced Local RAG with Ollama (phi4:14b-q4_K_M and nomic-embed-text)"
        ],
        "ollama_status": ollama_status,
        "rag_capabilities": {
            "status": ollama_status,
            "models": {
                "retrieval": "phi4:14b-q4_K_M",
                "embedding": "nomic-embed-text"
            },
            "endpoints": [
                "/rag/query",
                "/projects/{project_id}/documents/{document_id}/process",
                "/projects/{project_id}/process_all_documents"
            ]
        }
    }

# --- Ensure required directories exist ---

os.makedirs(os.path.join(DATA_DIR, "projects"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "uploads"), exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
