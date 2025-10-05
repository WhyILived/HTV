#!/usr/bin/env python3

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our custom tools
from .tools.sprite_from_storyline_pipeline import generate_sprites_from_storyline
from .tools.storyline_pipeline import build_storyline_pipeline

# Create MCP server
server = Server("game-dev-tools")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="create_file",
            description="Create a new file with specified content",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file to create"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                },
                "required": ["filename", "content"]
            }
        ),
        Tool(
            name="read_file",
            description="Read the contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file to read"}
                },
                "required": ["filename"]
            }
        ),
        Tool(
            name="list_directory",
            description="List files and directories in a path",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to list", "default": "."}
                },
                "required": []
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file to delete"}
                },
                "required": ["filename"]
            }
        ),
        Tool(
            name="append_file",
            description="Append content to an existing file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file to append to"},
                    "content": {"type": "string", "description": "Content to append"}
                },
                "required": ["filename", "content"]
            }
        ),
        Tool(
            name="generate_initial_storyline",
            description="Generates an initial storyline for a game based on a given theme. If the user is referencing a specific movie, show, book, fairy tale or historical individual, and wants a accurate depiction of the story, then input a prompt that explicitly references the name of the movie, show, book, fairy tale or historical individual. IMPORTANT: This tool should only be called ONCE per request. Do not repeat this tool call. DO NOT read or interpret any results, simply run the tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the game"}
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="generate_sprites_from_storyline",
            description="Generate character sprites for all characters in a storyline. Use this when user asks to 'generate sprites from storyline', 'create character sprites', or 'make sprites for characters'. Automatically reads storyline.json and creates sprites for all characters found.",
            inputSchema={
                "type": "object",
                "properties": {
                    "storyline_file": {"type": "string", "description": "Path to the storyline JSON file", "default": "storyline.json"}
                },
                "required": []
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    import os
    
    if name == "create_file":
        filename = arguments.get("filename")
        content = arguments.get("content")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return [TextContent(type="text", text=f"File '{filename}' created successfully")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error creating file: {str(e)}")]
    
    elif name == "read_file":
        filename = arguments.get("filename")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return [TextContent(type="text", text=f"Content of '{filename}':\n{content}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading file: {str(e)}")]
    
    elif name == "list_directory":
        path = arguments.get("path", ".")
        try:
            items = os.listdir(path)
            items_str = "\n".join(f"📁 {item}" if os.path.isdir(os.path.join(path, item)) else f"📄 {item}" for item in sorted(items))
            return [TextContent(type="text", text=f"Contents of '{path}':\n{items_str}")]
        except UnicodeDecodeError as e:
            # Handle encoding issues by using safe encoding
            try:
                items = os.listdir(path)
                safe_items = []
                for item in items:
                    try:
                        # Try to encode/decode to check if it's safe
                        item.encode('utf-8').decode('utf-8')
                        safe_items.append(item)
                    except UnicodeError:
                        # Skip items with encoding issues
                        safe_items.append(f"[ENCODING_ERROR_{len(safe_items)}]")
                items_str = "\n".join(f"📁 {item}" if os.path.isdir(os.path.join(path, item)) else f"📄 {item}" for item in sorted(safe_items))
                return [TextContent(type="text", text=f"Contents of '{path}':\n{items_str}")]
            except Exception as e2:
                return [TextContent(type="text", text=f"Error listing directory (encoding issue): {str(e2)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing directory: {str(e)}")]
    
    elif name == "delete_file":
        filename = arguments.get("filename")
        try:
            os.remove(filename)
            return [TextContent(type="text", text=f"File '{filename}' deleted successfully")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error deleting file: {str(e)}")]
    
    elif name == "append_file":
        filename = arguments.get("filename")
        content = arguments.get("content")
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(content)
            return [TextContent(type="text", text=f"Content appended to '{filename}' successfully")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error appending to file: {str(e)}")]
    
    elif name == "generate_initial_storyline":
        try:
            prompt = arguments.get("prompt")
            result = await build_storyline_pipeline(prompt)
            # result now includes output_path
            output_path = result.get("output_path", "storyline.json") if isinstance(result, dict) else "storyline.json"
            return [TextContent(type="text", text=f"Initial storyline generated and saved to: {output_path}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error generating storyline: {str(e)}")]
    
    elif name == "generate_sprites_from_storyline":
        try:
            storyline_file = arguments.get("storyline_file", "storyline.json")
            # Just run the tool - don't return the results
            await generate_sprites_from_storyline(storyline_file)
            return [TextContent(type="text", text="✅ Sprite generation completed - check mcp_output/spritesheets/ for results")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating sprites: {str(e)}")]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the MCP server."""
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    else:
        print("Usage: python -m mcp_server.main stdio")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
