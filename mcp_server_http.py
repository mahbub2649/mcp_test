#!/usr/bin/env python3
"""
HTTP-based MCP Server that acts as a middleman between LLM and business_server.py

This server exposes the business server's functionality as MCP tools via HTTP endpoints
that can be used by LLMs through the Model Context Protocol.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()
client_sessions = {}

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

# Create FastAPI app for HTTP-based MCP server
app = FastAPI(title="MCP Business Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Available tools definition
TOOLS = [
    {
        "name": "register_agent",
        "description": "Register a new agent with the business server",
        "inputSchema": {
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
    },
    {
        "name": "report_status",
        "description": "Report agent status to the business server",
        "inputSchema": {
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
    },
    {
        "name": "get_tasks",
        "description": "Get tasks assigned to a specific agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "ID of the agent to get tasks for"
                }
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "add_number",
        "description": "Add 1 to a given number using the business server",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number": {
                    "type": "integer",
                    "description": "The number to add 1 to"
                }
            },
            "required": ["number"]
        }
    },
    {
        "name": "get_joke",
        "description": "Get a random joke from the business server",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    client_ip = request.client.host
    logger.info(f"Health check from client {client_ip}")
    return {"status": "healthy", "message": "MCP server is running"}

@app.post("/mcp")
async def handle_mcp_request(request_data: Dict[str, Any], request: Request):
    """Handle MCP JSON-RPC requests"""
    
    # Get client information
    client_ip = request.client.host
    client_id = f"{client_ip}:{request.client.port}"
    
    try:
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        # Log the incoming request
        logger.info(f"[CLIENT {client_id}] Received request: method='{method}', id={request_id}")
        
        if method == "initialize":
            # Track new client connection
            if client_id not in connected_clients:
                connected_clients.add(client_id)
                client_sessions[client_id] = {
                    "connected_at": datetime.now().isoformat(),
                    "requests_count": 0,
                    "tools_called": []
                }
                logger.info(f"🔗 NEW CLIENT CONNECTED: {client_id}")
                logger.info(f"📊 Total connected clients: {len(connected_clients)}")
            
            # Update client session
            client_sessions[client_id]["requests_count"] += 1
            
            # Get client info from params
            client_info = params.get("clientInfo", {})
            client_name = client_info.get("name", "unknown")
            client_version = client_info.get("version", "unknown")
            
            logger.info(f"[CLIENT {client_id}] Initializing - Name: {client_name}, Version: {client_version}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "business-server-mcp",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "notifications/initialized":
            # Initialization complete notification
            logger.info(f"[CLIENT {client_id}] ✅ Initialization completed successfully")
            return {"jsonrpc": "2.0"}
        
        elif method == "tools/list":
            logger.info(f"[CLIENT {client_id}] 🔧 Requesting tools list ({len(TOOLS)} tools available)")
            if client_id in client_sessions:
                client_sessions[client_id]["requests_count"] += 1
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": TOOLS
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Log detailed tool call information
            logger.info(f"[CLIENT {client_id}] 🛠️  TOOL CALL: '{tool_name}'")
            logger.info(f"[CLIENT {client_id}] 📝 Tool arguments: {json.dumps(arguments, indent=2)}")
            
            # Track tool usage
            if client_id in client_sessions:
                client_sessions[client_id]["requests_count"] += 1
                client_sessions[client_id]["tools_called"].append({
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Call the tool and measure execution time
            start_time = datetime.now()
            result = await call_tool(tool_name, arguments)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.info(f"[CLIENT {client_id}] ✅ Tool '{tool_name}' completed in {execution_time:.2f}s")
            logger.info(f"[CLIENT {client_id}] 📤 Tool result: {result[:200]}{'...' if len(result) > 200 else ''}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
        
        else:
            logger.warning(f"[CLIENT {client_id}] ❌ Unknown method: {method}")
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
    except Exception as e:
        logger.error(f"[CLIENT {client_id}] 💥 Error handling request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }

async def call_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Handle tool calls by routing them to the appropriate business server endpoints"""
    
    try:
        logger.info(f"🔄 Executing tool '{name}' with business server...")
        
        if name == "register_agent":
            result = await business_client.register_agent(
                name=arguments["name"],
                version=arguments["version"]
            )
            response = f"Agent registered successfully. Agent ID: {result.get('agent_id')}"
            logger.info(f"✅ Agent registration completed: {result.get('agent_id')}")
            return response
            
        elif name == "report_status":
            result = await business_client.report_status(
                agent_id=arguments["agent_id"],
                status=arguments["status"],
                cpu_usage=arguments.get("cpu_usage"),
                memory_usage=arguments.get("memory_usage")
            )
            response = f"Status reported successfully: {result.get('message')}"
            logger.info(f"✅ Status report completed for agent: {arguments['agent_id']}")
            return response
            
        elif name == "get_tasks":
            result = await business_client.get_tasks(agent_id=arguments["agent_id"])
            tasks_info = json.dumps(result.get("tasks", {}), indent=2)
            response = f"Tasks for agent {arguments['agent_id']}:\n{tasks_info}"
            logger.info(f"✅ Tasks retrieved for agent: {arguments['agent_id']}")
            return response
            
        elif name == "add_number":
            result = await business_client.add_number(number=arguments["number"])
            response = f"Result: {arguments['number']} + 1 = {result.get('result')}"
            logger.info(f"✅ Number addition completed: {arguments['number']} + 1 = {result.get('result')}")
            return response
            
        elif name == "get_joke":
            result = await business_client.get_joke()
            setup = result.get("setup", "")
            punchline = result.get("punchline", "")
            response = f"Here's a joke for you:\n\nSetup: {setup}\nPunchline: {punchline}"
            logger.info(f"✅ Joke retrieved successfully")
            return response
            
        else:
            logger.warning(f"❌ Unknown tool requested: {name}")
            return f"Unknown tool: {name}"
            
    except Exception as e:
        logger.error(f"💥 Error calling tool {name}: {e}")
        return f"Error executing {name}: {str(e)}"

