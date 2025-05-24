#!/usr/bin/env python3
"""
Test script for the MCP server functionality
"""

import asyncio
import json
import sys
from mcp_server import BusinessServerMCP

async def test_business_server_connection():
    """Test connection to the business server"""
    client = BusinessServerMCP()
    
    try:
        print("Testing business server connection...")
        
        # Test 1: Register an agent
        print("\n1. Testing agent registration...")
        agent_result = await client.register_agent("TestAgent", "1.0.0")
        print(f"Agent registration result: {agent_result}")
        agent_id = agent_result.get("agent_id")
        
        if agent_id:
            # Test 2: Report status
            print("\n2. Testing status reporting...")
            status_result = await client.report_status(agent_id, "active", 25.5, 60.0)
            print(f"Status report result: {status_result}")
            
            # Test 3: Get tasks
            print("\n3. Testing task retrieval...")
            tasks_result = await client.get_tasks(agent_id)
            print(f"Tasks result: {json.dumps(tasks_result, indent=2)}")
        
        # Test 4: Add number
        print("\n4. Testing number addition...")
        add_result = await client.add_number(42)
        print(f"Add number result: {add_result}")
        
        # Test 5: Get joke
        print("\n5. Testing joke retrieval...")
        joke_result = await client.get_joke()
        print(f"Joke result: {json.dumps(joke_result, indent=2)}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    finally:
        await client.close()

if __name__ == "__main__":
    print("MCP Server Test Suite")
    print("===================")
    print("Make sure the business server is running on http://localhost:8000")
    print("Start it with: uvicorn business_server:app --host 0.0.0.0 --port 8000")
    print()
    
    asyncio.run(test_business_server_connection())
