# /Users/nickfox137/Documents/llm-creative-studio/python/enhanced_chunking.py
"""
Enhanced chunking functions for research papers.
This module contains improved implementations of text chunking algorithms
specifically designed for research papers.
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def chunk_research_paper(text: str, max_chunk_size: int = 2000) -> List[Dict[str, Any]]:
    """
    Split a research paper into chunks based on section headings with hierarchical structure.
    
    Args:
        text: Text of the research paper
        max_chunk_size: Maximum size for a single chunk
        
    Returns:
        List[Dict[str, Any]]: List of chunks with metadata (heading, content, level, etc.)
    """
    # Common section heading patterns in research papers across different disciplines
    section_patterns = [
        # Common main sections (case-insensitive)
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
        r"^\s*\d+[\.\)]\s+[A-Za-z][\w\s]+",  # Numbered sections like "1. Introduction" or "1) Introduction"
        r"^\s*[A-Z]\.\s+[A-Za-z][\w\s]+",    # Lettered sections like "A. Methodology"
        r"^\s*[IVXLCDM]+\.\s+[A-Za-z][\w\s]+", # Roman numeral sections
        r"^\s*[A-Z][a-zA-Z\s]+$",           # Any capitalized heading on its own line (more flexible)
    ]

    # Subsection patterns
    subsection_patterns = [
        r"^\s*\d+\.\d+[\.\s\)]*[A-Za-z]",  # Standard decimal subsections: 1.1 Title
        r"^\s*\d+\.\d+\s+",                 # Subsections without text on same line: 1.1
        r"^\s*[A-Z]\.\d+\s+",                # Letter-based subsections: A.1
        r"^\s*\d+\s*\.\s*\d+\s+"             # Spaced subsections: 1 . 1
    ]

    # Function to split text by pattern and check chunk sizes
    def split_by_pattern(text, patterns, level=0, min_lines=3):
        logger.debug(f"Attempting to split text by patterns at level {level}")
        chunks = []
        lines = text.split('\n')
        current_chunk = []
        current_heading = "Introduction"  # Default for start if no heading detected
        
        for line in lines:
            is_heading = False
            for pattern in patterns:
                if re.match(pattern, line, re.IGNORECASE | re.MULTILINE):
                    # Save the previous chunk if it exists and has sufficient content
                    if current_chunk and len(current_chunk) >= min_lines:
                        chunks.append({
                            "heading": current_heading,
                            "content": '\n'.join(current_chunk),
                            "size": len('\n'.join(current_chunk)),
                            "level": level
                        })
                    # Update heading and start new chunk
                    current_heading = line.strip()
                    current_chunk = [line]
                    is_heading = True
                    break  # Only match one pattern per line
            
            if not is_heading:
                current_chunk.append(line)
        
        # Add the last chunk
        if current_chunk and len(current_chunk) >= min_lines:
            chunks.append({
                "heading": current_heading,
                "content": '\n'.join(current_chunk),
                "size": len('\n'.join(current_chunk)),
                "level": level
            })
        
        return chunks

    # Try to split by main sections first
    section_chunks = split_by_pattern(text, section_patterns, level=0)
    logger.debug(f"Detected {len(section_chunks)} main sections in the research paper")
    
    # Process each section to look for subsections
    processed_chunks = []
    
    for section in section_chunks:
        # If section is small enough, keep it as is
        if section["size"] <= max_chunk_size:
            processed_chunks.append(section)
            continue
            
        # Try to split large sections into subsections
        subsection_text = section["content"]
        subsections = split_by_pattern(subsection_text, subsection_patterns, level=1, min_lines=2)
        
        # If we found subsections, add them
        if len(subsections) > 1:  # More than just the section itself
            for subsection in subsections:
                if subsection["size"] <= max_chunk_size:
                    # Add parent section info to subsection heading
                    if not subsection["heading"].startswith(section["heading"]):
                        subsection["parent_section"] = section["heading"]
                    processed_chunks.append(subsection)
                else:
                    # Split large subsections by paragraphs
                    processed_chunks.extend(
                        split_large_chunk(subsection, max_chunk_size, parent=section["heading"])
                    )
        else:
            # No subsections found, split by paragraphs
            processed_chunks.extend(
                split_large_chunk(section, max_chunk_size)
            )
    
    # If no sections were found at all, fall back to paragraph chunking
    if not processed_chunks:
        logger.debug("No sections found, falling back to paragraph chunking")
        paragraphs = text.split('\n\n')
        processed_chunks = create_paragraph_chunks(paragraphs, max_chunk_size)
    
    logger.debug(f"Research paper chunking completed with {len(processed_chunks)} chunks")
    return processed_chunks

def split_large_chunk(chunk, max_chunk_size, parent=None):
    """Split a large chunk into smaller chunks based on paragraphs."""
    heading = chunk["heading"]
    content = chunk["content"]
    level = chunk["level"]
    paragraphs = content.split('\n\n')
    
    # If parent is provided, include it in the heading
    if parent and not heading.startswith(parent):
        full_heading = f"{parent} - {heading}"
    else:
        full_heading = heading
    
    result_chunks = []
    current_chunk = []
    current_size = 0
    chunk_index = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        # If this paragraph alone is too big, we need to split it by sentences
        if para_size > max_chunk_size:
            # First add any accumulated paragraphs
            if current_chunk:
                chunk_heading = full_heading if chunk_index == 0 else f"{full_heading} (part {chunk_index+1})"
                result_chunks.append({
                    "heading": chunk_heading,
                    "content": '\n\n'.join(current_chunk),
                    "size": current_size,
                    "level": level + 1
                })
                current_chunk = []
                current_size = 0
                chunk_index += 1
            
            # Split the paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+|(?<=[.!?])(?=[A-Z])', para)
            sentence_chunks = []
            current_sentences = []
            current_sentence_size = 0
            
            for sentence in sentences:
                if current_sentence_size + len(sentence) <= max_chunk_size or not current_sentences:
                    current_sentences.append(sentence)
                    current_sentence_size += len(sentence) + 1  # +1 for space
                else:
                    sentence_chunks.append(' '.join(current_sentences))
                    current_sentences = [sentence]
                    current_sentence_size = len(sentence)
            
            if current_sentences:
                sentence_chunks.append(' '.join(current_sentences))
            
            # Add each sentence chunk
            for i, sentence_chunk in enumerate(sentence_chunks):
                chunk_heading = f"{full_heading} (part {chunk_index+1})"
                result_chunks.append({
                    "heading": chunk_heading,
                    "content": sentence_chunk,
                    "size": len(sentence_chunk),
                    "level": level + 1
                })
                chunk_index += 1
        
        # If adding this paragraph would exceed the chunk size, start a new chunk
        elif current_size + para_size > max_chunk_size and current_chunk:
            chunk_heading = full_heading if chunk_index == 0 else f"{full_heading} (part {chunk_index+1})"
            result_chunks.append({
                "heading": chunk_heading,
                "content": '\n\n'.join(current_chunk),
                "size": current_size,
                "level": level + 1
            })
            current_chunk = [para]
            current_size = para_size
            chunk_index += 1
        
        # Otherwise add to the current chunk
        else:
            current_chunk.append(para)
            current_size += para_size + (2 if current_chunk else 0)  # +2 for paragraph separator
    
    # Add the last chunk if it has content
    if current_chunk:
        chunk_heading = full_heading if chunk_index == 0 else f"{full_heading} (part {chunk_index+1})"
        result_chunks.append({
            "heading": chunk_heading,
            "content": '\n\n'.join(current_chunk),
            "size": current_size,
            "level": level + 1
        })
    
    return result_chunks

def create_paragraph_chunks(paragraphs, max_chunk_size):
    """Create chunks from paragraphs when no sections are found."""
    chunks = []
    current_chunk = []
    current_size = 0
    chunk_index = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        # If this paragraph alone is too big, split it by sentences
        if para_size > max_chunk_size:
            # First add any accumulated paragraphs
            if current_chunk:
                chunks.append({
                    "heading": f"Chunk {chunk_index+1}",
                    "content": '\n\n'.join(current_chunk),
                    "size": current_size,
                    "level": 0
                })
                current_chunk = []
                current_size = 0
                chunk_index += 1
            
            # Split the paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+|(?<=[.!?])(?=[A-Z])', para)
            sentence_chunk = []
            sentence_size = 0
            
            for sentence in sentences:
                if sentence_size + len(sentence) + 1 <= max_chunk_size or not sentence_chunk:
                    sentence_chunk.append(sentence)
                    sentence_size += len(sentence) + 1
                else:
                    chunks.append({
                        "heading": f"Chunk {chunk_index+1}",
                        "content": ' '.join(sentence_chunk),
                        "size": sentence_size,
                        "level": 0
                    })
                    chunk_index += 1
                    sentence_chunk = [sentence]
                    sentence_size = len(sentence)
            
            if sentence_chunk:
                chunks.append({
                    "heading": f"Chunk {chunk_index+1}",
                    "content": ' '.join(sentence_chunk),
                    "size": sentence_size,
                    "level": 0
                })
                chunk_index += 1
        
        # If adding this paragraph would exceed the chunk size, start a new chunk
        elif current_size + para_size > max_chunk_size and current_chunk:
            chunks.append({
                "heading": f"Chunk {chunk_index+1}",
                "content": '\n\n'.join(current_chunk),
                "size": current_size,
                "level": 0
            })
            current_chunk = [para]
            current_size = para_size
            chunk_index += 1
        
        # Otherwise add to the current chunk
        else:
            current_chunk.append(para)
            current_size += para_size + (2 if current_chunk else 0)  # +2 for paragraph separator
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append({
            "heading": f"Chunk {chunk_index+1}",
            "content": '\n\n'.join(current_chunk),
            "size": current_size,
            "level": 0
        })
    
    return chunks