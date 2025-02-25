# /Users/nickfox137/Documents/llm-creative-studio/python/tests/test_api_endpoints.py

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, conversation_managers, project_manager

client = TestClient(app)

@pytest.fixture
def reset_state():
    """Reset the global state between tests."""
    conversation_managers.clear()
    
    # Mock project_manager methods
    project_manager.list_projects = MagicMock(return_value=[
        {
            "id": "test-project-id",
            "name": "Test Project",
            "type": "research",
            "description": "A test project",
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T00:00:00.000Z"
        }
    ])
    
    project_manager.get_project = MagicMock(return_value={
        "id": "test-project-id",
        "name": "Test Project",
        "type": "research",
        "description": "A test project",
        "created_at": "2023-01-01T00:00:00.000Z",
        "updated_at": "2023-01-01T00:00:00.000Z",
        "metadata": {},
        "characters": [
            {
                "id": "test-character-id",
                "character_name": "John Lennon",
                "llm_name": "claude",
                "background": "Songwriter from Liverpool",
                "created_at": "2023-01-01T00:00:00.000Z"
            }
        ],
        "files": []
    })
    
    project_manager.create_project = MagicMock(return_value="new-project-id")
    project_manager.update_project = MagicMock(return_value=True)
    project_manager.delete_project = MagicMock(return_value=True)
    project_manager.add_character = MagicMock(return_value="new-character-id")
    project_manager.get_project_characters = MagicMock(return_value=[
        {
            "id": "test-character-id",
            "character_name": "John Lennon",
            "llm_name": "claude",
            "background": "Songwriter from Liverpool",
            "created_at": "2023-01-01T00:00:00.000Z"
        }
    ])
    project_manager.delete_character = MagicMock(return_value=True)
    project_manager.save_session = MagicMock(return_value=True)
    project_manager.load_session = MagicMock(return_value={
        "project_id": "test-project-id",
        "conversation_state": {
            "conversation_history": [],
            "conversation_mode": "creative",
            "current_task": "",
            "characters": {
                "character_map": {"John Lennon": "claude"},
                "llm_to_character": {"claude": "John Lennon"}
            }
        },
        "active_roles": {"claude": "creative"},
        "last_accessed": "2023-01-01T00:00:00.000Z"
    })
    
    yield

