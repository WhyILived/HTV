#!/usr/bin/env python3
"""
Simple test script for storyline pipeline - no MCP, just direct function calls.
"""

import asyncio
import sys
from pathlib import Path

# Add the mcp_server directory to the path
sys.path.append(str(Path(__file__).parent / "mcp_server"))

from tools.storyline_pipeline import build_storyline_pipeline

async def main():
    print("Testing storyline pipeline directly...")
    
    prompt = "Aladdin the movie"
    
    try:
        print(f"Generating storyline for: {prompt}")
        result = await build_storyline_pipeline(prompt)
        print("Storyline generation completed!")
        print(f"Result: {result}")
        
        # Check if storyline.json was created
        if Path("storyline.json").exists():
            print("storyline.json file created successfully!")
            with open("storyline.json", "r", encoding="utf-8") as f:
                content = f.read()
                print(f"File size: {len(content)} characters")
        else:
            print("storyline.json file was NOT created")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
