"""
Tests for the LLMFactory class.
"""

import pytest
from unittest.mock import MagicMock, patch
import logging

from llm_factory import LLMFactory
from models import InvalidLLMError, LLMException

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


class TestLLMFactory:
    """Tests for the LLMFactory class."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset the LLM cache before each test."""
        LLMFactory.reset_cache()
        yield
        # Also reset after each test
        LLMFactory.reset_cache()

    def test_valid_llms(self):
        """Test that all expected LLMs are in VALID_LLMS."""
        assert "claude" in LLMFactory.VALID_LLMS
        assert "chatgpt" in LLMFactory.VALID_LLMS
        assert "gemini" in LLMFactory.VALID_LLMS

    @patch("llms.Claude")
    def test_get_llm_claude(self, mock_claude):
        """Test getting a Claude instance."""
        mock_instance = MagicMock()
        mock_claude.return_value = mock_instance
        
        llm = LLMFactory.get_llm("claude")
        assert llm == mock_instance
        mock_claude.assert_called_once()

    @patch("llms.ChatGPT")
    def test_get_llm_chatgpt(self, mock_chatgpt):
        """Test getting a ChatGPT instance."""
        mock_instance = MagicMock()
        mock_chatgpt.return_value = mock_instance
        
        llm = LLMFactory.get_llm("chatgpt")
        assert llm == mock_instance
        mock_chatgpt.assert_called_once()

    @patch("llms.Gemini")
    def test_get_llm_gemini(self, mock_gemini):
        """Test getting a Gemini instance."""
        mock_instance = MagicMock()
        mock_gemini.return_value = mock_instance
        
        llm = LLMFactory.get_llm("gemini")
        assert llm == mock_instance
        mock_gemini.assert_called_once()

    def test_get_invalid_llm(self):
        """Test that getting an invalid LLM raises an error."""
        with pytest.raises(InvalidLLMError):
            LLMFactory.get_llm("invalid_llm")

    @patch("llms.Claude")
    def test_llm_instance_is_cached(self, mock_claude):
        """Test that LLM instances are cached."""
        mock_instance = MagicMock()
        mock_claude.return_value = mock_instance
        
        # First call should create and cache the instance
        llm1 = LLMFactory.get_llm("claude")
        # Second call should return the cached instance without creating a new one
        llm2 = LLMFactory.get_llm("claude")
        
        assert llm1 == llm2
        assert llm1 is llm2  # Check that they're the same object
        mock_claude.assert_called_once()  # Should only be called once

    @patch("llms.Claude")
    @patch("llms.ChatGPT")
    def test_different_llms_are_not_mixed(self, mock_chatgpt, mock_claude):
        """Test that different LLM types are not mixed in the cache."""
        claude_instance = MagicMock(name="claude_instance")
        chatgpt_instance = MagicMock(name="chatgpt_instance")
        
        mock_claude.return_value = claude_instance
        mock_chatgpt.return_value = chatgpt_instance
        
        claude = LLMFactory.get_llm("claude")
        chatgpt = LLMFactory.get_llm("chatgpt")
        
        assert claude == claude_instance
        assert chatgpt == chatgpt_instance
        assert claude != chatgpt

    @patch("llms.Claude")
    def test_reset_cache_clears_instances(self, mock_claude):
        """Test that reset_cache clears the cached instances."""
        mock_instance1 = MagicMock(name="claude_instance1")
        mock_instance2 = MagicMock(name="claude_instance2")
        
        # First call
        mock_claude.return_value = mock_instance1
        llm1 = LLMFactory.get_llm("claude")
        assert llm1 == mock_instance1
        assert mock_claude.call_count == 1
        
        # Reset cache
        LLMFactory.reset_cache()
        
        # Second call should create a new instance
        mock_claude.return_value = mock_instance2
        llm2 = LLMFactory.get_llm("claude")
        assert llm2 == mock_instance2
        assert mock_claude.call_count == 2

    @patch("llms.Claude", side_effect=Exception("LLM initialization error"))
    def test_llm_initialization_error(self, mock_claude):
        """Test that errors during LLM initialization are handled properly."""
        with pytest.raises(LLMException) as excinfo:
            LLMFactory.get_llm("claude")
        
        assert "Error creating LLM instance for claude" in str(excinfo.value)
        assert "LLM initialization error" in str(excinfo.value)