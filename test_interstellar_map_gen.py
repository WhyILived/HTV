#!/usr/bin/env python3
"""
Interstellar-themed map generation test script.
Generates 8 different scenes from the movie Interstellar across various scene types.
"""

import asyncio
import sys
from pathlib import Path

# Add the mcp_server directory to the path
sys.path.append(str(Path(__file__).parent / "mcp_server"))

from tools.map import generate_background_from_prompt

async def main():
    print("Testing Interstellar-themed map generation...")
    
    # Interstellar scenes across different types
    interstellar_scenes = [
        {
            "prompt": "Cooper's farmhouse living room with rustic wooden furniture, a cozy fireplace, and family photos on the walls. The room should feel warm and lived-in with earth tones and natural lighting.",
            "scene_type": "room"
        },
        {
            "prompt": "The Endurance spacecraft control room with advanced holographic displays, multiple control panels, and futuristic technology. The room should have a sleek, high-tech appearance with blue and white lighting.",
            "scene_type": "futuristic_room"
        },
        {
            "prompt": "The cornfield outside Cooper's farmhouse with tall, golden corn stalks stretching to the horizon under a vast, open sky. The scene should capture the rural, agricultural landscape of Earth.",
            "scene_type": "nature"
        },
        {
            "prompt": "The NASA facility corridor with clean, modern architecture, bright fluorescent lighting, and multiple doors leading to different research laboratories. The hallway should feel institutional and scientific.",
            "scene_type": "halls"
        },
        {
            "prompt": "The space station docking bay with multiple spacecraft, maintenance equipment, and zero-gravity preparation areas. The scene should show the bustling activity of space operations without any characters.",
            "scene_type": "market"
        },
        {
            "prompt": "The black hole Gargantua's accretion disk with swirling, glowing matter and intense gravitational lensing effects. The scene should be a cosmic, otherworldly environment with deep space elements.",
            "scene_type": "misc"
        },
        {
            "prompt": "The water planet's surface with massive tidal waves, rocky shorelines, and an alien sky. The scene should show the extreme, hostile environment with dramatic weather and geological features.",
            "scene_type": "nature"
        },
        {
            "prompt": "The tesseract library with infinite bookshelves extending in all directions, creating a mind-bending, multidimensional space where time and space intersect. The scene should be surreal and impossible.",
            "scene_type": "misc"
        }
    ]
    
    for i, scene in enumerate(interstellar_scenes, 1):
        print(f"\n--- Interstellar Scene {i}: {scene['scene_type']} ---")
        print(f"Prompt: {scene['prompt']}")
        
        try:
            # Create a custom name for this scene
            custom_name = f"interstellar_{i}"
            
            result = await generate_background_from_prompt(
                scene['prompt'], 
                scene['scene_type'],
                custom_name
            )
            print(f"Result: {result.replace('SUCCESS:', 'SUCCESS:').replace('ERROR:', 'ERROR:')}")
            
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
    
    print("\nInterstellar map generation tests completed!")
    print(f"Total scenes generated: {len(interstellar_scenes)}")

if __name__ == "__main__":
    asyncio.run(main())
