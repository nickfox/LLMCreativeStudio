# /Users/nickfox137/Documents/llm-creative-studio/python/data.py
import json
import logging
from typing import List
import pypdf
from config import METADATA_FILE, DATA_DIR
from llms import LLM  # Import the base class.
from fastapi import HTTPException
import os

def load_metadata(metadata_path: str = METADATA_FILE) -> List[dict]:
    """Loads metadata from a JSON file."""
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        logging.info(f"Loaded metadata from {metadata_path}")
        return metadata
    except FileNotFoundError:
        logging.error(f"Metadata file not found: {metadata_path}")
        raise HTTPException(status_code=500, detail=f"Metadata file not found: {metadata_path}")
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON in: {metadata_path}")
        raise HTTPException(status_code=500, detail=f"Error decoding JSON in: {metadata_path}")


async def select_relevant_documents(query: str, metadata: List[dict], llm: LLM) -> List[str]: #llm is passed in
    """Selects relevant documents based on a user query."""
    prompt = f"""You are a helpful assistant that selects relevant documents based on a user query.
    Here is the user query:
    '{query}'
    Here is the metadata for available documents:
    {json.dumps(metadata, indent=2)}

    Return a JSON array of file paths of the MOST relevant documents.  If no documents are relevant, return an empty array.
    Be concise and only return the array of file paths, nothing else.
    """

    try:
        # Use the llm instance (passed as argument) for document selection.
        response = await llm.get_response(prompt)
        logging.info(f"Document selection response: {response}")
        relevant_files = json.loads(response)  # Parse the JSON response
        return relevant_files
    except json.JSONDecodeError:
        logging.error(f"Error decoding document selection response: {response}")
        return [] #Return empty array on failure
    except Exception as e:
        logging.exception(f"Error in document selection: {e}")
        return []


def read_file_content(file_path: str) -> str:
    """Reads the content of a file, handling different file types."""
    try:
        # Construct *absolute* path, starting from project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        full_path = os.path.join(project_root, file_path)
        logging.info(f"Reading file: {full_path}")  # Log the full path

        if file_path.endswith(".pdf"):
            with open(full_path, "rb") as f:
                reader = pypdf.PdfReader(f)  # Use PdfReader
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        elif file_path.endswith(".txt"):
            with open(full_path, "r") as f:
                return f.read()
        else:
            logging.warning(f"Unsupported file type: {file_path}")
            return ""
    except FileNotFoundError:
        logging.error(f"File not found: {full_path}")  # Log full path
        return ""
    except Exception as e:
        logging.exception(f"Error reading file {full_path}: {e}")  # Log full path
        return ""