@app.get("/stats")
async def get_server_stats():
    """Get server statistics including client information"""
    return {
        "server_status": "running",
        "connected_clients": len(connected_clients),
        "client_details": client_sessions,
        "total_tools": len(TOOLS),
        "uptime": "Server running"
    }

@app.get("/clients")
async def get_connected_clients():
    """Get list of connected clients and their activity"""
    return {
        "connected_clients": list(connected_clients),
        "client_sessions": client_sessions
    }

@app.on_event("startup")
async def startup_event():
    """Initialize server on startup"""
    logger.info("🚀 MCP HTTP Server starting up...")
    logger.info(f"📡 Server will listen on port 3000")
    logger.info(f"🔗 Business server URL: {BUSINESS_SERVER_URL}")
    logger.info(f"🛠️  Available tools: {[tool['name'] for tool in TOOLS]}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("🛑 MCP HTTP Server shutting down...")
    logger.info(f"📊 Final stats - Connected clients: {len(connected_clients)}")
    
    # Log client session summaries
    for client_id, session in client_sessions.items():
        tools_count = len(session.get("tools_called", []))
        requests_count = session.get("requests_count", 0)
        logger.info(f"[CLIENT {client_id}] Session summary - Requests: {requests_count}, Tools called: {tools_count}")
    
    await business_client.close()
    logger.info("✅ Cleanup completed")

if __name__ == "__main__":
    logger.info("🎯 Starting MCP HTTP Server...")
    logger.info("=" * 60)
    logger.info("🔧 Model Context Protocol HTTP Server")
    logger.info("🏢 Business Server Middleman")
    logger.info("📍 Listening on: http://0.0.0.0:3000")
    logger.info("🔗 Business Server: http://localhost:8000")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=3000)
