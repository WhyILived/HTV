#!/usr/bin/env python3
"""
Simple test script for map generation pipeline.
"""

import asyncio
import sys
from pathlib import Path

# Add the mcp_server directory to the path
sys.path.append(str(Path(__file__).parent / "mcp_server"))

from tools.map import generate_background_from_prompt

async def main():
    print("Testing map generation pipeline...")
    
    # Test different scene types
    test_cases = [
        {
            "prompt": "A cozy tavern with wooden tables and a fireplace",
            "scene_type": "room"
        },
        {
            "prompt": "A mystical forest with ancient trees and glowing mushrooms",
            "scene_type": "nature"
        },
        {
            "prompt": "A grand palace corridor with marble floors and golden chandeliers",
            "scene_type": "halls"
        },
        {
            "prompt": "A bustling Arabian marketplace with colorful tents and merchants",
            "scene_type": "market"
        },
        {
            "prompt": "A magical laboratory with floating crystals and alchemical equipment",
            "scene_type": "misc"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['scene_type']} ---")
        print(f"Prompt: {test_case['prompt']}")
        
        try:
            result = await generate_background_from_prompt(
                test_case['prompt'], 
                test_case['scene_type']
            )
            print(f"Result: {result}")
            
            # Check if file was created
            output_dir = Path("mcp_output/maps")
            if output_dir.exists():
                files = list(output_dir.glob("*.png"))
                print(f"Generated files: {[f.name for f in files]}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    print("\nMap generation tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
