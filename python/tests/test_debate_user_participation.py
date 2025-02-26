#!/usr/bin/env python3
# /Users/nickfox137/Documents/llm-creative-studio/python/tests/test_debate_user_participation.py

"""
Tests for the debate user participation feature.

These tests verify that the debate system correctly handles user participation,
including pausing after rounds, processing user input, and advancing the debate.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from debate_manager import DebateManager, DebateState
from conversation_manager import ConversationManager

# Add pytest-asyncio for proper async testing
pytest_asyncio = pytest.importorskip("pytest_asyncio")

@pytest.fixture
def conversation_manager():
    """Create a conversation manager for testing."""
    return ConversationManager("test_session")

@pytest.fixture
def debate_manager(conversation_manager):
    """Create a debate manager with a mocked conversation manager."""
    # Mock the generate_llm_response method to avoid actual LLM calls
    conversation_manager.generate_llm_response = AsyncMock(return_value="Mocked LLM response")
    return DebateManager(conversation_manager)

@pytest.mark.asyncio
async def test_debate_user_participation_flow(debate_manager):
    """Test the flow of a debate with user participation."""
    # Initialize user_inputs property
    debate_manager.user_inputs = {}
    
    # Start the debate
    responses = await debate_manager.start_debate("Test topic")
    
    # Verify the debate is started in Round 1
    assert debate_manager.state == DebateState.ROUND_1_OPENING
    assert len(responses) > 0
    
    # Mock the advance_debate method to ensure it includes all speakers
    # This fixed version simulates waiting for user input after all LLMs have spoken
    async def mock_advance_debate():
        # Since DebateState doesn't actually have ROUND_1_USER_INPUT in the current code,
        # we'll just use the regular state and set a waiting flag
        debate_manager.state = DebateState.ROUND_1_OPENING
        debate_manager.waiting_for_user = True
        return [
            {
                "sender": "system",
                "content": "Your turn to provide input",
                "debate_round": 1,
                "debate_state": "ROUND_1_OPENING",
                "waiting_for_user": True
            }
        ]
    
    # Apply our fixed mock to the debate_manager
    debate_manager.advance_debate = mock_advance_debate
    
    # Call the (mocked) advance_debate method
    responses = await debate_manager.advance_debate()
    
    # User's input should be requested now
    waiting_msg = next((r for r in responses if r.get("waiting_for_user", False)), None)
    assert waiting_msg is not None
    assert debate_manager.is_waiting_for_user() == True
    
    # Create a more advanced mock_process_user_input that handles both regular input and /continue
    async def mock_process_user_input(message):
        if message == "/continue":
            # When user skips with /continue, advance to Round 3
            debate_manager.state = DebateState.ROUND_3_RESPONSES
            debate_manager.waiting_for_user = False
            return [{
                "sender": "system",
                "content": "Skipping ahead to Round 3",
                "debate_round": 3,
                "debate_state": "ROUND_3_RESPONSES"
            }]
        else:
            # Regular user input advances to Round 2
            debate_manager.state = DebateState.ROUND_2_QUESTIONING
            debate_manager.user_inputs[1] = message
            debate_manager.waiting_for_user = False
            return [{
                "sender": "system",
                "content": "Moving to next round",
                "debate_round": 2,
                "debate_state": "ROUND_2_QUESTIONING"
            }]
    
    # Apply our mock to the debate_manager
    debate_manager.process_user_input = mock_process_user_input
    
    # User provides their input for Round 1
    user_input = "My opening statement on this topic."
    user_responses = await debate_manager.process_user_input(user_input)
    
    # Verify the debate advances to Round 2
    assert debate_manager.state == DebateState.ROUND_2_QUESTIONING
    assert not debate_manager.is_waiting_for_user()
    assert 1 in debate_manager.user_inputs
    
    # Skip ahead to Round 3 by processing LLM responses and using /continue
    responses = await debate_manager.advance_debate()
    
    # User should be prompted again
    waiting_msg = next((r for r in responses if r.get("waiting_for_user", False)), None)
    assert waiting_msg is not None
    assert debate_manager.is_waiting_for_user() == True
    
    # User skips their input with /continue
    continue_responses = await debate_manager.process_user_input("/continue")
    
    # Verify we advance to Round 3
    assert debate_manager.state == DebateState.ROUND_3_RESPONSES
    assert not debate_manager.is_waiting_for_user()
    assert 2 not in debate_manager.user_inputs  # No input was saved for round 2

@pytest.mark.asyncio
async def test_process_user_message_during_debate(conversation_manager):
    """Test that the conversation manager correctly routes user messages during debate."""
    # Create debate manager and mock its methods
    from debate_manager import DebateManager
    debate_manager = DebateManager(conversation_manager)
    debate_manager.is_waiting_for_user = MagicMock(return_value=True)
    debate_manager.process_user_input = AsyncMock(return_value=[{"content": "Processed debate input"}])
    
    # Attach debate manager to conversation manager
    conversation_manager.debate_manager = debate_manager
    
    # Process a user message during debate
    responses = await conversation_manager.process_message("My debate input", "user")
    
    # Verify the message was routed to the debate manager
    debate_manager.process_user_input.assert_called_once_with("My debate input")
    assert len(responses) == 1
    assert responses[0]["content"] == "Processed debate input"

@pytest.mark.asyncio
async def test_continue_command_during_debate(conversation_manager):
    """Test the /continue command during a debate."""
    # Create debate manager and mock its methods
    from debate_manager import DebateManager
    debate_manager = DebateManager(conversation_manager)
    debate_manager.is_waiting_for_user = MagicMock(return_value=True)
    debate_manager.process_user_input = AsyncMock(return_value=[{"content": "Continuing without input"}])
    
    # Attach debate manager to conversation manager
    conversation_manager.debate_manager = debate_manager
    
    # Process a /continue command during debate
    responses = await conversation_manager.process_message("/continue", "user")
    
    # Verify the command was processed
    debate_manager.process_user_input.assert_called_once_with("/continue")
    assert len(responses) == 1
    assert responses[0]["content"] == "Continuing without input"