class TestChatEndpoints:
    
    @patch("main.select_relevant_documents")
    @patch("llms.Claude.autogen_response")
    def test_chat_endpoint(self, mock_autogen_response, mock_select_docs, reset_state):
        """Test the /chat endpoint."""
        # Mock the LLM response
        mock_autogen_response.return_value = "Test response from Claude"
        
        # Mock document selection
        mock_select_docs.return_value = []
        
        # Send a chat request
        response = client.post(
            "/chat",
            json={
                "llm_name": "claude",
                "message": "Hello, Claude!",
                "user_name": "Test User",
                "session_id": "test-session"
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["llm"] == "claude"
        assert data[0]["response"] == "Test response from Claude"
    
    @patch("main.select_relevant_documents")
    @patch("llms.Claude.autogen_response")
    def test_chat_with_project(self, mock_autogen_response, mock_select_docs, reset_state):
        """Test the /chat endpoint with a project ID."""
        # Mock the LLM response
        mock_autogen_response.return_value = "Test response from Claude"
        
        # Mock document selection
        mock_select_docs.return_value = []
        
        # Send a chat request
        response = client.post(
            "/chat",
            json={
                "llm_name": "claude",
                "message": "Hello, Claude!",
                "user_name": "Test User",
                "session_id": "test-session",
                "project_id": "test-project-id"
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["llm"] == "claude"
        assert data[0]["response"] == "Test response from Claude"
        
        # Check that the session was saved
        project_manager.save_session.assert_called_once()
    
    @patch("main.select_relevant_documents")
    def test_chat_command(self, mock_select_docs, reset_state):
        """Test the /chat endpoint with a command."""
        # Mock document selection
        mock_select_docs.return_value = []
        
        # Send a chat request with a command
        response = client.post(
            "/chat",
            json={
                "llm_name": "system",
                "message": "/help",
                "user_name": "Test User",
                "session_id": "test-session"
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["llm"] == "system"
        assert "Commands" in data[0]["response"]
    
    def test_conversation_modes_endpoint(self, reset_state):
        """Test the /conversation_modes endpoint."""
        response = client.get("/conversation_modes")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "modes" in data
        assert len(data["modes"]) == 4
        assert "open" in data["modes"]
        assert "debate" in data["modes"]
        assert "creative" in data["modes"]
        assert "research" in data["modes"]
    
    def test_clear_session_endpoint(self, reset_state):
        """Test the /sessions/{session_id} endpoint."""
        # Create a conversation manager for the session
        from conversation_manager import ConversationManager
        conversation_managers["test-session"] = ConversationManager("test-session")
        
        # Send a delete request
        response = client.delete("/sessions/test-session")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session test-session cleared"
        
        # Check that the conversation manager was removed
        assert "test-session" not in conversation_managers
    
    def test_restore_session_endpoint(self, reset_state):
        """Test the /sessions/{project_id}/restore/{session_id} endpoint."""
        # Send a post request
        response = client.post("/sessions/test-project-id/restore/test-session")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session test-session restored for project test-project-id"
        assert data["session_id"] == "test-session"
        assert data["conversation_mode"] == "creative"
        
        # Check that a conversation manager was created
        assert "test-session" in conversation_managers
        assert conversation_managers["test-session"].conversation_mode == "creative"
        assert "claude" in conversation_managers["test-session"].active_roles
        assert conversation_managers["test-session"].active_roles["claude"] == "creative"

class TestProjectEndpoints:
    
    def test_list_projects_endpoint(self, reset_state):
        """Test the /projects endpoint."""
        response = client.get("/projects")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "projects" in data
        assert len(data["projects"]) == 1
        assert data["projects"][0]["id"] == "test-project-id"
        assert data["projects"][0]["name"] == "Test Project"
    
    def test_create_project_endpoint(self, reset_state):
        """Test the /projects endpoint for creating a project."""
        response = client.post(
            "/projects",
            json={
                "name": "New Project",
                "type": "songwriting",
                "description": "A new project"
            }
        )
        
        # Check the response
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Project created successfully"
        assert data["project_id"] == "new-project-id"
        assert data["name"] == "New Project"
        
        # Check that the create_project method was called
        project_manager.create_project.assert_called_once_with(
            name="New Project",
            project_type="songwriting",
            description="A new project",
            metadata={}
        )
    
    def test_get_project_endpoint(self, reset_state):
        """Test the /projects/{project_id} endpoint."""
        response = client.get("/projects/test-project-id")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "project" in data
        assert data["project"]["id"] == "test-project-id"
        assert data["project"]["name"] == "Test Project"
        assert len(data["project"]["characters"]) == 1
        assert data["project"]["characters"][0]["character_name"] == "John Lennon"
    
    def test_update_project_endpoint(self, reset_state):
        """Test the /projects/{project_id} endpoint for updating a project."""
        response = client.put(
            "/projects/test-project-id",
            json={
                "name": "Updated Project",
                "description": "An updated project"
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Project test-project-id updated successfully"
        
        # Check that the update_project method was called
        project_manager.update_project.assert_called_once_with(
            project_id="test-project-id",
            name="Updated Project",
            description="An updated project",
            metadata=None
        )
    
    def test_delete_project_endpoint(self, reset_state):
        """Test the /projects/{project_id} endpoint for deleting a project."""
        response = client.delete("/projects/test-project-id")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Project test-project-id deleted successfully"
        
        # Check that the delete_project method was called
        project_manager.delete_project.assert_called_once_with("test-project-id")

class TestCharacterEndpoints:
    
    def test_add_character_endpoint(self, reset_state):
        """Test the /projects/{project_id}/characters endpoint."""
        response = client.post(
            "/projects/test-project-id/characters",
            json={
                "character_name": "Paul McCartney",
                "llm_name": "chatgpt",
                "background": "Bassist from Liverpool"
            }
        )
        
        # Check the response
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Character Paul McCartney added to project test-project-id"
        assert data["character_id"] == "new-character-id"
        
        # Check that the add_character method was called
        project_manager.add_character.assert_called_once_with(
            project_id="test-project-id",
            character_name="Paul McCartney",
            llm_name="chatgpt",
            background="Bassist from Liverpool"
        )
    
    def test_get_project_characters_endpoint(self, reset_state):
        """Test the /projects/{project_id}/characters endpoint."""
        response = client.get("/projects/test-project-id/characters")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "characters" in data
        assert len(data["characters"]) == 1
        assert data["characters"][0]["character_name"] == "John Lennon"
        assert data["characters"][0]["llm_name"] == "claude"
    
    def test_delete_character_endpoint(self, reset_state):
        """Test the /projects/{project_id}/characters/{character_id} endpoint."""
        response = client.delete("/projects/test-project-id/characters/test-character-id")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Character test-character-id deleted from project test-project-id"
        
        # Check that the delete_character method was called
        project_manager.delete_character.assert_called_once_with("test-character-id")
