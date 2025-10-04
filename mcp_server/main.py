#!/usr/bin/env python3

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our custom tools
from .tools.spritesheet_pipeline import generate_character_sprites
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
            name="generate_character_sprites",
            description="Generate complete character sprite set with animations (front, back, left, right, walk, sprint)",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Character name (used for file naming)"},
                    "gender": {"type": "string", "enum": ["male", "female"], "description": "Character gender"},
                    "custom_prompt": {"type": "string", "description": "Custom description of the character ONLY - describe appearance, clothing, accessories, etc. Do NOT mention spritesheets, animations, or frames. Example: 'a female elf mage with blue robes and staff' - REQUIRED"}
                },
                "required": ["name", "gender", "custom_prompt"]
            }
        ),
        Tool(
            name="generate_initial_storyline",
            description="Generate an initial storyline for a game based on a given theme",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the game"}
                },
                "required": ["prompt"]
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
            with open(filename, 'w') as f:
                f.write(content)
            return [TextContent(type="text", text=f"✅ File '{filename}' created successfully")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creating file: {str(e)}")]
    
    elif name == "read_file":
        filename = arguments.get("filename")
        try:
            with open(filename, 'r') as f:
                content = f.read()
            return [TextContent(type="text", text=f"📄 Content of '{filename}':\n{content}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error reading file: {str(e)}")]
    
    elif name == "list_directory":
        path = arguments.get("path", ".")
        try:
            items = os.listdir(path)
            items_str = "\n".join(f"📁 {item}" if os.path.isdir(os.path.join(path, item)) else f"📄 {item}" for item in sorted(items))
            return [TextContent(type="text", text=f"📂 Contents of '{path}':\n{items_str}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error listing directory: {str(e)}")]
    
    elif name == "delete_file":
        filename = arguments.get("filename")
        try:
            os.remove(filename)
            return [TextContent(type="text", text=f"🗑️ File '{filename}' deleted successfully")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error deleting file: {str(e)}")]
    
    elif name == "append_file":
        filename = arguments.get("filename")
        content = arguments.get("content")
        try:
            with open(filename, 'a') as f:
                f.write(content)
            return [TextContent(type="text", text=f"➕ Content appended to '{filename}' successfully")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error appending to file: {str(e)}")]
    
    elif name == "generate_character_sprites":
        try:
            result = await generate_character_sprites(
                name=arguments.get("name"),
                gender=arguments.get("gender"),
                custom_prompt=arguments.get("custom_prompt")
            )
            sprite_list = "\n".join([f"  - {name}: {filename}" for name, filename in result.items()])
            return [TextContent(type="text", text=f"✅ Character sprites generated ({len(result)} sprites):\n{sprite_list}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating character sprites: {str(e)}")]
        
    elif name == "generate_initial_storyline":
        try:
            prompt = arguments.get("prompt")
            storyline = await build_storyline_pipeline(prompt)
            return [TextContent(type="text", text=f"📖 Initial Storyline:\n{storyline}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating storyline: {str(e)}")]
    
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
