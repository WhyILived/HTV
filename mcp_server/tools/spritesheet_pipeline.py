#!/usr/bin/env python3
"""
Simplified Spritesheet Pipeline Tool - Generates 4 character images: base, idle, walk1, walk2.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Literal, Dict, List, Optional
from dataclasses import dataclass

# Context is optional - will be None if not using FastMCP
try:
    from mcp.server.fastmcp.server import Context
except ImportError:
    Context = None
from ..nanobanana_check import generate


@dataclass
class CharacterConfig:
    """Configuration for character generation."""
    name: str
    character_type: Literal["male", "female", "robot"]
    custom_prompt: str = ""
    background_color: str = "#ea00ff"  # Fixed background color
    size: str = "16x16"


class SpritesheetPipeline:
    """Generates 4 character images: base, idle, walk1, walk2."""
    
    def __init__(self, config: CharacterConfig):
        self.config = config
        self.output_dir = Path("mcp_output/spritesheets")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Reference images based on character type
        self.ref_images = {
            "male": "example_male_1.png",
            "female": "example_female_1.png", 
            "robot": "example_robot_1.png"
        }
        
        # Prompts for each generation step
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompts for the 4 generation steps."""
        # Base character description from custom prompt
        base_description = self.config.custom_prompt if self.config.custom_prompt else f"a {self.config.character_type} character"
        
        return {
            # Base image - AI selects from example pictures
            "base": f"Create a pixelated {base_description} using the reference image as a style guide. "
                   f"Match the pixel art style, proportions, and visual characteristics of the reference image exactly. "
                   f"Keep the character design consistent with the reference but adapt it to your custom description. "
                   f"MAKE SURE ITS TURNING AN ALMOST 45 DEGREES SIMILAR TO TOP DOWN GAMES. DONT HAVE ANY WEAPONS OR ITEMS IN ITS HANDS"
                   f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}**. "
                   f"The character must be **centered**, well-proportioned, and rendered in a **high-detail {self.config.size} pixel art style**.",
            
            # Idle animation - slight breathing movement
            "idle": f"EDIT the base character image to create a subtle idle breathing animation. "
                   f"Make a bit of change - the character should down a bit to show breathing. "
                   f"Keep the same pose, clothing, and all other details exactly the same. "
                   f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}**. "
                   f"Ensure the character is centered and maintains the same proportions as the base image.",
            
            # Walk animation 1 - right leg forward, left leg back
            "walk1": f"EDIT the base character image to create a walking pose. "
                    f"POSTURE DETAILS: For the RIGHT SIDE of the picture, the leg should be FORWARD and the hand should be BACK. "
                    f"For the LEFT SIDE of the picture, the leg should be BENT and the hand should be FORWARD. "
                    f"Show a natural walking step with the right leg extended forward and left leg bent behind. "
                    f"Arms should swing naturally - right arm back, left arm forward. "
                    f"Body should be slightly leaned forward in a walking motion. "
                    f"Keep the same character design, colors, and style as the base image. "
                    f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}**. "
                    f"Ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            # Walk animation 2 - opposite of walk1 (left leg forward, right leg back)
            "walk2": f"EDIT the base character image to create the second walking pose - the OPPOSITE of walk1. "
                    f"POSTURE DETAILS: For the LEFT SIDE of the picture, the leg should be FORWARD and the hand should be BACK. "
                    f"For the RIGHT SIDE of the picture, the leg should be BENT and the hand should be FORWARD. "
                    f"Show a natural walking step with the left leg extended forward and right leg bent behind. "
                    f"Arms should swing naturally - left arm back, right arm forward. "
                    f"Body should be slightly leaned forward in a walking motion. "
                    f"Keep the same character design, colors, and style as the base image. "
                    f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}**. "
                    f"Ensure the character is centered and well-proportioned for a {self.config.size} pixel art style."
        }
    
    def _get_reference_path(self, ref_name: str) -> Path:
        """Get the path to a reference image."""
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / "schemas" / "excharacs" / ref_name
    
    def _generate_image_sync(self, prompt: str, output_name: str, reference_image: Optional[str] = None) -> bool:
        """Generate a single image with optional reference (synchronous)."""
        try:
            print(f"🖼️ Generating image: {output_name}")
            print(f"📝 Prompt length: {len(prompt)} characters")
            
            ref_path = None
            if reference_image:
                # Check if it's already a full path (contains / or \)
                if "/" in reference_image or "\\" in reference_image:
                    ref_path = Path(reference_image)
                else:
                    ref_path = self._get_reference_path(reference_image)
                
                if not ref_path.exists():
                    print(f"⚠️ Reference image not found: {ref_path}")
                    ref_path = None
                else:
                    print(f"📷 Using reference image: {ref_path}")
            
            # Generate the image with custom output name
            output_path = self.output_dir / f"{output_name}.png"
            print(f"💾 Output path: {output_path}")
            
            print("🚀 Calling generate function...")
            if ref_path:
                generate(prompt, str(ref_path), str(output_path))
            else:
                generate(prompt, None, str(output_path))
            
            print("✅ Generate function completed")
            
            # Check if the file was created successfully
            if output_path.exists():
                print(f"✅ Image saved successfully: {output_path}")
                return True
            else:
                print(f"❌ Image file not found after generation: {output_path}")
            return False
            
        except Exception as e:
            print(f"❌ Failed to generate {output_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _generate_image(self, prompt: str, output_name: str, reference_image: Optional[str] = None) -> bool:
        """Generate a single image with optional reference (async wrapper)."""
        return await asyncio.to_thread(self._generate_image_sync, prompt, output_name, reference_image)
    
    async def generate_character_set(self, ctx: Optional[Context] = None) -> Dict[str, str]:
        """Generate 4 character images: base, idle, walk1, walk2."""
        print("🎨 Starting simplified character generation pipeline...")
        if ctx:
            await ctx.info("🎨 Starting simplified character generation pipeline...")
        
        results = {}
        start_time = time.time()
        
        # Step 1: Generate base character using example reference
        print("Step 1: Generating base character from example reference...")
        if ctx:
            await ctx.info("Step 1: Generating base character from example reference...")
        
        ref_image = self.ref_images[self.config.character_type]
        print(f"Using reference image: {ref_image}")
        
        print("Starting base image generation...")
        success = await self._generate_image(
            self.prompts["base"],
            f"{self.config.name}_base",
            ref_image
        )
        
        if not success:
            print("❌ Failed to generate base character")
            if ctx:
                await ctx.error("Failed to generate base character")
            return {}
        
        print("✅ Base character generated successfully")
        results["base"] = f"{self.config.name}_base.png"
        
        # Use the generated base character as reference for all subsequent generations
        base_character_path = str(self.output_dir / f"{self.config.name}_base.png")
        print(f"Base character path: {base_character_path}")
        
        # Step 2: Generate idle, walk1, and walk2 animations concurrently
        print("Step 2: Generating idle, walk1, and walk2 animations concurrently...")
        if ctx:
            await ctx.info("Step 2: Generating idle, walk1, and walk2 animations concurrently...")
        
        print("Starting concurrent animation generation...")
        animation_tasks = [
            self._generate_image(
                self.prompts["idle"],
                f"{self.config.name}_idle",
                base_character_path
            ),
            self._generate_image(
                self.prompts["walk1"],
                f"{self.config.name}_walk1",
                base_character_path
            ),
            self._generate_image(
                self.prompts["walk2"],
                f"{self.config.name}_walk2",
                base_character_path
            )
        ]
        
        print("Waiting for all animations to complete...")
        animation_results = await asyncio.gather(*animation_tasks)
        animation_names = ["idle", "walk1", "walk2"]
        
        for i, success in enumerate(animation_results):
            if success:
                results[animation_names[i]] = f"{self.config.name}_{animation_names[i]}.png"
        
        # Generate metadata
        metadata = {
            "character": {
                "name": self.config.name,
                "character_type": self.config.character_type,
                "custom_prompt": self.config.custom_prompt,
                "background_color": self.config.background_color,
                "size": self.config.size
            },
            "sprites": results,
            "animations": {
                "idle_cycle": ["base", "idle"],
                "walk_cycle": ["base", "walk1", "walk2"]
            },
            "generated_at": time.time(),
            "total_sprites": len(results)
        }
        
        # Save metadata
        metadata_path = self.output_dir / f"{self.config.name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        total_time = time.time() - start_time
        
        if ctx:
            await ctx.info(f"✅ Character generation complete! Generated {len(results)} sprites in {total_time:.2f}s")
            await ctx.info(f"📁 Output directory: {self.output_dir}")
            await ctx.info(f"📄 Metadata saved: {metadata_path.name}")
        
        return results


async def generate_character_sprites(
    name: str,
    character_type: Literal["male", "female", "robot"],
    custom_prompt: str,
    ctx: Optional[Context] = None
) -> Dict[str, str]:
    """
    Generate 4 character images: base, idle, walk1, walk2.
    
    Args:
        name: Character name (used for file naming)
        character_type: Character type (male/female/robot) - determines reference image
        custom_prompt: Character description ONLY - describe appearance, clothing, accessories, etc. 
                      Do NOT mention spritesheets, animations, frames, or technical details.
                      Example: "a female elf mage with blue robes and staff" - REQUIRED
        ctx: MCP context for logging
    
    Returns:
        Dictionary mapping sprite names to filenames
    """
    config = CharacterConfig(
        name=name,
        character_type=character_type,
        custom_prompt=custom_prompt
    )
    
    pipeline = SpritesheetPipeline(config)
    return await pipeline.generate_character_set(ctx)