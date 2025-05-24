#!/usr/bin/env python3
"""
Test script for the HTTP-based MCP server
"""

import asyncio
import json
import httpx

async def test_mcp_server():
    """Test the HTTP MCP server endpoints"""
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        print("Testing MCP Server Connection...")
        
        # Test 1: Health check
        print("\n1. Testing health check...")
        response = await client.get("http://localhost:3000/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        
        # Test 2: Initialize
        print("\n2. Testing initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        response = await client.post("http://localhost:3000/mcp", json=init_request)
        print(f"Initialize: {response.status_code} - {response.json()}")
        
        # Test 3: List tools
        print("\n3. Testing tools list...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        response = await client.post("http://localhost:3000/mcp", json=tools_request)
        result = response.json()
        print(f"Tools list: {response.status_code}")
        if "result" in result and "tools" in result["result"]:
            tools = result["result"]["tools"]
            print(f"Available tools: {[tool['name'] for tool in tools]}")
        
        # Test 4: Call get_joke tool
        print("\n4. Testing get_joke tool...")
        joke_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_joke",
                "arguments": {}
            }
        }
        response = await client.post("http://localhost:3000/mcp", json=joke_request)
        result = response.json()
        print(f"Get joke: {response.status_code}")
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"][0]["text"]
            print(f"Joke result: {content}")
        
        # Test 5: Call add_number tool
        print("\n5. Testing add_number tool...")
        add_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "add_number",
                "arguments": {"number": 42}
            }
        }
        response = await client.post("http://localhost:3000/mcp", json=add_request)
        result = response.json()
        print(f"Add number: {response.status_code}")
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"][0]["text"]
            print(f"Add result: {content}")
        
        print("\n✅ All MCP server tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    print("MCP Server HTTP Test Suite")
    print("=" * 30)
    print("Make sure the servers are running:")
    print("1. Business server: uvicorn business_server:app --host 0.0.0.0 --port 8000")
    print("2. MCP server: uvicorn mcp_server_http:app --host 0.0.0.0 --port 3000")
    print()
    
    asyncio.run(test_mcp_server())
