#!/usr/bin/env python3
"""
MCP Server that acts as a middleman between LLM and business_server.py

This server exposes the business server's functionality as MCP tools that can be
used by LLMs through the Model Context Protocol.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    Resource,
    TextContent,
    Tool,
    EmbeddedResource,
)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Business server configuration
BUSINESS_SERVER_URL = "http://localhost:8000"

class BusinessServerMCP:
    def __init__(self, base_url: str = BUSINESS_SERVER_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def register_agent(self, name: str, version: str) -> Dict[str, Any]:
        """Register a new agent with the business server"""
        url = urljoin(self.base_url, "/register")
        data = {"name": name, "version": version}
        
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error registering agent: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error registering agent: {e}")
            raise

    async def report_status(self, agent_id: str, status: str, cpu_usage: Optional[float] = None, memory_usage: Optional[float] = None) -> Dict[str, Any]:
        """Report agent status to the business server"""
        url = urljoin(self.base_url, "/report_status")
        data = {
            "agent_id": agent_id,
            "status": status,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage
        }
        
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error reporting status: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error reporting status: {e}")
            raise

    async def get_tasks(self, agent_id: str) -> Dict[str, Any]:
        """Get tasks for a specific agent"""
        url = urljoin(self.base_url, "/tasks")
        params = {"agent_id": agent_id}
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error getting tasks: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting tasks: {e}")
            raise

    async def add_number(self, number: int) -> Dict[str, Any]:
        """Add 1 to a number using the business server"""
        url = urljoin(self.base_url, "/adder")
        data = {"number": number}
        
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error adding number: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error adding number: {e}")
            raise

    async def get_joke(self) -> Dict[str, Any]:
        """Get a random joke from the business server"""
        url = urljoin(self.base_url, "/joke")
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error getting joke: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting joke: {e}")
            raise

# Initialize the business server client
business_client = BusinessServerMCP()

# Create the MCP server
server = Server("business-server-mcp")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools that interact with the business server"""
    return [
        Tool(
            name="register_agent",
            description="Register a new agent with the business server",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the agent to register"
                    },
                    "version": {
                        "type": "string",
                        "description": "Version of the agent"
                    }
                },
                "required": ["name", "version"]
            }
        ),
        Tool(
            name="report_status",
            description="Report agent status to the business server",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "ID of the agent reporting status"
                    },
                    "status": {
                        "type": "string",
                        "description": "Current status of the agent"
                    },
                    "cpu_usage": {
                        "type": "number",
                        "description": "CPU usage percentage (optional)"
                    },
                    "memory_usage": {
                        "type": "number",
                        "description": "Memory usage percentage (optional)"
                    }
                },
                "required": ["agent_id", "status"]
            }
        ),
        Tool(
            name="get_tasks",
            description="Get tasks assigned to a specific agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "ID of the agent to get tasks for"
                    }
                },
                "required": ["agent_id"]
            }
        ),
        Tool(
            name="add_number",
            description="Add 1 to a given number using the business server",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {
                        "type": "integer",
                        "description": "The number to add 1 to"
                    }
                },
                "required": ["number"]
            }
        ),
        Tool(
            name="get_joke",
            description="Get a random joke from the business server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls by routing them to the appropriate business server endpoints"""
    
    try:
        if name == "register_agent":
            result = await business_client.register_agent(
                name=arguments["name"],
                version=arguments["version"]
            )
            return [TextContent(
                type="text",
                text=f"Agent registered successfully. Agent ID: {result.get('agent_id')}"
            )]
            
        elif name == "report_status":
            result = await business_client.report_status(
                agent_id=arguments["agent_id"],
                status=arguments["status"],
                cpu_usage=arguments.get("cpu_usage"),
                memory_usage=arguments.get("memory_usage")
            )
            return [TextContent(
                type="text",
                text=f"Status reported successfully: {result.get('message')}"
            )]
            
        elif name == "get_tasks":
            result = await business_client.get_tasks(agent_id=arguments["agent_id"])
            tasks_info = json.dumps(result.get("tasks", {}), indent=2)
            return [TextContent(
                type="text",
                text=f"Tasks for agent {arguments['agent_id']}:\n{tasks_info}"
            )]
            
        elif name == "add_number":
            result = await business_client.add_number(number=arguments["number"])
            return [TextContent(
                type="text",
                text=f"Result: {arguments['number']} + 1 = {result.get('result')}"
            )]
            
        elif name == "get_joke":
            result = await business_client.get_joke()
            setup = result.get("setup", "")
            punchline = result.get("punchline", "")
            return [TextContent(
                type="text",
                text=f"Here's a joke for you:\n\nSetup: {setup}\nPunchline: {punchline}"
            )]
            
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

async def main():
    """Main function to run the MCP server"""
    # Use stdio transport
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options()
        )

if __name__ == "__main__":
    # Ensure proper cleanup
    try:
        asyncio.run(main())
    finally:
        asyncio.run(business_client.close())