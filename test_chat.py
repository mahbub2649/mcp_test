#!/usr/bin/env python3
"""
Simple test script to demonstrate the MCP client functionality
"""

import asyncio
import os
from mcp_client import ChatBot

async def test_chat():
    """Test the chatbot with some sample interactions"""
    
    # Check if .env file exists and has the API key
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please create it with your OPEN_ROUTER_KEY")
        return
    
    chatbot = ChatBot()
    
    try:
        print("🤖 Starting test chat session...")
        await chatbot.initialize()
        print("✅ Chatbot initialized successfully!\n")
        
        # Test interactions
        test_messages = [
            "Hello! Can you tell me a joke?",
            "Add 1 to the number 42",
            "What tasks are available for my agent?",
            "What's 5 + 1? Use the adder tool.",
        ]
        
        for message in test_messages:
            print(f"Test: {message}")
            response = await chatbot.chat(message)
            print(f"Bot: {response}\n")
            await asyncio.sleep(1)  # Small delay between requests
            
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(test_chat())
