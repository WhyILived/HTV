#!/usr/bin/env python3

import asyncio
import json
import os
import subprocess
import sys
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class MCPOpenAIClient:
    def __init__(self, model="gpt-4o"):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model  # Configurable model
        self.mcp_tools = []
        self.process = None
        
    async def connect_to_mcp_server(self):
        """Connect to the MCP server and get available tools."""
        try:
            # Start MCP server process
            self.process = subprocess.Popen(
                ["python", "-m", "mcp_server.main", "stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Initialize the session
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "openai-mcp-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            self.process.stdin.write(json.dumps(init_request) + "\n")
            self.process.stdin.flush()
            
            init_response = self.process.stdout.readline()
            init_data = json.loads(init_response)
            
            # Send initialized notification
            initialized_msg = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            self.process.stdin.write(json.dumps(initialized_msg) + "\n")
            self.process.stdin.flush()
            
            # Get available tools
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            self.process.stdin.write(json.dumps(tools_request) + "\n")
            self.process.stdin.flush()
            
            tools_response = self.process.stdout.readline()
            tools_data = json.loads(tools_response)
            
            if "result" in tools_data:
                self.mcp_tools = tools_data["result"].get("tools", [])
                print(f"✅ Available MCP tools: {[tool['name'] for tool in self.mcp_tools]}")
                return True
            else:
                return False
                    
        except Exception as e:
            print(f"❌ Error connecting to MCP server: {e}")
            return False
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a specific MCP tool."""
        try:
            tool_call = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            self.process.stdin.write(json.dumps(tool_call) + "\n")
            self.process.stdin.flush()
            
            response = self.process.stdout.readline()
            response_data = json.loads(response)
            
            if "result" in response_data:
                return response_data["result"]
            else:
                print(f"❌ Tool call error: {response_data}")
                return None
                
        except Exception as e:
            print(f"❌ Error calling tool: {e}")
            return None
    
    def create_openai_tools_schema(self):
        """Convert MCP tools to OpenAI tools schema."""
        openai_tools = []
        
        for tool in self.mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    async def chat_with_tools(self, message: str):
        """Chat with OpenAI using MCP tools with conversation loop."""
        try:
            # Convert MCP tools to OpenAI format
            openai_tools = self.create_openai_tools_schema()
            
            # Initialize conversation
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant with access to game development tools. When the user asks for multiple actions, break them down into individual tool calls. After each tool call, continue with the next action until all requested tasks are complete."
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
            
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Create chat completion with tools
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto"
                )
                
                message_response = response.choices[0].message
                
                # Add the AI's response to conversation
                messages.append(message_response)
                
                # Handle tool calls
                if message_response.tool_calls:
                    print(f"🔄 Step {iteration}: Processing {len(message_response.tool_calls)} tool(s)")
                    
                    tool_results = []
                    for tool_call in message_response.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"⚙️ Executing {tool_name}...")
                        
                        # Call the MCP tool
                        result = await self.call_mcp_tool(tool_name, tool_args)
                        
                        if result:
                            tool_results.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "content": str(result)
                            })
                            print(f"✅ {tool_name} completed")
                    
                    # Add tool results to conversation
                    messages.extend(tool_results)
                    
                    # Continue the conversation to see if more tools are needed
                    continue
                else:
                    # No more tool calls, return the final response
                    return message_response.content
                    
            # If we hit max iterations, return what we have
            return "⚠️ Reached maximum iterations. Some tasks may not be complete."
                
        except Exception as e:
            return f"❌ Error in chat: {e}"
    
    def cleanup(self):
        """Clean up the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()

async def main():
    """Main interactive chat function."""
    # You can change the model here: "gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4o-mini", etc.
    client = MCPOpenAIClient(model="gpt-5")
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
        print("❌ Please set your OpenAI API key in the .env file")
        print("   Edit .env and replace 'your_openai_api_key_here' with your actual API key")
        return
    
    print("🚀 Starting Persistence MCP client...")
    print(f"🤖 Using model: {client.model}")
    print("📝 Type 'quit' to exit\n")
    
    # Initialize MCP server once
    connected = await client.connect_to_mcp_server()
    if not connected:
        print("❌ Failed to connect to MCP server")
        return
    
    print("✅ Ready! Starting operations...\n")
    
    try:
        while True:
            # Check if we're in an interactive terminal
            if not sys.stdin.isatty():
                print("❌ Interactive mode requires a terminal.")
                break
                
            message = input("💬 User: ").strip()
            
            if message.lower() == 'quit':
                print("👋 Goodbye! Shutting down MCP server...")
                break
            elif not message:
                continue
            
            print("⚙️ Chat: ", end="", flush=True)
            response = await client.chat_with_tools(message)
            print(response)
            print()  # Add spacing between messages
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Shutting down MCP server...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clean up
        client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
