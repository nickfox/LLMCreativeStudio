# /Users/nickfox137/Documents/llm-creative-studio/python/tests/test_project_manager.py

import pytest
import sys
import os
import sqlite3
import json
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_manager import ProjectManager

# Define a test database path
TEST_DB_PATH = "test_projects.db"
TEST_PROJECTS_DIR = "test_projects"

@pytest.fixture
def project_manager():
    """Create a project manager for testing with a test database."""
    # Patch the database and directory paths
    with patch("project_manager.PROJECTS_DB", TEST_DB_PATH):
        with patch("project_manager.PROJECTS_DIR", TEST_PROJECTS_DIR):
            # Create the test directory
            os.makedirs(TEST_PROJECTS_DIR, exist_ok=True)
            
            # Create the project manager
            manager = ProjectManager()
            
            yield manager
            
            # Clean up after the test
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
            if os.path.exists(TEST_PROJECTS_DIR):
                shutil.rmtree(TEST_PROJECTS_DIR)

class TestProjectManager:
    
    def test_create_project(self, project_manager):
        """Test creating a project."""
        # Create a project
        project_id = project_manager.create_project(
            name="Test Project",
            project_type="research",
            description="A test project",
            metadata={"key": "value"}
        )
        
        # Check that the project was created in the database
        assert project_id is not None
        
        # Get the project and check its properties
        project = project_manager.get_project(project_id)
        assert project is not None
        assert project["name"] == "Test Project"
        assert project["type"] == "research"
        assert project["description"] == "A test project"
        assert project["metadata"].get("key") == "value"
        
        # Check that the project directory was created
        project_dir = os.path.join(TEST_PROJECTS_DIR, project_id)
        assert os.path.exists(project_dir)
        assert os.path.exists(os.path.join(project_dir, "references"))
        assert os.path.exists(os.path.join(project_dir, "outputs"))
    
    def test_list_projects(self, project_manager):
        """Test listing projects."""
        # Create some projects
        project_id1 = project_manager.create_project(
            name="Project 1",
            project_type="research",
            description="Project 1 description"
        )
        project_id2 = project_manager.create_project(
            name="Project 2",
            project_type="songwriting",
            description="Project 2 description"
        )
        
        # List the projects
        projects = project_manager.list_projects()
        
        # Check that both projects are in the list
        assert len(projects) == 2
        assert any(p["id"] == project_id1 for p in projects)
        assert any(p["id"] == project_id2 for p in projects)
        
        # Check that the project properties are correct
        project1 = next(p for p in projects if p["id"] == project_id1)
        assert project1["name"] == "Project 1"
        assert project1["type"] == "research"
        
        project2 = next(p for p in projects if p["id"] == project_id2)
        assert project2["name"] == "Project 2"
        assert project2["type"] == "songwriting"
    
    def test_update_project(self, project_manager):
        """Test updating a project."""
        # Create a project
        project_id = project_manager.create_project(
            name="Original Name",
            project_type="research",
            description="Original description",
            metadata={"key": "original"}
        )
        
        # Update the project
        success = project_manager.update_project(
            project_id=project_id,
            name="Updated Name",
            description="Updated description",
            metadata={"key": "updated"}
        )
        
        # Check that the update was successful
        assert success
        
        # Get the updated project
        project = project_manager.get_project(project_id)
        
        # Check that the properties were updated
        assert project["name"] == "Updated Name"
        assert project["description"] == "Updated description"
        assert project["metadata"].get("key") == "updated"
        
        # The type should not change as we didn't update it
        assert project["type"] == "research"
    
    def test_delete_project(self, project_manager):
        """Test deleting a project."""
        # Create a project
        project_id = project_manager.create_project(
            name="Project to Delete",
            project_type="research"
        )
        
        # Add a character to the project
        character_id = project_manager.add_character(
            project_id=project_id,
            character_name="Test Character",
            llm_name="claude"
        )
        
        # Delete the project
        success = project_manager.delete_project(project_id)
        
        # Check that the deletion was successful
        assert success
        
        # Check that the project is no longer in the database
        assert project_manager.get_project(project_id) is None
        
        # Check that the project directory was deleted
        project_dir = os.path.join(TEST_PROJECTS_DIR, project_id)
        assert not os.path.exists(project_dir)
    
    def test_add_character(self, project_manager):
        """Test adding a character to a project."""
        # Create a project
        project_id = project_manager.create_project(
            name="Character Test Project",
            project_type="creative"
        )
        
        # Add a character
        character_id = project_manager.add_character(
            project_id=project_id,
            character_name="John Lennon",
            llm_name="claude",
            background="Songwriter from Liverpool"
        )
        
        # Check that the character was added
        assert character_id is not None
        
        # Get the characters for the project
        characters = project_manager.get_project_characters(project_id)
        
        # Check that the character is in the list
        assert len(characters) == 1
        assert characters[0]["id"] == character_id
        assert characters[0]["character_name"] == "John Lennon"
        assert characters[0]["llm_name"] == "claude"
        assert characters[0]["background"] == "Songwriter from Liverpool"
    
    def test_delete_character(self, project_manager):
        """Test deleting a character from a project."""
        # Create a project
        project_id = project_manager.create_project(
            name="Character Delete Test",
            project_type="creative"
        )
        
        # Add a character
        character_id = project_manager.add_character(
            project_id=project_id,
            character_name="Paul McCartney",
            llm_name="chatgpt"
        )
        
        # Delete the character
        success = project_manager.delete_character(character_id)
        
        # Check that the deletion was successful
        assert success
        
        # Check that the character is no longer in the database
        characters = project_manager.get_project_characters(project_id)
        assert len(characters) == 0
    
    def test_add_project_file(self, project_manager):
        """Test adding a file to a project."""
        # Create a project
        project_id = project_manager.create_project(
            name="File Test Project",
            project_type="research"
        )
        
        # Add a file
        file_id = project_manager.add_project_file(
            project_id=project_id,
            file_path="test.pdf",
            file_type="pdf",
            description="Test file",
            is_reference=True,
            is_output=False
        )
        
        # Check that the file was added
        assert file_id is not None
        
        # Get the files for the project
        files = project_manager.get_project_files(project_id)
        
        # Check that the file is in the list
        assert len(files) == 1
        assert files[0]["id"] == file_id
        assert files[0]["file_path"] == "test.pdf"
        assert files[0]["file_type"] == "pdf"
        assert files[0]["description"] == "Test file"
        assert files[0]["is_reference"] is True
        assert files[0]["is_output"] is False
    
    def test_delete_project_file(self, project_manager):
        """Test deleting a file from a project."""
        # Create a project
        project_id = project_manager.create_project(
            name="File Delete Test",
            project_type="research"
        )
        
        # Add a file
        file_id = project_manager.add_project_file(
            project_id=project_id,
            file_path="delete_me.pdf",
            file_type="pdf"
        )
        
        # Delete the file
        success = project_manager.delete_project_file(file_id, delete_physical_file=False)
        
        # Check that the deletion was successful
        assert success
        
        # Check that the file is no longer in the database
        files = project_manager.get_project_files(project_id)
        assert len(files) == 0
    
    def test_save_and_load_session(self, project_manager):
        """Test saving and loading a session."""
        # Create a project
        project_id = project_manager.create_project(
            name="Session Test",
            project_type="creative"
        )
        
        # Create a session ID
        session_id = "test_session_id"
        
        # Sample conversation state
        conversation_state = {
            "conversation_history": [
                {"sender": "user", "content": "Hello", "timestamp": 1234567890}
            ],
            "conversation_mode": "creative",
            "current_task": "Writing a song",
            "characters": {
                "character_map": {"John Lennon": "claude"},
                "llm_to_character": {"claude": "John Lennon"}
            }
        }
        
        # Sample active roles
        active_roles = {
            "claude": "creative",
            "chatgpt": "assistant"
        }
        
        # Save the session
        success = project_manager.save_session(
            project_id=project_id,
            session_id=session_id,
            conversation_state=conversation_state,
            active_roles=active_roles
        )
        
        # Check that the save was successful
        assert success
        
        # Load the session
        loaded_session = project_manager.load_session(session_id)
        
        # Check that the loaded session matches what we saved
        assert loaded_session is not None
        assert loaded_session["project_id"] == project_id
        assert loaded_session["conversation_state"] == conversation_state
        assert loaded_session["active_roles"] == active_roles
    
    def test_delete_session(self, project_manager):
        """Test deleting a session."""
        # Create a project
        project_id = project_manager.create_project(
            name="Session Delete Test",
            project_type="research"
        )
        
        # Create a session ID
        session_id = "delete_session_id"
        
        # Save a session
        project_manager.save_session(
            project_id=project_id,
            session_id=session_id,
            conversation_state={},
            active_roles={}
        )
        
        # Delete the session
        success = project_manager.delete_session(session_id)
        
        # Check that the deletion was successful
        assert success
        
        # Check that the session is no longer in the database
        loaded_session = project_manager.load_session(session_id)
        assert loaded_session is None
