# /Users/nickfox137/Documents/llm-creative-studio/python/data_access.py

import sqlite3
import json
import logging
from typing import List, Dict, Optional
from config import DATA_DIR, METADATA_FILE  # Import from config
import os

DATABASE_FILE = "metadata.db"  # Database file in the python directory

class DataAccess:
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self.logger = logging.getLogger(__name__)
        self.create_table() # Create table if it doesn't exist.

    def _get_connection(self):
        """Establishes and returns a database connection."""
        return sqlite3.connect(self.db_file)

    def create_table(self):
        """Creates the 'documents' table if it doesn't exist."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    title TEXT,
                    type TEXT,
                    keywords TEXT,
                    summary TEXT,
                    authors TEXT,
                    section_titles TEXT
                )
            ''')
            conn.commit()
            conn.close()
            self.logger.info("Documents table created (or already exists).")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating table: {e}")

    def insert_document(self, data: Dict) -> Optional[int]:
        """Inserts a new document record into the database.
        
        Args:
            data: A dictionary containing the document metadata.  Must include
              'file_path', and can optionally include 'title', 'type', 'keywords',
              'summary', 'authors', and 'section_titles'.

        Returns:
            The ID of the newly inserted row, or None on failure.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (file_path, title, type, keywords, summary, authors, section_titles)
                VALUES (:file_path, :title, :type, :keywords, :summary, :authors, :section_titles)
            ''', data)
            conn.commit()
            last_row_id = cursor.lastrowid  # Get the ID of the inserted row
            conn.close()
            self.logger.info(f"Inserted document: {data['file_path']}")
            return last_row_id
        except sqlite3.IntegrityError:
            # Handle UNIQUE constraint violation (file_path already exists)
            self.logger.warning(f"Document already exists: {data['file_path']}")
            return None
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting document: {e}")
            return None


    def get_all_documents(self) -> List[Dict]:
        """Retrieves all document records from the database.
        Returns:
            A list of dictionaries, where each dictionary represents a document.
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents")
            rows = cursor.fetchall()
            conn.close()
            # Convert rows to dictionaries
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Retrieves a document by its ID."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None  # Return None if not found
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving document by ID: {e}")
            return None

    def get_documents_by_path(self, file_path: str) -> List[Dict]:
        """Retrieves document(s) by their file path.  Since file_path is
        UNIQUE, this should return a list containing 0 or 1 documents."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE file_path = ?", (file_path,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving document by path: {e}")
            return []

    def update_document(self, doc_id: int, data: Dict):
        """Updates an existing document record."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Construct the SET part of the SQL query dynamically
            set_clause = ", ".join([f"{key} = :{key}" for key in data])
            query = f"UPDATE documents SET {set_clause} WHERE id = :id"
            data['id'] = doc_id  # Add the ID to the data dictionary
            cursor.execute(query, data)
            conn.commit()
            conn.close()
            self.logger.info(f"Updated document with ID: {doc_id}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error updating document: {e}")
            return False

    def delete_document(self, doc_id: int):
        """Deletes a document record by its ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            conn.close()
            self.logger.info(f"Deleted document with ID: {doc_id}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting document: {e}")
            return False
    
    def delete_document_by_path(self, file_path: str):
        """Deletes a document by its file path."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE file_path = ?", (file_path,))
            conn.commit()
            conn.close()
            self.logger.info(f"Deleted document with path: {file_path}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting document by path: {e}")
            return False

    def import_from_json(self, json_file: str = METADATA_FILE):
        """Imports metadata from a JSON file (for initial migration)."""

        # Check if the database is empty before importing.  This prevents
        # accidentally importing the same data multiple times.
        if self.get_all_documents():
            self.logger.info("Database is not empty. Skipping JSON import.")
            return

        try:
            with open(json_file, 'r') as f:
                metadata_list = json.load(f)
            # Make all paths relative to the project root directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            for item in metadata_list:
                # Make file_path relative to project root
                absolute_path = os.path.normpath(os.path.join(project_root, item['file_path']))
                relative_path = os.path.relpath(absolute_path, project_root)
                item['file_path'] = relative_path

                # Convert lists to comma-separated strings.
                for key in ("keywords", "authors", "section_titles"):
                    if key in item and isinstance(item[key], list):
                        item[key] = ", ".join(item[key])


            for item in metadata_list:
                self.insert_document(item)
            self.logger.info(f"Imported metadata from {json_file}")

        except FileNotFoundError:
            self.logger.error(f"JSON file not found: {json_file}")
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON in: {json_file}")
        except Exception as e:
            self.logger.exception(f"Error importing from JSON: {e}")


    def clear_database(self):
        """Deletes all rows from the documents table.  USE WITH CAUTION."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents")
            conn.commit()
            conn.close()
            self.logger.info("All documents deleted from database.")
        except sqlite3.Error as e:
            self.logger.error(f"Error clearing database: {e}")

# Example Usage (for testing):
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Set logging to INFO
    dao = DataAccess()
    
    # dao.clear_database() # Use this with caution, while testing.
    
    dao.import_from_json()

    all_docs = dao.get_all_documents()
    print("All Documents:", all_docs)

    # Example usage of other methods (add/uncomment as needed for testing)

    # new_doc = {
    #     "file_path": "data/new_document.txt",
    #     "title": "New Document",
    #     "type": "test",
    #     "keywords": "test, new",
    #     "summary": "A test document.",
    #     "authors": "Test Author",
    #     "section_titles": "Section 1, Section 2"
    # }
    # new_id = dao.insert_document(new_doc)
    # print(f"New doc ID: {new_id}")


    # doc_by_id = dao.get_document_by_id(new_id)
    # print("Doc by ID:", doc_by_id)

    # updated_doc = {
    #     "title": "Updated Document Title",
    #     "keywords": "test, updated, document"
    # }
    # dao.update_document(new_id, updated_doc)
    # print("Updated Doc:", dao.get_document_by_id(new_id))

    # dao.delete_document(new_id)
    # print("All Documents After Delete:", dao.get_all_documents())
