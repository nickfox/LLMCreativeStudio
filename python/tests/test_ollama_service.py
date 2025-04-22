# /Users/nickfox137/Documents/llm-creative-studio/python/tests/test_ollama_service.py
"""
Tests for the OllamaService class, focusing on the research paper chunking functionality.
"""

import pytest
import os
import sys
import re
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add the parent directory to sys.path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ollama_service import OllamaService

class TestOllamaService:
    """Test suite for OllamaService class."""
    
    @pytest.fixture
    def ollama_service(self):
        """Create an OllamaService instance for testing."""
        service = OllamaService()
        return service
    
    def test_chunk_research_paper_section_detection(self, ollama_service):
        """Test that the _chunk_research_paper method correctly detects sections."""
        # Sample research paper text with clear sections
        paper_text = """
        Abstract
        This is the abstract of the paper.

        Introduction
        This is the introduction section.

        Methodology
        This is the methodology section.

        Results
        These are the results.

        Discussion
        This is the discussion section.

        Conclusion
        This is the conclusion.

        References
        [1] Author, A. (2023). Title. Journal.
        """
        
        chunks = ollama_service._chunk_research_paper(paper_text)
        
        # Check that we have the expected number of chunks
        assert len(chunks) >= 5, f"Expected at least 5 chunks, got {len(chunks)}"
        
        # Check that each section is in its own chunk
        section_names = ["Abstract", "Introduction", "Methodology", "Results", "Discussion", "Conclusion"]
        for section in section_names:
            assert any(section in chunk for chunk in chunks), f"Section '{section}' not found in any chunk"
    
    def test_chunk_research_paper_hierarchical(self, ollama_service):
        """Test that the _chunk_research_paper method handles hierarchical sections."""
        # Sample research paper text with hierarchical sections
        paper_text = """
        Abstract
        This is the abstract of the paper.

        1. Introduction
        This is the introduction section.

        2. Methodology
        This is the methodology section.

        2.1 Data Collection
        This describes data collection.

        2.2 Analysis Approach
        This describes the analysis approach.

        3. Results
        These are the results.

        4. Discussion
        This is the discussion section.

        5. Conclusion
        This is the conclusion.

        References
        [1] Author, A. (2023). Title. Journal.
        """
        
        chunks = ollama_service._chunk_research_paper(paper_text)
        
        # Check that we have the expected number of chunks
        assert len(chunks) >= 7, f"Expected at least 7 chunks, got {len(chunks)}"
        
        # Check that main sections and subsections are in chunks
        section_names = ["Abstract", "Introduction", "Methodology", "Data Collection", 
                         "Analysis Approach", "Results", "Discussion", "Conclusion"]
        for section in section_names:
            assert any(section in chunk for chunk in chunks), f"Section '{section}' not found in any chunk"
    
    def test_chunk_research_paper_large_section(self, ollama_service):
        """Test that the _chunk_research_paper method handles large sections by splitting them."""
        # Create a section that's larger than the max chunk size
        large_section = "Results\n" + "This is a result. " * 500  # Should be > 2000 chars
        
        chunks = ollama_service._chunk_research_paper(large_section, max_chunk_size=1000)
        
        # Check that the large section was split into multiple chunks
        assert len(chunks) > 1, "Large section should be split into multiple chunks"
        
        # Check that the first chunk contains the section heading
        assert "Results" in chunks[0], "First chunk should contain the section heading"
    
    def test_chunk_research_paper_fallback(self, ollama_service):
        """Test that the _chunk_research_paper method falls back to paragraph chunking when no sections are found."""
        # Text without clear section headers
        text_without_sections = "This is a paragraph.\n\n" * 10
        
        chunks = ollama_service._chunk_research_paper(text_without_sections)
        
        # Check that we still get chunks even without section headers
        assert len(chunks) > 0, "Should create chunks even without section headers"
