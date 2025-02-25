# /Users/nickfox137/Documents/llm-creative-studio/python/project_manager.py
"""
Project Manager Module

This module manages the creation, loading, and saving of projects in LLMCreativeStudio.
It provides a database abstraction for project persistence and file management utilities.
"""

import os
import logging
import json
import sqlite3
import shutil
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
import uuid
from config import DATA_DIR

# Configure path for project storage
PROJECTS_DIR = os.path.join(DATA_DIR, "projects")
PROJECTS_DB = os.path.join(DATA_DIR, "projects.db")

# Ensure directories exist
os.makedirs(PROJECTS_DIR, exist_ok=True)

class ProjectManager:
    """
    Manages the creation, retrieval, updating, and deletion of projects.
    
    This class handles all project-related operations including database interactions,
    file management, and session state persistence.
    
    Attributes:
        conn (sqlite3.Connection): Database connection
    """
    
    def __init__(self):
        """Initialize the ProjectManager and ensure the database exists."""
        self.conn = sqlite3.connect(PROJECTS_DB)
        self.cursor = self.conn.cursor()
        self._create_tables_if_not_exist()
        logging.info("ProjectManager initialized")
    
    def _create_tables_if_not_exist(self):
        """Create the database tables if they don't already exist."""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_sessions (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            conversation_state TEXT,
            active_roles TEXT,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_files (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            description TEXT,
            is_reference BOOLEAN DEFAULT 0,
            is_output BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_characters (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            character_name TEXT NOT NULL,
            llm_name TEXT NOT NULL,
            background TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        ''')
        
        self.conn.commit()
        logging.info("Database tables created or verified")
    
    def create_project(self, name: str, project_type: str, description: str = "", 
                      metadata: Dict[str, Any] = None) -> str:
        """
        Create a new project.
        
        Args:
            name (str): Project name
            project_type (str): Type of project (research, songwriting, book)
            description (str, optional): Project description
            metadata (Dict[str, Any], optional): Additional project metadata
            
        Returns:
            str: The ID of the created project
        """
        project_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})
        
        try:
            # Insert project into database
            self.cursor.execute(
                "INSERT INTO projects (id, name, type, description, metadata) VALUES (?, ?, ?, ?, ?)",
                (project_id, name, project_type, description, metadata_json)
            )
            
            # Create project directory
            project_dir = os.path.join(PROJECTS_DIR, project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            # Create subdirectories for reference and output files
            os.makedirs(os.path.join(project_dir, "references"), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "outputs"), exist_ok=True)
            
            self.conn.commit()
            logging.info(f"Created project: {name} (ID: {project_id})")
            
            return project_id
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error creating project: {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project details by ID.
        
        Args:
            project_id (str): The ID of the project to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Project details or None if not found
        """
        try:
            self.cursor.execute(
                "SELECT id, name, type, description, created_at, updated_at, metadata FROM projects WHERE id = ?",
                (project_id,)
            )
            
            result = self.cursor.fetchone()
            if not result:
                return None
                
            project_data = {
                "id": result[0],
                "name": result[1],
                "type": result[2],
                "description": result[3],
                "created_at": result[4],
                "updated_at": result[5],
                "metadata": json.loads(result[6] or "{}")
            }
            
            # Get characters associated with the project
            project_data["characters"] = self.get_project_characters(project_id)
            
            # Get files associated with the project
            project_data["files"] = self.get_project_files(project_id)
            
            return project_data
            
        except Exception as e:
            logging.error(f"Error retrieving project {project_id}: {e}")
            return None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.
        
        Returns:
            List[Dict[str, Any]]: List of project summaries
        """
        try:
            self.cursor.execute(
                "SELECT id, name, type, description, created_at, updated_at FROM projects ORDER BY updated_at DESC"
            )
            
            projects = []
            for row in self.cursor.fetchall():
                projects.append({
                    "id": row[0],
                    "name": row[1],
                    "type": row[2],
                    "description": row[3],
                    "created_at": row[4],
                    "updated_at": row[5]
                })
                
            return projects
            
        except Exception as e:
            logging.error(f"Error listing projects: {e}")
            return []
    
    def update_project(self, project_id: str, name: Optional[str] = None, 
                      description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update project details.
        
        Args:
            project_id (str): Project ID to update
            name (Optional[str]): New project name
            description (Optional[str]): New project description
            metadata (Optional[Dict[str, Any]]): Updated metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update_fields = []
            values = []
            
            if name is not None:
                update_fields.append("name = ?")
                values.append(name)
                
            if description is not None:
                update_fields.append("description = ?")
                values.append(description)
                
            if metadata is not None:
                update_fields.append("metadata = ?")
                values.append(json.dumps(metadata))
            
            # Always update the updated_at timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            if not update_fields:
                logging.warning(f"No fields to update for project {project_id}")
                return True  # Nothing to update, so technically successful
                
            query = f"UPDATE projects SET {', '.join(update_fields)} WHERE id = ?"
            values.append(project_id)
            
            self.cursor.execute(query, values)
            self.conn.commit()
            
            if self.cursor.rowcount == 0:
                logging.warning(f"Project {project_id} not found for update")
                return False
                
            logging.info(f"Updated project {project_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error updating project {project_id}: {e}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and all associated data.
        
        Args:
            project_id (str): ID of the project to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if project exists
            self.cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not self.cursor.fetchone():
                logging.warning(f"Project {project_id} not found for deletion")
                return False
            
            # Delete from database tables (cascade will handle related records)
            self.cursor.execute("DELETE FROM project_characters WHERE project_id = ?", (project_id,))
            self.cursor.execute("DELETE FROM project_files WHERE project_id = ?", (project_id,))
            self.cursor.execute("DELETE FROM project_sessions WHERE project_id = ?", (project_id,))
            self.cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            
            # Delete project directory
            project_dir = os.path.join(PROJECTS_DIR, project_id)
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            
            self.conn.commit()
            logging.info(f"Deleted project {project_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error deleting project {project_id}: {e}")
            return False
    
    # File Management Methods
    
    def add_project_file(self, project_id: str, file_path: str, file_type: str, 
                         description: str = "", is_reference: bool = False, 
                         is_output: bool = False) -> Optional[str]:
        """
        Add a file to a project.
        
        Args:
            project_id (str): Project ID
            file_path (str): Path to the file (relative to project directory)
            file_type (str): Type of file (pdf, music, text, etc.)
            description (str, optional): File description
            is_reference (bool): Whether this is a reference file
            is_output (bool): Whether this is an output file
            
        Returns:
            Optional[str]: File ID if successful, None otherwise
        """
        try:
            file_id = str(uuid.uuid4())
            
            self.cursor.execute(
                """INSERT INTO project_files 
                   (id, project_id, file_path, file_type, description, is_reference, is_output) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (file_id, project_id, file_path, file_type, description, is_reference, is_output)
            )
            
            self.conn.commit()
            logging.info(f"Added file {file_path} to project {project_id}")
            return file_id
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error adding file to project {project_id}: {e}")
            return None
    
    def get_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all files associated with a project.
        
        Args:
            project_id (str): Project ID
            
        Returns:
            List[Dict[str, Any]]: List of file details
        """
        try:
            self.cursor.execute(
                """SELECT id, file_path, file_type, description, is_reference, is_output, created_at 
                   FROM project_files WHERE project_id = ?""",
                (project_id,)
            )
            
            files = []
            for row in self.cursor.fetchall():
                files.append({
                    "id": row[0],
                    "file_path": row[1],
                    "file_type": row[2],
                    "description": row[3],
                    "is_reference": bool(row[4]),
                    "is_output": bool(row[5]),
                    "created_at": row[6]
                })
                
            return files
            
        except Exception as e:
            logging.error(f"Error retrieving files for project {project_id}: {e}")
            return []
    
    def delete_project_file(self, file_id: str, delete_physical_file: bool = False) -> bool:
        """
        Delete a file from a project.
        
        Args:
            file_id (str): File ID to delete
            delete_physical_file (bool): Whether to delete the actual file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get file information before deletion
            self.cursor.execute(
                "SELECT project_id, file_path FROM project_files WHERE id = ?",
                (file_id,)
            )
            
            result = self.cursor.fetchone()
            if not result:
                logging.warning(f"File {file_id} not found for deletion")
                return False
                
            project_id, file_path = result
            
            # Delete from database
            self.cursor.execute("DELETE FROM project_files WHERE id = ?", (file_id,))
            
            # Delete physical file if requested
            if delete_physical_file:
                full_path = os.path.join(PROJECTS_DIR, project_id, file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logging.info(f"Deleted physical file: {full_path}")
            
            self.conn.commit()
            logging.info(f"Deleted file {file_id} from project {project_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error deleting file {file_id}: {e}")
            return False
    
    # Session Management Methods
    
    def save_session(self, project_id: str, session_id: str, conversation_state: Dict[str, Any], 
                    active_roles: Dict[str, str]) -> bool:
        """
        Save the current conversation session state for a project.
        
        Args:
            project_id (str): Project ID
            session_id (str): Session ID
            conversation_state (Dict[str, Any]): Conversation state to save
            active_roles (Dict[str, str]): Active roles to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if session exists
            self.cursor.execute(
                "SELECT id FROM project_sessions WHERE id = ?",
                (session_id,)
            )
            
            conversation_json = json.dumps(conversation_state)
            roles_json = json.dumps(active_roles)
            
            if self.cursor.fetchone():
                # Update existing session
                self.cursor.execute(
                    """UPDATE project_sessions 
                       SET conversation_state = ?, active_roles = ?, last_accessed = CURRENT_TIMESTAMP 
                       WHERE id = ?""",
                    (conversation_json, roles_json, session_id)
                )
            else:
                # Create new session
                self.cursor.execute(
                    """INSERT INTO project_sessions 
                       (id, project_id, conversation_state, active_roles) 
                       VALUES (?, ?, ?, ?)""",
                    (session_id, project_id, conversation_json, roles_json)
                )
            
            self.conn.commit()
            logging.info(f"Saved session {session_id} for project {project_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error saving session {session_id} for project {project_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a conversation session state.
        
        Args:
            session_id (str): Session ID to load
            
        Returns:
            Optional[Dict[str, Any]]: Session data or None if not found
        """
        try:
            self.cursor.execute(
                """SELECT project_id, conversation_state, active_roles, last_accessed 
                   FROM project_sessions WHERE id = ?""",
                (session_id,)
            )
            
            result = self.cursor.fetchone()
            if not result:
                return None
                
            return {
                "project_id": result[0],
                "conversation_state": json.loads(result[1] or "{}"),
                "active_roles": json.loads(result[2] or "{}"),
                "last_accessed": result[3]
            }
            
        except Exception as e:
            logging.error(f"Error loading session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.
        
        Args:
            session_id (str): Session ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute("DELETE FROM project_sessions WHERE id = ?", (session_id,))
            self.conn.commit()
            
            if self.cursor.rowcount == 0:
                logging.warning(f"Session {session_id} not found for deletion")
                return False
                
            logging.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error deleting session {session_id}: {e}")
            return False
    
    # Character Management Methods
    
    def add_character(self, project_id: str, character_name: str, llm_name: str, 
                      background: str = "") -> Optional[str]:
        """
        Add a character to a project.
        
        Args:
            project_id (str): Project ID
            character_name (str): Name of the character
            llm_name (str): LLM to assign to this character
            background (str, optional): Character background info
            
        Returns:
            Optional[str]: Character ID if successful, None otherwise
        """
        try:
            character_id = str(uuid.uuid4())
            
            self.cursor.execute(
                """INSERT INTO project_characters 
                   (id, project_id, character_name, llm_name, background) 
                   VALUES (?, ?, ?, ?, ?)""",
                (character_id, project_id, character_name, llm_name, background)
            )
            
            self.conn.commit()
            logging.info(f"Added character {character_name} to project {project_id}")
            return character_id
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error adding character to project {project_id}: {e}")
            return None
    
    def get_project_characters(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all characters associated with a project.
        
        Args:
            project_id (str): Project ID
            
        Returns:
            List[Dict[str, Any]]: List of character details
        """
        try:
            self.cursor.execute(
                """SELECT id, character_name, llm_name, background, created_at 
                   FROM project_characters WHERE project_id = ?""",
                (project_id,)
            )
            
            characters = []
            for row in self.cursor.fetchall():
                characters.append({
                    "id": row[0],
                    "character_name": row[1],
                    "llm_name": row[2],
                    "background": row[3],
                    "created_at": row[4]
                })
                
            return characters
            
        except Exception as e:
            logging.error(f"Error retrieving characters for project {project_id}: {e}")
            return []
    
    def delete_character(self, character_id: str) -> bool:
        """
        Delete a character from a project.
        
        Args:
            character_id (str): Character ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute("DELETE FROM project_characters WHERE id = ?", (character_id,))
            self.conn.commit()
            
            if self.cursor.rowcount == 0:
                logging.warning(f"Character {character_id} not found for deletion")
                return False
                
            logging.info(f"Deleted character {character_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error deleting character {character_id}: {e}")
            return False
    
    def __del__(self):
        """Close database connection when the object is destroyed."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
