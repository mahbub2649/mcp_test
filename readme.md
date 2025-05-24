# MCP Business Server System

A comprehensive Model Context Protocol (MCP) implementation that creates a bridge between Large Language Models and business server functionality, enabling natural language interaction with business operations through AI agents.

## 🎯 General Purpose

This system allows LLMs to interact with business server functionality through a standardized protocol. It enables:

- **Natural Language Business Operations**: Chat with an AI that can perform real business tasks
- **Tool-Based AI Interactions**: LLMs can call business functions as tools during conversations
- **Scalable Architecture**: Separate services that can be deployed independently
- **Real-time Monitoring**: Comprehensive logging and client tracking
- **Extensible Design**: Easy to add new business functions and AI capabilities

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│ Chat Client │◄──►│ LLM API     │◄──►│ MCP Server  │◄──►│ Business    │
│             │    │ LLM API     │    │ (HTTP)      │    │ Server      │
│             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     Port: -            Cloud           Port: 3000         Port: 8000
```

### Components

1. **Business Server** (`business_server.py`) - FastAPI server providing core business functionality
2. **HTTP MCP Server** (`mcp_server_http.py`) - Protocol bridge between LLMs and business server
3. **Chat Client** (`mcp_client.py`) - Interactive chat interface with LLM API integration
4. **Startup Scripts** - Automated setup and configuration tools

## 🚀 Installation

### Prerequisites

- **Python 3.8+** installed on your system
- **LLM API Key** (configured in environment variables)
- **Internet connection** for LLM API calls

### Quick Setup

1. **Clone/Download the project files** to your local directory

2. **Create environment file:**
   Create a `.env` file in the project root:
   ```env
   OPEN_ROUTER_KEY=your-llm-api-key-here
   ```
   > Configure your LLM API key for AI functionality

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

That's it! The system is ready to run.

## 🎮 Usage

### Method 1: Automated Startup (Recommended)

**Single Command Launch:**
```powershell
python start_chat.py
```

This automatically:
- ✅ Installs any missing dependencies
- ✅ Starts the business server (port 8000)
- ✅ Starts the MCP server (port 3000)  
- ✅ Launches the interactive chat client
- ✅ Handles graceful shutdown

### Method 2: Manual Startup

**Terminal 1 - Business Server:**
```powershell
python business_server.py
```

**Terminal 2 - MCP Server:**
```powershell
python mcp_server_http.py
```

**Terminal 3 - Chat Client:**
```powershell
python mcp_client.py
```

### Interactive Chat Examples

Once running, try these natural language commands:

```
You: Tell me a joke
Bot: Here's a joke for you:
     Setup: Why don't scientists trust atoms?
     Punchline: Because they make up everything!

You: Add 1 to 42
Bot: Result: 42 + 1 = 43

You: Register a new agent called "DataBot" version "2.1"
Bot: Agent registered successfully. Agent ID: agent_12345

You: What tasks do I have for agent_12345?
Bot: Tasks for agent agent_12345:
     {
       "task_1": "Process daily reports",
       "task_2": "Update inventory"
     }
```

## 🛠️ Available Tools

The system provides these business tools that the AI can use:

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `register_agent` | Register a new agent in the system | "Register agent TestBot v1.0" |
| `report_status` | Report agent status and metrics | "Report status for agent_123 as active" |
| `get_tasks` | Retrieve tasks for a specific agent | "What tasks does agent_456 have?" |
| `add_number` | Mathematical operation (demo tool) | "Add 1 to 99" |
| `get_joke` | Fetch a random joke | "Tell me a joke" |

## 📊 Monitoring & Logging

### Server Monitoring

The MCP server provides detailed logging:

```
🔗 NEW CLIENT CONNECTED: 127.0.0.1:54321
[CLIENT 127.0.0.1:54321] 🛠️ TOOL CALL: 'get_joke'
[CLIENT 127.0.0.1:54321] ✅ Tool 'get_joke' completed in 0.25s
```

### Monitoring Endpoints

- **Health Check:** `GET http://localhost:3000/health`
- **Server Stats:** `GET http://localhost:3000/stats`
- **Client Info:** `GET http://localhost:3000/clients`

## 🧪 Testing

### Automated Tests

```powershell
# Test the chat system
python test_chat.py

# Test MCP HTTP server
python test_mcp_http.py

# Test original MCP server (stdio)
python test_mcp.py
```

### Manual Testing

1. **Business Server Direct:**
   ```powershell
   curl http://localhost:8000/joke
   ```

2. **MCP Server Health:**
   ```powershell
   curl http://localhost:3000/health
   ```

## 🔧 Configuration

### Environment Variables

Create `.env` file with:
```env
# Required
OPEN_ROUTER_KEY=your-api-key

# Optional
BUSINESS_SERVER_URL=http://localhost:8000
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
```

### Model Configuration

The system uses configurable LLM models through API integration.

To change the model, edit `mcp_client.py`:
```python
self.openrouter_client = OpenRouterClient(api_key, "your-preferred-model")
```



**🎉 Ready to Chat with AI-Powered Business Tools!**

Run `python start_chat.py` and start exploring natural language business operations.