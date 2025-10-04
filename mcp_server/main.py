#!/usr/bin/env python3

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our custom tools
from .tools.spritesheet_pipeline import generate_character_sprites

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
        Tool(
            name="generate_overview",
            description="Generate a high-level game overview including title, genre, and summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the game"}
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="generate_characters",
            description="Generate a list of characters for the game, including roles and abilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the game"}
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="generate_scenes",
            description="Generate story scenes including settings, events, and narrative flow",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the game"}
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="generate_skill_tree",
            description="Generate a skill tree with branches, skills, and requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the game"}
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="generate_cutscenes",
            description="Generate cinematic cutscenes with dialogue and descriptions",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the game"}
                },
                "required": ["prompt"]
            }
        )
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
            storyline = f"Once upon a time in a world inspired by '{prompt}', an epic adventure began..."
            return [TextContent(type="text", text=f"📖 Initial Storyline:\n{storyline}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating storyline: {str(e)}")]
    
    elif name == "generate_overview":
        try:
            prompt = arguments.get("prompt")
            overview = {
                "title": f"{prompt} RPG Adventure",
                "genre": "Fantasy RPG",
                "summary": f"A role-playing game inspired by '{prompt}' with quests, battles, and magic."
            }
            return [TextContent(type="text", text=f"📘 Game Overview:\n{json.dumps(overview, indent=2)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating overview: {str(e)}")]
    
    elif name == "generate_characters":
        try:
            prompt = arguments.get("prompt")
            characters = [
                {"name": "Elsa", "role": "Protagonist", "abilities": ["Ice Shard", "Frozen Barrier"]},
                {"name": "Anna", "role": "Companion", "abilities": ["Inspiration", "Swordplay"]},
                {"name": "The Duke", "role": "Antagonist", "abilities": ["Schemes", "Soldiers"]}
            ]
            return [TextContent(type="text", text=f"🧑‍🤝‍🧑 Characters:\n{json.dumps(characters, indent=2)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating characters: {str(e)}")]
    
    elif name == "generate_scenes":
        try:
            prompt = arguments.get("prompt")
            scenes = [
                {
                    "id": 1,
                    "title": "Attack on Arendelle",
                    "setting": "Snowy kingdom under siege",
                    "events": ["Elsa defends the gates", "Anna rallies the people"]
                },
                {
                    "id": 2,
                    "title": "Journey into the Mountains",
                    "setting": "Frozen wilderness",
                    "events": ["Elsa encounters magical spirits", "A vision of the Ice Queen appears"]
                }
            ]
            return [TextContent(type="text", text=f"🎬 Scenes:\n{json.dumps(scenes, indent=2)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating scenes: {str(e)}")]
    
    elif name == "generate_skill_tree":
        try:
            prompt = arguments.get("prompt")
            skill_tree = [
                {
                    "branch": "Frost Magic",
                    "skills": [
                        {"name": "Ice Shard", "effect": "Launches an icy projectile"},
                        {"name": "Frozen Barrier", "effect": "Creates a defensive wall of ice"}
                    ]
                },
                {
                    "branch": "Leadership",
                    "skills": [
                        {"name": "Inspire Allies", "effect": "Boosts morale and attack power"},
                        {"name": "Royal Command", "effect": "Orders NPC allies to perform special actions"}
                    ]
                }
            ]
            return [TextContent(type="text", text=f"🌟 Skill Tree:\n{json.dumps(skill_tree, indent=2)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating skill tree: {str(e)}")]
    
    elif name == "generate_cutscenes":
        try:
            prompt = arguments.get("prompt")
            cutscenes = [
                {
                    "id": 1,
                    "title": "Elsa’s Vision",
                    "description": "Elsa sees an ancient Ice Queen warning her of destiny.",
                    "dialogue": [
                        {"speaker": "Ice Queen", "line": "Your powers are just the beginning..."},
                        {"speaker": "Elsa", "line": "What must I do?"}
                    ]
                }
            ]
            return [TextContent(type="text", text=f"🎥 Cutscenes:\n{json.dumps(cutscenes, indent=2)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generating cutscenes: {str(e)}")]
    
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
