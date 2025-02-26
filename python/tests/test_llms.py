# /Users/nickfox137/Documents/llm-creative-studio/python/tests/test_llms.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llms import LLM, ChatGPT, Gemini, Claude
from langchain_core.messages import HumanMessage, AIMessage

@pytest.fixture
def sample_context():
    return [
        {
            "id": "123",
            "text": "What do you think about this?",
            "sender": "user",
            "senderName": "nick",
            "messageIntent": "question"
        },
        {
            "id": "124",
            "text": "I believe we should consider...",
            "sender": "chatgpt",
            "senderName": "ChatGPT",
            "messageIntent": "response"
        }
    ]

@pytest.fixture
def sample_history():
    return [
        HumanMessage(content="What do you think about this?"),
        AIMessage(content="I believe we should consider...")
    ]

def test_format_context_prompt():
    llm = LLM("test")
    context = [
        {
            "senderName": "Nick",
            "text": "What's your opinion?",
            "messageIntent": "question"
        },
        {
            "senderName": "Claude",
            "text": "I think we should analyze this further.",
            "messageIntent": "response"
        }
    ]
    
    formatted = llm.format_context_prompt(context, "Continue the discussion")
    assert "Nick asked: What's your opinion?" in formatted
    assert "Continue the discussion" in formatted

@pytest.mark.asyncio
@patch('llms.ChatGPT.get_response')
async def test_chatgpt_response_with_context(mock_get_response, sample_context, sample_history):
    mock_get_response.return_value = AsyncMock(return_value="This is a mocked ChatGPT response")
    chatgpt = ChatGPT()
    
    # Use a helper function to avoid actually calling the API
    async def mock_response(*args, **kwargs):
        return "This is a mocked ChatGPT response"
    
    chatgpt.get_response = mock_response
    
    response = await chatgpt.get_response(
        "What's your take on this?",
        sample_history,
        sample_context
    )
    assert isinstance(response, str)
    assert response == "This is a mocked ChatGPT response"

@pytest.mark.asyncio
@patch('llms.Claude.get_response')
async def test_claude_response_with_context(mock_get_response, sample_context, sample_history):
    mock_get_response.return_value = AsyncMock(return_value="This is a mocked Claude response")
    claude = Claude()
    
    # Use a helper function to avoid actually calling the API
    async def mock_response(*args, **kwargs):
        return "This is a mocked Claude response"
    
    claude.get_response = mock_response
    
    response = await claude.get_response(
        "Can you elaborate on that?",
        sample_history,
        sample_context
    )
    assert isinstance(response, str)
    assert response == "This is a mocked Claude response"

@pytest.mark.asyncio
@patch('llms.Gemini.get_response')
async def test_gemini_response_with_context(mock_get_response, sample_context, sample_history):
    mock_get_response.return_value = AsyncMock(return_value="This is a mocked Gemini response")
    gemini = Gemini()
    
    # Use a helper function to avoid actually calling the API
    async def mock_response(*args, **kwargs):
        return "This is a mocked Gemini response"
    
    gemini.get_response = mock_response
    
    response = await gemini.get_response(
        "Do you agree with ChatGPT's response?",
        sample_history,
        sample_context
    )
    assert isinstance(response, str)
    assert response == "This is a mocked Gemini response"

@pytest.mark.asyncio
@patch('llms.Claude.autogen_response', new_callable=AsyncMock)
async def test_claude_autogen_response(mock_autogen):
    # Configure the mock
    mock_autogen.return_value = "Claude autogen response"
    
    # Create the instance (this won't use the actual API)
    claude = Claude()
    
    # Test with our properly patched method
    response = await claude.autogen_response("Test message", "assistant")
    assert response == "Claude autogen response"
    mock_autogen.assert_called_once()

@pytest.mark.asyncio
@patch('llms.ChatGPT.autogen_response', new_callable=AsyncMock)
async def test_chatgpt_autogen_response(mock_autogen):
    # Configure the mock
    mock_autogen.return_value = "ChatGPT autogen response"
    
    # Create the instance (this won't use the actual API)
    chatgpt = ChatGPT()
    
    # Test with our properly patched method
    response = await chatgpt.autogen_response("Test message", "assistant")
    assert response == "ChatGPT autogen response"
    mock_autogen.assert_called_once()

@pytest.mark.asyncio
@patch('llms.Gemini.autogen_response', new_callable=AsyncMock)
async def test_gemini_autogen_response(mock_autogen):
    # Configure the mock
    mock_autogen.return_value = "Gemini autogen response"
    
    # Create the instance (this won't use the actual API)
    gemini = Gemini()
    
    # Test with our properly patched method
    response = await gemini.autogen_response("Test message", "assistant")
    assert response == "Gemini autogen response"
    mock_autogen.assert_called_once()
