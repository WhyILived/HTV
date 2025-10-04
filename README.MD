# MCP Server for Game Development

This project provides an MCP (Model Context Protocol) server with tools for game development, including character sprite generation and storyline creation.

## Windows Compatibility

This project has been updated for Windows compatibility. The main changes include:

- Using `sys.executable` instead of hardcoded "python" in subprocess calls
- Windows-compatible path handling throughout the codebase
- Proper environment variable loading

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the project root with the following content:

```env
# OpenAI API Key (required for the MCP client)
OPENAI_API_KEY=your_openai_api_key_here

# Gemini API Key (required for image generation)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the MCP Client

```bash
python mcp_client.py
```

## Available Tools

- **File Operations**: create_file, read_file, delete_file, append_file, list_directory
- **Character Generation**: generate_character_sprites (creates complete sprite sets with animations)
- **Story Generation**: generate_initial_storyline, generate_overview, generate_characters, generate_scenes, generate_skill_tree, generate_cutscenes

## Troubleshooting

If you encounter issues on Windows:

1. Make sure Python is in your PATH
2. Ensure all environment variables are set correctly
3. Check that the reference images exist in `schemas/excharacs/`
4. Verify that the output directory `mcp_output/` is writable

## Project Structure

```
HTV/
├── mcp_client.py              # Main MCP client
├── mcp_server/                # MCP server implementation
│   ├── main.py               # Server entry point
│   ├── nanobanana_check.py   # Image generation using Gemini
│   └── tools/
│       └── spritesheet_pipeline.py  # Character sprite generation
├── schemas/
│   └── excharacs/            # Reference images for character generation
└── requirements.txt          # Python dependencies
```