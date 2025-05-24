#!/usr/bin/env python3
"""
Startup script for the MCP Business Server Chat System

This script helps you get everything running properly.
"""

import subprocess
import sys
import os
import time
import asyncio
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required keys"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("Please create a .env file with your OPEN_ROUTER_KEY:")
        print("OPEN_ROUTER_KEY=your-api-key-here")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
        if "OPEN_ROUTER_KEY" not in content:
            print("❌ OPEN_ROUTER_KEY not found in .env file!")
            return False
    
    print("✅ .env file is properly configured!")
    return True

def start_business_server():
    """Start the business server in background"""
    print("🚀 Starting business server...")
    try:
        # Start the business server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "business_server:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if it's still running
        if process.poll() is None:
            print("✅ Business server started successfully on http://localhost:8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Business server failed to start:")
            print(f"stdout: {stdout.decode()}")
            print(f"stderr: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ Failed to start business server: {e}")
        return None

def start_mcp_server():
    """Start the HTTP-based MCP server in background"""
    print("🚀 Starting MCP server...")
    try:
        # Start the MCP server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "mcp_server_http:app", 
            "--host", "0.0.0.0", 
            "--port", "3000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if it's still running
        if process.poll() is None:
            print("✅ MCP server started successfully on http://localhost:3000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ MCP server failed to start:")
            print(f"stdout: {stdout.decode()}")
            print(f"stderr: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        return None

async def start_chat():
    """Start the interactive chat"""
    print("🤖 Starting interactive chat...")
    try:
        from mcp_client import main
        await main()
    except Exception as e:
        print(f"❌ Failed to start chat: {e}")

def main():
    """Main startup function"""
    print("🚀 MCP Business Server Chat System Startup")
    print("=" * 50)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        return
    
    # Step 2: Check environment
    if not check_env_file():
        return
    
    # Step 3: Start business server
    business_process = start_business_server()
    if not business_process:
        return
    
    # Step 4: Start MCP server
    mcp_process = start_mcp_server()
    if not mcp_process:
        # Clean up business server if MCP server failed to start
        if business_process and business_process.poll() is None:
            business_process.terminate()
            business_process.wait()
        return
    
    try:
        # Step 5: Start chat
        print("\n🎉 All systems ready! Starting chat interface...")
        print("=" * 50)
        asyncio.run(start_chat())
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    finally:
        # Clean up both servers
        if business_process and business_process.poll() is None:
            print("🛑 Stopping business server...")
            business_process.terminate()
            business_process.wait()
            print("✅ Business server stopped")
        
        if mcp_process and mcp_process.poll() is None:
            print("🛑 Stopping MCP server...")
            mcp_process.terminate()
            mcp_process.wait()
            print("✅ MCP server stopped")

if __name__ == "__main__":
    main()
