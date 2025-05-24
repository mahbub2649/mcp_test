#!/usr/bin/env python3
"""
MCP Client that interacts with the MCP server and uses OpenRouter API for LLM interactions.

This client allows you to chat with an LLM that can use the business server tools
through the MCP server as a middleman.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Tool:
    """Represents a tool that can be called"""
    name: str
    description: str
    input_schema: Dict[str, Any]

@dataclass
class Message:
    """Represents a chat message"""
    role: str
    content: str

class MCPServerManager:
    """Manages communication with an external MCP server"""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 3000):
        self.server_host = server_host
        self.server_port = server_port
        self.client = None
        self.tools: List[Tool] = []
        
    async def connect_to_server(self):
        """Connect to an already running MCP server"""
        try:
            # Create HTTP client to connect to MCP server
            self.client = httpx.AsyncClient(timeout=30.0)
            
            # Test connection by checking if server is running
            await self._check_server_health()
            
            # Initialize and get tools
            await self._initialize_server()
            await self._get_tools()
            
            logger.info(f"Connected to MCP server at {self.server_host}:{self.server_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def _check_server_health(self):
        """Check if the MCP server is running and reachable"""
        try:
            # Try to ping the server
            response = await self.client.get(f"http://{self.server_host}:{self.server_port}/health")
            if response.status_code != 200:
                raise Exception(f"Server health check failed with status {response.status_code}")
        except httpx.ConnectError:            raise Exception(f"Cannot connect to MCP server at {self.server_host}:{self.server_port}. Make sure it's running.")
        except Exception as e:
            logger.warning(f"Health check failed, assuming server is running: {e}")
    
    async def _initialize_server(self):
        """Initialize connection with the MCP server"""
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "mcp-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self._send_request(init_request)
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await self._send_notification(initialized_notification)
        logger.info("MCP server initialization completed")
    
    async def _get_tools(self):
        """Get available tools from the MCP server"""
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = await self._send_request(tools_request)
        if response and "result" in response and "tools" in response["result"]:
            self.tools = [
                Tool(
                    name=tool["name"],
                    description=tool["description"],
                    input_schema=tool["inputSchema"]                )
                for tool in response["result"]["tools"]
            ]
            logger.info(f"Loaded {len(self.tools)} tools: {[t.name for t in self.tools]}")
        else:
            logger.warning("No tools found or failed to retrieve tools from MCP server")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server"""
        tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(tool_request)
        if response and "result" in response and "content" in response["result"]:
            # Extract text from the response
            content = response["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", str(content))
            return str(content)
        return "No response from tool"
    
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request to the MCP server via HTTP"""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            response = await self.client.post(
                f"http://{self.server_host}:{self.server_port}/mcp",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error communicating with MCP server: {e}")
            return None
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a JSON-RPC notification to the MCP server via HTTP"""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            await self.client.post(
                f"http://{self.server_host}:{self.server_port}/mcp",
                json=notification,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            logger.error(f"Error sending notification to MCP server: {e}")
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.client:
            await self.client.aclose()
            logger.info("Disconnected from MCP server")

class OpenRouterClient:
    """Client for OpenRouter API"""
    
    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.3-8b-instruct:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def chat_completion(self, messages: List[Message], tools: List[Tool] = None) -> str:
        """Send a chat completion request to OpenRouter"""
        
        # Prepare messages for API
        api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema
                    }
                }
                for tool in tools
            ]
            payload["tool_choice"] = "auto"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "MCP Business Server Client"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                message = choice["message"]
                
                # Check if the model wants to call a tool
                if "tool_calls" in message and message["tool_calls"]:
                    return message  # Return the full message with tool calls
                else:
                    return message["content"]
            
            return "No response from LLM"
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OpenRouter: {e.response.status_code} - {e.response.text}")
            return f"Error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return f"Error: {str(e)}"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class ChatBot:
    """Main chatbot that orchestrates MCP server and OpenRouter API"""
    
    def __init__(self):
        self.mcp_manager = MCPServerManager()
        self.openrouter_client = None
        self.conversation_history: List[Message] = []
        self.agent_id: Optional[str] = None
    
    async def initialize(self):
        """Initialize the chatbot"""
        # Get API key from environment        
        api_key = os.getenv("OPEN_ROUTER_KEY")
        if not api_key:
            raise ValueError("OPEN_ROUTER_KEY not found in environment variables")
        
        # Initialize OpenRouter client
        self.openrouter_client = OpenRouterClient(api_key, "meta-llama/llama-3.3-8b-instruct:free")
        
        # Connect to MCP server
        await self.mcp_manager.connect_to_server()
        
        # Register this client as an agent
        try:
            result = await self.mcp_manager.call_tool("register_agent", {
                "name": "ChatBot",
                "version": "1.0.0"
            })
            logger.info(f"Agent registration result: {result}")
            # Extract agent ID from result if available
            if "Agent ID:" in result:
                self.agent_id = result.split("Agent ID: ")[1].strip()
        except Exception as e:
            logger.warning(f"Could not register agent: {e}")
        
        # Add system message
        system_message = Message(
            role="system",
            content="""You are a helpful assistant that can interact with a business server through various tools. 
            You have access to the following tools:
            - register_agent: Register a new agent
            - report_status: Report agent status  
            - get_tasks: Get tasks for an agent
            - add_number: Add 1 to a number
            - get_joke: Get a random joke
            
            When a user asks for something that can be accomplished with these tools, use the appropriate tool.
            For example, if they ask for a joke, use the get_joke tool.
            If they ask to add 1 to a number, use the add_number tool.
            Be helpful and conversational in your responses."""
        )
        self.conversation_history.append(system_message)
    
    async def chat(self, user_input: str) -> str:
        """Process a chat message from the user"""
        # Add user message to conversation
        user_message = Message(role="user", content=user_input)
        self.conversation_history.append(user_message)
        
        try:
            # Get response from LLM with tools
            response = await self.openrouter_client.chat_completion(
                self.conversation_history,
                self.mcp_manager.tools
            )
            
            # Check if LLM wants to call a tool
            if isinstance(response, dict) and "tool_calls" in response:
                # Process tool calls
                tool_results = []
                for tool_call in response["tool_calls"]:
                    function = tool_call["function"]
                    tool_name = function["name"]
                    arguments = json.loads(function["arguments"])
                    
                    logger.info(f"Calling tool: {tool_name} with args: {arguments}")
                    
                    # Call the tool via MCP server
                    tool_result = await self.mcp_manager.call_tool(tool_name, arguments)
                    tool_results.append(f"Tool '{tool_name}' result: {tool_result}")
                
                # Add tool results to conversation and get final response
                tool_message = Message(
                    role="assistant", 
                    content=f"I used some tools to help you. {' '.join(tool_results)}"
                )
                self.conversation_history.append(tool_message)
                
                # Get a final response from the LLM incorporating the tool results
                final_response = await self.openrouter_client.chat_completion(
                    self.conversation_history + [
                        Message(role="user", content="Please provide a helpful response based on the tool results above.")
                    ]
                )
                
                assistant_message = Message(role="assistant", content=str(final_response))
                self.conversation_history.append(assistant_message)
                
                return str(final_response)
            else:
                # Regular text response
                assistant_message = Message(role="assistant", content=str(response))
                self.conversation_history.append(assistant_message)
                return str(response)
                
        except Exception as e:            
            error_msg = f"Error processing your request: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def cleanup(self):
        """Clean up resources"""
        if self.openrouter_client:
            await self.openrouter_client.close()
        await self.mcp_manager.disconnect()

async def main():
    """Main chat loop"""
    chatbot = ChatBot()
    
    try:
        print("🤖 Initializing chatbot...")
        await chatbot.initialize()
        print("✅ Chatbot ready! You can now chat with me.")
        print("💡 Try asking: 'tell me a joke' or 'add 1 to 42' or 'what tasks do I have?'")
        print("Type 'quit' to exit.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Thinking...")
                response = await chatbot.chat(user_input)
                print(f"Bot: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
