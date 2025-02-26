"""
LLM Factory Module

This module is responsible for creating and managing LLM instances.
It uses a factory pattern to create appropriate LLM instances based on the LLM name.
"""

import logging
from typing import Dict, Any, Optional

from models import LLMException, InvalidLLMError


class LLMFactory:
    """
    Factory class for creating LLM instances.
    
    This factory centralizes the creation of LLM objects and makes it easier
    to add new LLM implementations in the future.
    """
    
    # Valid LLM identifiers
    VALID_LLMS = {"claude", "chatgpt", "gemini"}
    
    # Cache of LLM instances for reuse
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def get_llm(cls, llm_name: str) -> Any:
        """
        Get or create an LLM instance by name.
        
        Args:
            llm_name (str): Name of the LLM to get or create
            
        Returns:
            Any: An instance of the requested LLM
            
        Raises:
            InvalidLLMError: If the LLM name is not valid
        """
        llm_name = llm_name.lower()
        
        # Validate LLM name
        if llm_name not in cls.VALID_LLMS:
            raise InvalidLLMError(f"Unknown LLM: {llm_name}. Available options: {', '.join(cls.VALID_LLMS)}")
        
        # Return cached instance if available
        if llm_name in cls._instances:
            return cls._instances[llm_name]
        
        # Create new instance based on LLM name
        try:
            if llm_name == "claude":
                from llms import Claude
                instance = Claude()
            elif llm_name == "chatgpt":
                from llms import ChatGPT
                instance = ChatGPT()
            elif llm_name == "gemini":
                from llms import Gemini
                instance = Gemini()
                
            # Cache and return instance
            cls._instances[llm_name] = instance
            return instance
            
        except Exception as e:
            error_msg = f"Error creating LLM instance for {llm_name}: {str(e)}"
            logging.exception(error_msg)
            raise LLMException(error_msg) from e

    @classmethod
    def reset_cache(cls) -> None:
        """Clear the cache of LLM instances."""
        cls._instances.clear()