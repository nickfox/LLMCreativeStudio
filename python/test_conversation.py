# /Users/nickfox137/Documents/llm-creative-studio/python/test_conversation.py

import asyncio
import logging
from conversation_manager import ConversationManager

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_conversation():
    """
    Test the ConversationManager with a simple conversation.
    """
    # Create a conversation manager
    manager = ConversationManager(session_id="test_session")
    
    # Test a simple message
    print("\n=== Testing simple message ===")
    responses = await manager.process_message("Hello, can you introduce yourselves?", "user")
    for response in responses:
        print(f"{response['llm'].capitalize()}: {response['response'][:100]}...")
    
    # Test a directed message
    print("\n=== Testing directed message ===")
    responses = await manager.process_message("What's your opinion on AI safety?", "user", target_llm="claude")
    for response in responses:
        print(f"{response['llm'].capitalize()}: {response['response'][:100]}...")
    
    # Test a role assignment
    print("\n=== Testing role assignment ===")
    responses = await manager.process_message("/role claude debater", "user")
    for response in responses:
        print(f"{response['llm'].capitalize()}: {response['response']}")
    
    # Test a debate command
    print("\n=== Testing debate mode ===")
    responses = await manager.process_message("/debate 2 The future of AI", "user")
    for response in responses:
        # Handle different response formats (debate responses might have 'sender' instead of 'llm')
        if 'llm' in response:
            print(f"{response['llm'].capitalize()}: {response['response']}")
        elif 'sender' in response:
            sender = response['sender']
            content = response.get('content', response.get('response', 'No content'))
            print(f"{sender.capitalize()}: {content}")
        else:
            print(f"Unknown format: {response}")
    
    # Test message in debate mode
    print("\n=== Testing message in debate mode ===")
    responses = await manager.process_message("What are the main considerations for AI governance?", "user")
    for response in responses:
        # Handle different response formats
        if 'llm' in response:
            print(f"{response['llm'].capitalize()}: {response['response'][:100]}...")
        elif 'sender' in response:
            sender = response['sender']
            content = response.get('content', response.get('response', 'No content'))[:100]
            print(f"{sender.capitalize()}: {content}...")
        else:
            print(f"Unknown format: {response}")
    
    # Test help command
    print("\n=== Testing help command ===")
    responses = await manager.process_message("/help", "user")
    for response in responses:
        # Handle different response formats
        if 'llm' in response:
            print(f"{response['llm'].capitalize()}: {response['response'][:200]}...")
        elif 'sender' in response:
            sender = response['sender']
            content = response.get('content', response.get('response', 'No content'))[:200]
            print(f"{sender.capitalize()}: {content}...")
        else:
            print(f"Unknown format: {response}")

if __name__ == "__main__":
    asyncio.run(test_conversation())
