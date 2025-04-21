# /Users/nickfox137/Documents/llm-creative-studio/python/ollama_service.py
"""
Ollama Service Module

This module provides integration with locally running Ollama models:
- qwen2.5:14b-instruct-q8_0 for retrieval and text generation
- snowflake-arctic-embed:137m for document embedding generation

It enables local RAG (Retrieval Augmented Generation) capabilities
for the LLMCreativeStudio without external API dependencies.
"""

import os
import logging
import json
import httpx
import asyncio
import numpy as np
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import time
import traceback

# Import the enhanced chunking function
from enhanced_chunking import chunk_research_paper

# Configure logging
logger = logging.getLogger(__name__)

class OllamaService:
    """
    Service for interacting with local Ollama models for document processing,
    embedding generation, and retrieval augmented generation.
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 rag_model: str = "qwen2.5:14b-instruct-q8_0",
                 embedding_model: str = "snowflake-arctic-embed:137m"):
        """
        Initialize the Ollama service.
        
        Args:
            base_url: URL for the Ollama API
            rag_model: Model to use for retrieval and generation
            embedding_model: Model to use for embedding generation
        """
        self.base_url = base_url
        self.rag_model = rag_model
        self.embedding_model = embedding_model
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
        # Vector storage - project_id -> {document_id -> {embeddings, chunks}}
        self.vector_store_dir = Path("data/vector_stores")
        self.vector_store_dir.mkdir(exist_ok=True, parents=True)
        self.vector_stores = {}
        
        # Keep track of models we've checked for availability
        self.available_models = set()
        
        logger.info(f"Initialized Ollama service with RAG model {rag_model} and embedding model {embedding_model}")
    
    async def check_availability(self) -> bool:
        """
        Check if Ollama is available and if the required models are installed.
        
        Returns:
            bool: True if Ollama is available with required models, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code != 200:
                    logger.error(f"Ollama server responded with status code {response.status_code}")
                    return False
                
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                
                # Check if required models are available
                rag_model_available = any(self.rag_model in model for model in available_models)
                embedding_model_available = any(self.embedding_model in model for model in available_models)
                
                if not rag_model_available:
                    logger.warning(f"RAG model {self.rag_model} not found in Ollama")
                if not embedding_model_available:
                    logger.warning(f"Embedding model {self.embedding_model} not found in Ollama")
                
                # Store available models
                self.available_models = set(available_models)
                
                return rag_model_available and embedding_model_available
                
        except httpx.RequestError as e:
            logger.error(f"Error connecting to Ollama: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking Ollama availability: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def process_all_project_documents(self, project_id: str) -> Dict[str, Any]:
        """
        Process all documents for a project for RAG.
        
        Args:
            project_id: Project ID to process documents for
            
        Returns:
            Dict[str, Any]: Summary of processing results
        """
        try:
            # Import here to avoid circular imports
            from project_manager import ProjectManager
            
            pm = ProjectManager()
            files = pm.get_project_files(project_id)
            
            if not files:
                logger.warning(f"No files found for project {project_id}")
                return {"success": False, "message": "No files found for project", "processed": 0, "failed": 0}
            
            # Process each file
            results = {
                "success": True,
                "total": len(files),
                "processed": 0,
                "failed": 0,
                "file_results": []
            }
            
            for file in files:
                file_id = file["id"]
                file_path = file["file_path"]
                
                # Import data access here to avoid circular imports
                from data_access import DataAccess
                data_access = DataAccess()
                
                # Get document content
                content = await data_access.get_document_content(file_id)
                
                if not content:
                    logger.warning(f"Could not get content for file {file_id}")
                    results["failed"] += 1
                    results["file_results"].append({
                        "file_id": file_id,
                        "success": False,
                        "message": "Could not read file content"
                    })
                    continue
                
                # Process the document
                success = await self.process_document(
                    project_id=project_id,
                    document_id=file_id,
                    document_text=content
                )
                
                if success:
                    results["processed"] += 1
                    results["file_results"].append({
                        "file_id": file_id,
                        "success": True
                    })
                else:
                    results["failed"] += 1
                    results["file_results"].append({
                        "file_id": file_id,
                        "success": False,
                        "message": "Processing failed"
                    })
            
            # Update success flag if any failures
            if results["failed"] > 0:
                results["success"] = False
                results["message"] = f"Processed {results['processed']} files with {results['failed']} failures"
            else:
                results["message"] = f"Successfully processed {results['processed']} files"
                
            return results
            
        except Exception as e:
            logger.error(f"Error processing all project documents: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "processed": 0,
                "failed": 0
            }
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for a text using the Ollama embedding model.
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            # Truncate text if very long 
            if len(text) > 8000:
                text = text[:8000]  # Prevent token limit issues
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.embedding_model, "prompt": text}
                )
                
                if response.status_code != 200:
                    logger.error(f"Error generating embeddings: {response.status_code}")
                    return []
                
                result = response.json()
                return result.get("embedding", [])
                
        except httpx.RequestError as e:
            logger.error(f"Error connecting to Ollama for embedding generation: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error generating embeddings: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def generate_response(self, 
                              prompt: str, 
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7,
                              max_tokens: int = 1024) -> str:
        """
        Generate a response using the RAG model.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            str: Generated response
        """
        try:
            payload = {
                "model": self.rag_model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True  # Use streaming to handle larger responses
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        logger.error(f"Error generating response: {response.status_code}")
                        return f"Error: Could not generate response (Status {response.status_code})"
                    
                    # Process the streaming response
                    full_response = ""
                    async for chunk in response.aiter_lines():
                        if not chunk.strip():
                            continue
                        
                        try:
                            data = json.loads(chunk)
                            if "response" in data:
                                full_response += data["response"]
                        except json.JSONDecodeError:
                            logger.error(f"Could not parse Ollama response chunk: {chunk[:100]}...")
                            continue
                    
                    return full_response
                
        except httpx.RequestError as e:
            logger.error(f"Error connecting to Ollama for response generation: {e}")
            return f"Error: Could not connect to Ollama ({str(e)})"
        except Exception as e:
            logger.error(f"Unexpected error generating response: {e}")
            logger.error(traceback.format_exc())
            return f"Error: Failed to generate response ({str(e)})"
    
    async def process_document(self, 
                              project_id: str,
                              document_id: str,
                              document_text: str,
                              chunk_size: int = 1000,
                              chunk_overlap: int = 200) -> bool:
        """
        Process a document for RAG:
        1. Chunk the document
        2. Generate embeddings for each chunk
        3. Store in the vector store
        
        Args:
            project_id: Project ID to associate with document
            document_id: Unique ID for the document
            document_text: Document text content
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check that embeddings model is available
            if self.embedding_model not in self.available_models and not await self.check_availability():
                logger.error(f"Embedding model {self.embedding_model} not available")
                return False
            
            # Chunk document
            chunk_data = self._chunk_text(document_text, chunk_size, chunk_overlap)
            logger.info(f"Document {document_id} chunked into {len(chunk_data)} parts")

            # Initialize project vector store if needed
            if project_id not in self.vector_stores:
                # Try to load from disk first
                if not await self._load_vector_store(project_id):
                    # Create new if not found
                    self.vector_stores[project_id] = {}
            
            # Generate and store embeddings for each chunk
            document_embeddings = []
            for i, chunk_info in enumerate(chunk_data):
                embedding = await self.generate_embedding(chunk_info["content"])
                if embedding:
                    document_embeddings.append({
                        "chunk_id": i,
                        "text": chunk_info["content"],
                        "embedding": embedding,
                        "heading": chunk_info["heading"],
                        "level": chunk_info["level"]
                    })
                # Add a small delay to avoid overwhelming Ollama
                await asyncio.sleep(0.1)

            # Store the embeddings
            self.vector_stores[project_id][document_id] = document_embeddings
            
            # Save to disk
            await self._save_vector_store(project_id)
            
            logger.info(f"Successfully processed document {document_id} for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def retrieve_context(self, 
                             project_id: str, 
                             query: str, 
                             top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from the vector store based on query.
        
        Args:
            project_id: Project ID to search in
            query: Query to search for
            top_k: Number of chunks to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of relevant text chunks with metadata
        """
        try:
            # Check if project exists in vector store
            if project_id not in self.vector_stores:
                # Try to load from disk
                if not await self._load_vector_store(project_id):
                    logger.warning(f"No vector store found for project {project_id}")
                    return []
            
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Collect all chunks from all documents with similarity scores
            all_chunks = []
            for document_id, chunks in self.vector_stores[project_id].items():
                for chunk in chunks:
                    similarity = self._cosine_similarity(query_embedding, chunk["embedding"])
                    all_chunks.append({
                        "document_id": document_id,
                        "chunk_id": chunk["chunk_id"],
                        "text": chunk["text"],
                        "similarity": similarity,
                        "heading": chunk["heading"],
                        "level": chunk["level"]
                    })

            # Calculate a score based on similarity, heading match, and level
            for chunk in all_chunks:
                score = chunk["similarity"]
                # Bonus for heading match (simple keyword match)
                if any(keyword.lower() in chunk["heading"].lower() for keyword in query.split()):
                    score += 0.2  # Example bonus
                # Penalty for deeper levels (higher level number)
                score -= chunk["level"] * 0.1  # Example penalty

                chunk["score"] = score

            # Sort by combined score and get top_k
            all_chunks.sort(key=lambda x: x["score"], reverse=True)
            return all_chunks[:top_k]

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def answer_with_rag(self, 
                             project_id: str, 
                             query: str,
                             top_k: int = 3,
                             use_thinking: bool = False) -> Dict[str, Any]:
        """
        Answer a query using RAG.
        
        Args:
            project_id: Project ID to search in
            query: Query to answer
            top_k: Number of context chunks to include
            use_thinking: Whether to add thinking steps (for debug/transparency)
            
        Returns:
            Dict[str, Any]: Generated answer with metadata
        """
        # Retrieve relevant context
        start_time = time.time()
        context_chunks = await self.retrieve_context(project_id, query, top_k)
        retrieval_time = time.time() - start_time
        
        # Format result dictionary
        result = {
            "query": query,
            "sources": [],
            "answer": "",
            "thinking": "",
            "metadata": {
                "retrieval_time_ms": int(retrieval_time * 1000),
                "generation_time_ms": 0,
                "total_time_ms": 0
            }
        }
        
        # If no context found, generate a response without context
        if not context_chunks:
            result["thinking"] = "No relevant context found in the project documents."
            
            # Use the RAG model directly
            start_time = time.time()
            result["answer"] = await self.generate_response(
                prompt=query,
                system_prompt="You are a helpful research assistant. Answer the user's question based on your knowledge."
            )
            generation_time = time.time() - start_time
            result["metadata"]["generation_time_ms"] = int(generation_time * 1000)
            result["metadata"]["total_time_ms"] = int((retrieval_time + generation_time) * 1000)
            
            return result
        
        # Build context from chunks
        context_text = ""
        for i, chunk in enumerate(context_chunks):
            context_text += f"\n\nContext {i+1} (Document: {chunk['document_id']}, Similarity: {chunk['similarity']:.2f}):\n{chunk['text']}"
            result["sources"].append({
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "similarity": chunk["similarity"],
                "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            })
        
        # Add thinking if requested
        if use_thinking:
            result["thinking"] = f"Found {len(context_chunks)} relevant context chunks.\n{context_text}"
        
        # Build prompt with context
        system_prompt = """You are a helpful research assistant. Answer the user's question based ONLY on the provided context.
        
        Guidelines:
        1. If the context doesn't contain enough information to fully answer the question, acknowledge this clearly
        2. Always cite the specific document source (e.g. "According to Document 1...")
        3. Do not make up or infer information that isn't directly in the context
        4. If relevant information appears in multiple sources, synthesize it and cite all relevant sources
        5. If you're uncertain about something in the context, express that uncertainty
        6. Keep your answer concise but comprehensive
        """
        
        prompt = f"""Here is context information from relevant documents:

{context_text}

Based ONLY on the above context, please answer this question: {query}

Remember to cite your sources and only use information from the provided context."""
        
        # Generate response
        start_time = time.time()
        result["answer"] = await self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for more factual responses
        )
        generation_time = time.time() - start_time
        
        # Update timing metadata
        result["metadata"]["generation_time_ms"] = int(generation_time * 1000)
        result["metadata"]["total_time_ms"] = int((retrieval_time + generation_time) * 1000)
        
        return result
    
    async def _save_vector_store(self, project_id: str) -> bool:
        """
        Save the vector store to disk.
        
        Args:
            project_id: Project ID to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if project_id not in self.vector_stores:
                logger.warning(f"No vector store to save for project {project_id}")
                return False
            
            # Prepare a serializable version (without the chunk text to save space)
            serializable_store = {}
            for document_id, chunks in self.vector_stores[project_id].items():
                serializable_store[document_id] = []
                for chunk in chunks:
                    serializable_store[document_id].append({
                        "chunk_id": chunk["chunk_id"],
                        "embedding": chunk["embedding"],
                        "heading": chunk["heading"],
                        "level": chunk["level"]
                    })

            project_file = self.vector_store_dir / f"{project_id}.json"
            
            with open(project_file, 'w') as f:
                json.dump(serializable_store, f)
                
            logger.info(f"Saved vector store for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving vector store for project {project_id}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _load_vector_store(self, project_id: str) -> bool:
        """
        Load the vector store from disk.
        
        Args:
            project_id: Project ID to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project_file = self.vector_store_dir / f"{project_id}.json"
            
            if not project_file.exists():
                logger.warning(f"No vector store file found for project {project_id}")
                return False
            
            with open(project_file, 'r') as f:
                serialized_store = json.load(f)
            
            # We need to reconnect with document text from the document store
            # For now, just load the embeddings since we can still do similarity search
            self.vector_stores[project_id] = {}
            
            for document_id, chunks in serialized_store.items():
                self.vector_stores[project_id][document_id] = []
                
                for chunk in chunks:
                    self.vector_stores[project_id][document_id].append({
                        "chunk_id": chunk["chunk_id"],
                        "embedding": chunk["embedding"],
                        "text": "Embedded text",  # Placeholder - will be filled in when needed
                        "heading": chunk.get("heading", ""), # added to fix: Unused variable 'chunk'
                        "level": chunk.get("level", 0) # added to fix: Unused variable 'chunk'
                    })

            logger.info(f"Loaded vector store for project {project_id} with {len(self.vector_stores[project_id])} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error loading vector store for project {project_id}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Split text into overlapping chunks with a preference for semantic boundaries.
        For research papers, uses section-based chunking if possible.
        
        Args:
            text: Text to split
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List[str]: List of text chunks
        """
        # Try to detect if this is a research paper based on content patterns
        research_paper_indicators = [
            "Abstract", "Introduction", "Methodology", "Results", "Discussion", "Conclusion", 
            "References", "et al.", "Fig.", "Table", "Eq.", "i.e."
        ]
        
        indicator_count = sum(1 for indicator in research_paper_indicators if indicator in text)
        
        # If this looks like a research paper, use specialized chunking
        if indicator_count >= 3:  # At least 3 indicators suggest this is a research paper
            logging.info(f"Detected research paper format, using section-based chunking")
            chunks = chunk_research_paper(text, max_chunk_size=chunk_size)
            logging.info(f"Research paper split into {len(chunks)} semantic sections")
            return [chunk["content"] for chunk in chunks]

        # Otherwise use the general chunking method
        # Split text by double newline to preserve paragraph boundaries
        paragraphs = text.split("\n\n")
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            # Handle case where a single paragraph is larger than chunk_size
            if len(para) > chunk_size:
                # If we have content in the current chunk, add it first
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    # Start a new chunk with overlap from the previous chunk
                    if chunks[-1]:
                        overlap_text = chunks[-1][-chunk_overlap:] if len(chunks[-1]) > chunk_overlap else chunks[-1]
                        current_chunk = [overlap_text]
                        current_size = len(overlap_text)
                    else:
                        current_chunk = []
                        current_size = 0
                
                # Process the long paragraph
                for i in range(0, len(para), chunk_size - chunk_overlap):
                    if i > 0:
                        start = i - chunk_overlap
                    else:
                        start = 0
                    
                    end = min(i + chunk_size, len(para))
                    chunks.append(para[start:end])
                    
                    # Stop if we've reached the end of the paragraph
                    if end >= len(para):
                        break
                
                # Reset for next paragraph
                current_chunk = []
                current_size = 0
            else:
                # See if adding this paragraph would exceed the chunk size
                if current_size + len(para) + (2 if current_chunk else 0) > chunk_size:
                    # Finish current chunk
                    chunks.append("\n\n".join(current_chunk))
                    
                    # Calculate overlap to maintain continuity
                    if len(chunks[-1]) > chunk_overlap:
                        # Find a nice sentence boundary for overlap if possible
                        overlap_text = chunks[-1][-chunk_overlap:]
                        sentence_boundaries = [". ", "! ", "? ", ".\n", "!\n", "?\n"]
                        for boundary in sentence_boundaries:
                            last_boundary = overlap_text.rfind(boundary)
                            if last_boundary != -1:
                                # Include the boundary itself and context after it
                                last_boundary += len(boundary)
                                overlap_text = chunks[-1][-chunk_overlap:][last_boundary:]
                                # Add a bit of context before the boundary
                                overlap_text = chunks[-1][-chunk_overlap:][max(0, last_boundary-50):] 
                                break
                    else:
                        overlap_text = chunks[-1]
                    
                    # Start new chunk with overlap
                    current_chunk = [overlap_text, para]
                    current_size = len(overlap_text) + len(para) + 2  # +2 for paragraph separator
                else:
                    # Add paragraph to current chunk
                    current_chunk.append(para)
                    current_size += len(para) + (2 if current_chunk else 0)  # +2 for paragraph separator
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
    
    def _chunk_research_paper(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        logger = logging.getLogger(__name__)
        """
        Split a research paper into chunks based on section headings with fallback mechanisms.
        
        Args:
            text: Text of the research paper
            max_chunk_size: Maximum size for a single chunk
            
        Returns:
            List[str]: List of text chunks preserving semantic structure where possible
        """
        
        # Common section heading patterns in research papers across different disciplines
        section_patterns = [
            # Common main sections
            r"^\s*Abstract[\s:]*$",
            r"^\s*Introduction[\s:]*$",
            r"^\s*Background[\s:]*$",
            r"^\s*Related Work[\s:]*$", 
            r"^\s*Methodology[\s:]*$",
            r"^\s*Methods[\s:]*$",
            r"^\s*Materials and Methods[\s:]*$",
            r"^\s*Experimental Setup[\s:]*$",
            r"^\s*Results[\s:]*$",
            r"^\s*Discussion[\s:]*$",
            r"^\s*Conclusion[\s:]*$",
            r"^\s*Conclusions[\s:]*$",
            r"^\s*References[\s:]*$",
            r"^\s*Bibliography[\s:]*$",
            
            # Additional common sections
            r"^\s*Literature Review[\s:]*$",
            r"^\s*Theoretical Framework[\s:]*$",
            r"^\s*Data Collection[\s:]*$",
            r"^\s*Analysis[\s:]*$",
            r"^\s*Evaluation[\s:]*$",
            r"^\s*Implementation[\s:]*$",
            r"^\s*System Design[\s:]*$",
            r"^\s*Proposed Method[\s:]*$",
            r"^\s*Proposed Approach[\s:]*$",
            r"^\s*Experiments[\s:]*$",
            r"^\s*Findings[\s:]*$",
            r"^\s*Limitations[\s:]*$",
            r"^\s*Future Work[\s:]*$",
            r"^\s*Acknowledgments[\s:]*$",
            r"^\s*Appendix[\s:]*$",
            
            # Numbered sections and generic patterns (should be last to avoid false positives)
            r"^\s*\d+[\.\)]\s+[A-Z][\w\s]+",  # Numbered sections like "1. Introduction"
            r"^\s*[A-Z]\.\s+[A-Z][\w\s]+",    # Lettered sections like "A. Methodology"
            r"^\s*[IVXLCDM]+\.\s+[A-Z][\w\s]+", # Roman numeral sections
            r"^\s*[A-Z][A-Za-z\s]+$"           # Any capitalized heading on its own line
        ]
        
        # Function to split text by pattern and check chunk sizes
        def split_by_pattern(text, pattern, min_lines=3):  # Reduced min_lines for better compatibility with shorter sections
            logger.debug(f"Attempting to split text by pattern: {pattern}")
            chunks = []
            lines = text.split('\n')
            current_chunk = []
            current_heading = "Introduction"  # Default for start if no heading detected
            
            for line in lines:
                if re.match(pattern, line, re.MULTILINE):
                    # Save the previous chunk if it exists and has sufficient content
                    if current_chunk and len(current_chunk) >= min_lines:
                        chunks.append({
                            "heading": current_heading,
                            "content": '\n'.join(current_chunk),
                            "size": len('\n'.join(current_chunk))
                        })
                    # Update heading and start new chunk
                    current_heading = line.strip()
                    current_chunk = [line]
                else:
                    current_chunk.append(line)
            
            # Add the last chunk
            if current_chunk and len(current_chunk) >= min_lines:
                chunks.append({
                    "heading": current_heading,
                    "content": '\n'.join(current_chunk),
                    "size": len('\n'.join(current_chunk))
                })
            
            return chunks
        
        # Try to split by main sections first
        combined_pattern = '|'.join(section_patterns)
        section_chunks = split_by_pattern(text, combined_pattern)
        logger.debug(f"Detected {len(section_chunks)} main sections in the research paper")
        
        # If no sections were found or there's just one giant chunk, try fallback approaches
        if not section_chunks or (len(section_chunks) == 1 and section_chunks[0]["size"] > max_chunk_size):
            # Fallback 1: Try looking for subsections (often numbered like 1.1, 1.2, etc.)
            logger.debug("No main sections found or section too large, trying subsection detection")
            
            # Multiple patterns for different subsection formats
            subsection_patterns = [
                r"^\s*\d+\.\d+[\.\s\)]*[A-Za-z]",  # Standard decimal subsections: 1.1 Title
                r"^\s*\d+\.\d+\s+",                 # Subsections without text on same line: 1.1
                r"^\s*[A-Z]\.\d+\s+",                # Letter-based subsections: A.1
                r"^\s*\d+\s*\.\s*\d+\s+"             # Spaced subsections: 1 . 1
            ]
            
            subsection_pattern = "|".join(subsection_patterns)
            logger.debug(f"Using subsection pattern: {subsection_pattern}")
            section_chunks = split_by_pattern(text, subsection_pattern)
            logger.debug(f"Detected {len(section_chunks)} subsections in the research paper")
        
        # If still no good chunks, fall back to paragraph-based chunking
        final_chunks = []
        
        if not section_chunks or all(chunk["size"] > max_chunk_size for chunk in section_chunks):
            logger.debug("No sections or subsections found or all sections too large, falling back to paragraph chunking")
            # Paragraph-based chunking as final fallback
            paragraphs = text.split('\n\n')
            current_chunk = []
            current_size = 0
            
            for para in paragraphs:
                para_size = len(para)
                
                # If single paragraph is too big, we'll have to split it by sentences
                if para_size > max_chunk_size:
                    # Try to split by sentences, handling cases where there might not be proper spacing
                    sentences = re.split(r'(?<=[.!?])\s+|(?<=[.!?])(?=[A-Z])', para)
                    sentence_chunk = []
                    sentence_size = 0
                    
                    for sentence in sentences:
                        if sentence_size + len(sentence) + 1 <= max_chunk_size or not sentence_chunk:
                            sentence_chunk.append(sentence)
                            sentence_size += len(sentence) + 1
                        else:
                            final_chunks.append('\n'.join(sentence_chunk))
                            sentence_chunk = [sentence]
                            sentence_size = len(sentence)
                    
                    if sentence_chunk:
                        final_chunks.append('\n'.join(sentence_chunk))
                
                # Normal paragraph handling
                elif current_size + para_size <= max_chunk_size or not current_chunk:
                    current_chunk.append(para)
                    current_size += para_size + 2  # +2 for paragraph break
                else:
                    final_chunks.append('\n\n'.join(current_chunk))
                    current_chunk = [para]
                    current_size = para_size
            
            # Add the last chunk if it exists
            if current_chunk:
                final_chunks.append('\n\n'.join(current_chunk))
        else:
            # Process the section chunks, splitting any that are too large
            for chunk in section_chunks:
                if chunk["size"] <= max_chunk_size:
                    final_chunks.append(chunk["content"])
                else:
                    # Split large sections by paragraphs
                    heading = chunk["heading"]
                    content = chunk["content"]
                    paragraphs = content.split('\n\n')
                    
                    current_chunk = [heading]  # Start with the heading
                    current_size = len(heading)
                    
                    for para in paragraphs:
                        if current_size + len(para) + 2 <= max_chunk_size or len(current_chunk) == 1:  # Only heading so far
                            current_chunk.append(para)
                            current_size += len(para) + 2
                        else:
                            final_chunks.append('\n\n'.join(current_chunk))
                            current_chunk = [heading + " (continued)", para]
                            current_size = len(heading) + 13 + len(para)  # 13 for " (continued)"
                    
                    if len(current_chunk) > 1:  # More than just the heading
                        final_chunks.append('\n\n'.join(current_chunk))
        
        logger.debug(f"Research paper chunking completed with {len(final_chunks)} chunks")
        return final_chunks
        
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            float: Cosine similarity (0-1)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        # Convert to numpy arrays
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        
        # Calculate dot product and magnitudes
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        # Avoid division by zero
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
