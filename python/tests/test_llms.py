# /Users/nickfox137/Documents/llm-creative-studio/python/tests/test_llms.py

import pytest
import asyncio
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
async def test_chatgpt_response_with_context(sample_context, sample_history):
    chatgpt = ChatGPT()
    response = await chatgpt.get_response(
        "What's your take on this?",
        sample_history,
        sample_context
    )
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_claude_response_with_context(sample_context, sample_history):
    claude = Claude()
    response = await claude.get_response(
        "Can you elaborate on that?",
        sample_history,
        sample_context
    )
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_gemini_response_with_context(sample_context, sample_history):
    gemini = Gemini()
    response = await gemini.get_response(
        "Do you agree with ChatGPT's response?",
        sample_history,
        sample_context
    )
    assert isinstance(response, str)
    assert len(response) > 0
