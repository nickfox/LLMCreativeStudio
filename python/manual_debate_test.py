#!/usr/bin/env python3
# /Users/nickfox137/Documents/llm-creative-studio/python/manual_debate_test.py
"""
Simple manual test to verify the debate system functionality.
This script doesn't require pytest and can be run directly.
"""

import asyncio
import logging
from conversation_manager import ConversationManager
from debate_manager import DebateManager, DebateState

# Configure basic logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Create conversation manager
    cm = ConversationManager("test_session")
    
    # Mock the LLM response method with an async function
    async def mock_generate_llm_response(llm, message, include_history=False, use_thinking_mode=False):
        return f"Simulated response from {llm} for message: {message[:30]}..."
    
    cm.generate_llm_response = mock_generate_llm_response
    
    # Create debate manager
    debate_manager = DebateManager(cm)
    
    # Mock process_user_input for testing user participation
    async def mock_process_user_input(message):
        print(f"Received user input: {message}")
        debate_manager.user_inputs[debate_manager.state.value] = message
        debate_manager.waiting_for_user = False
        
        # Move to the next state based on current state
        if debate_manager.state == DebateState.ROUND_1_OPENING:
            debate_manager.state = DebateState.ROUND_2_QUESTIONING
        elif debate_manager.state == DebateState.ROUND_2_QUESTIONING:
            debate_manager.state = DebateState.ROUND_3_RESPONSES
        elif debate_manager.state == DebateState.ROUND_3_RESPONSES:
            debate_manager.state = DebateState.ROUND_4_CONSENSUS
        elif debate_manager.state == DebateState.ROUND_4_CONSENSUS:
            debate_manager.state = DebateState.FINAL_SYNTHESIS
        
        return [{"sender": "system", "content": f"Processed user input and moved to {debate_manager.state.name}"}]
    
    debate_manager.process_user_input = mock_process_user_input
    
    # Start debate
    topic = "The impact of AI on creative industries"
    print(f"Starting debate on topic: {topic}")
    
    responses = await debate_manager.start_debate(topic)
    print(f"Debate started. Initial state: {debate_manager.state.name}")
    print(f"Received {len(responses)} initial responses")
    
    # Simulate user input after Round 1
    debate_manager.waiting_for_user = True
    user_input = "This is my position on AI and creative industries."
    print(f"Sending user input: {user_input}")
    
    responses = await debate_manager.process_user_input(user_input)
    print(f"State after user input: {debate_manager.state.name}")
    print(f"Debate user inputs: {debate_manager.user_inputs}")
    
    print("Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
