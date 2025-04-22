# /Users/nickfox137/Documents/llm-creative-studio/python/tests/test_enhanced_chunking.py
"""
Tests for the enhanced chunking functionality.
"""

import pytest
import os
import sys
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_chunking import chunk_research_paper, split_large_chunk, create_paragraph_chunks

class TestEnhancedChunking:
    """Test suite for enhanced chunking functions."""
    
    def test_chunk_research_paper_section_detection(self):
        """Test that the chunk_research_paper function correctly detects sections."""
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
        
        chunks = chunk_research_paper(paper_text)
        
        # Check that we have the expected number of chunks
        assert len(chunks) >= 5, f"Expected at least 5 chunks, got {len(chunks)}"
        
        # Check that each section is in its own chunk
        section_names = ["Abstract", "Introduction", "Methodology", "Results", "Discussion", "Conclusion"]
        for section in section_names:
            assert any(section in chunk["heading"] for chunk in chunks), f"Section '{section}' not found in any chunk heading"
    
    def test_chunk_research_paper_hierarchical(self):
        """Test that the chunk_research_paper function handles hierarchical sections."""
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
        
        chunks = chunk_research_paper(paper_text)
        
        # Check that we have the expected number of chunks
        assert len(chunks) >= 7, f"Expected at least 7 chunks, got {len(chunks)}"
        
        # Check that main sections and subsections are in chunks
        section_names = ["Abstract", "Introduction", "Methodology", "Data Collection", 
                         "Analysis Approach", "Results", "Discussion", "Conclusion"]
        
        # Check that we have different levels in our chunks
        levels = set(chunk["level"] for chunk in chunks)
        assert len(levels) > 1, "Expected multiple hierarchy levels in chunks"
    
    def test_split_large_chunk(self):
        """Test that the split_large_chunk function correctly splits large chunks."""
        # Create a large chunk
        large_chunk = {
            "heading": "Results",
            "content": "Results\n" + "This is a result. " * 500,  # Should be > 2000 chars
            "size": 2000 + 500,  # Approximate size
            "level": 0
        }
        
        # Split the chunk
        split_chunks = split_large_chunk(large_chunk, 1000)
        
        # Check that we got multiple chunks
        assert len(split_chunks) > 1, "Large chunk should be split into multiple chunks"
        
        # Check that the first chunk contains the original heading
        assert split_chunks[0]["heading"] == "Results", "First chunk should have the original heading"
        
        # Check that subsequent chunks have continuation headings
        assert "part" in split_chunks[1]["heading"], "Subsequent chunks should indicate they are continuations"
        
        # Check that all chunks are smaller than the max size
        assert all(chunk["size"] <= 1000 for chunk in split_chunks), "All chunks should be smaller than max_chunk_size"
    
    def test_create_paragraph_chunks(self):
        """Test that the create_paragraph_chunks function correctly creates chunks from paragraphs."""
        # Create a list of paragraphs
        paragraphs = ["Paragraph " + str(i) + ": " + "This is a sentence. " * 20 for i in range(10)]
        
        # Create chunks
        chunks = create_paragraph_chunks(paragraphs, 500)
        
        # Check that we got multiple chunks
        assert len(chunks) > 1, "Should create multiple chunks from paragraphs"
        
        # Check that all chunks are smaller than the max size
        assert all(chunk["size"] <= 500 for chunk in chunks), "All chunks should be smaller than max_chunk_size"
        
        # Check that chunks have sequential headings
        for i, chunk in enumerate(chunks):
            assert f"Chunk {i+1}" == chunk["heading"], f"Chunk {i} should have heading 'Chunk {i+1}'"