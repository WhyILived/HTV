#!/usr/bin/env python3
"""
Spritesheet Pipeline Tool - Generates complete character sprite sets with animations.
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
    gender: Literal["male", "female"]
    custom_prompt: str = ""
    background_color: str = "#ea00ff"  # Fixed background color
    size: str = "16x16"


class SpritesheetPipeline:
    """Generates complete character sprite sets with animations."""
    
    def __init__(self, config: CharacterConfig):
        self.config = config
        self.output_dir = Path("mcp_output/spritesheets")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Reference images based on gender
        self.ref_images = {
            "male": ["mp1.png", "mp2.png"],
            "female": ["fp1.png", "fp2.png"]
        }
        
        # Prompts for each generation step
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load configurable prompts for each generation step."""
        # Base character description from custom prompt
        base_description = self.config.custom_prompt if self.config.custom_prompt else f"a {self.config.gender} character"
        
        return {
            # Stationary poses
            "front": f"Make a pixelated {base_description} facing forward. "
                    f"POSTURE: Standing upright with both feet together, arms at sides or slightly bent. "
                    f"Match the pixel art style and dimensions of the reference image exactly. "
                    f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                    f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "back": f"Use the **EXACT SAME** character from the reference image, keeping all body features, clothing, and accessories. "
                    f"POSTURE: Standing upright facing DIRECTLY AWAY from viewer, both feet together, arms at sides. "
                    f"Show the back of the head, shoulders, and back view of clothing. "
                    f"Ensure the character design, colors, and style are **identical** to the reference. "
                    f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}**. "
                    f"The character must be **centered**, well-proportioned, and rendered in a **high-detail {self.config.size} pixel art style**.",
            
            "right": f"Use the **EXACT SAME** character from the reference image, keeping all body features, clothing, and accessories. "
                    f"POSTURE: Standing upright facing DIRECTLY TO THE RIGHT (side profile), both feet together, arms at sides. "
                    f"Show the right side profile with one arm visible, head in profile. "
                    f"Ensure the character design, colors, and style are **identical** to the reference. "
                    f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}**. "
                    f"The character must be **centered**, well-proportioned, and rendered in a **high-detail {self.config.size} pixel art style**.",
            
            "left": f"Use the **EXACT SAME** character from the reference image, keeping all body features, clothing, and accessories. "
                   f"POSTURE: Standing upright facing DIRECTLY TO THE LEFT (side profile), both feet together, arms at sides. "
                   f"Show the left side profile with one arm visible, head in profile. "
                   f"Ensure the character design, colors, and style are **identical** to the reference. "
                   f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}**. "
                   f"The character must be **centered**, well-proportioned, and rendered in a **high-detail {self.config.size} pixel art style**.",
            
            # Walk1 animations (right leg forward)
            "front_walk1": f"Use the EXACT SAME character from the reference image. "
                          f"POSTURE: Walking pose with RIGHT LEG FORWARD, left leg back. "
                          f"Arms should swing naturally - right arm back, left arm forward. "
                          f"Body slightly leaned forward, head facing forward. "
                          f"This is frame 1 of a 3-frame walk cycle: stationary -> walk1 -> walk2 -> stationary. "
                          f"Show a light walking step, not sprinting. Keep the same character design, colors, and style. "
                          f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                          f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "back_walk1": f"Use the EXACT SAME character from the reference image. "
                         f"POSTURE: Walking pose with RIGHT LEG FORWARD, left leg back, facing away from viewer. "
                         f"Arms should swing naturally - right arm back, left arm forward. "
                         f"Body slightly leaned forward, back of head visible. "
                         f"This is frame 1 of a 3-frame walk cycle: stationary -> walk1 -> walk2 -> stationary. "
                         f"Show a light walking step, not sprinting. Keep the same character design, colors, and style. "
                         f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                         f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "right_walk1": f"Use the EXACT SAME character from the reference image. "
                          f"POSTURE: Walking pose with RIGHT LEG FORWARD, left leg back, facing right (side profile). "
                          f"Arms should swing naturally - right arm back, left arm forward. "
                          f"Body slightly leaned forward, head in right profile. "
                          f"This is frame 1 of a 3-frame walk cycle: stationary -> walk1 -> walk2 -> stationary. "
                          f"Show a light walking step, not sprinting. Keep the same character design, colors, and style. "
                          f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                          f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "left_walk1": f"Use the EXACT SAME character from the reference image. "
                         f"POSTURE: Walking pose with RIGHT LEG FORWARD, left leg back, facing left (side profile). "
                         f"Arms should swing naturally - right arm back, left arm forward. "
                         f"Body slightly leaned forward, head in left profile. "
                         f"This is frame 1 of a 3-frame walk cycle: stationary -> walk1 -> walk2 -> stationary. "
                         f"Show a light walking step, not sprinting. Keep the same character design, colors, and style. "
                         f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                         f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            # Walk2 animations (alternate limb forward)
            "front_walk2": f"EDIT the reference picture of the character to produce the NEXT FRAME by CHANGING WHICH LIMB LEADS. "
                          f"POSTURE: Keep the SAME camera view and overall pose, but SWAP which leg is forward. If the LEG ON THE RIGHT SIDE OF THE REFERENCE PICTURE is forward, make the LEG ON THE LEFT SIDE forward instead (and vice versa). "
                          f"Also SWAP the arm swing accordingly: if the ARM ON THE RIGHT SIDE OF THE REFERENCE PICTURE was back, make the ARM ON THE LEFT SIDE back instead (and vice versa). Do not mirror or rotate the character. Do not change proportions. "
                          f"Body slightly leaned forward, head facing forward. "
                          f"This is frame 2 of a 3-frame walk cycle: stationary -> walk1 -> walk2 -> stationary. "
                          f"Show a light walking step, not sprinting. Keep the same character design, colors, and style. "
                          f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                          f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "back_walk2": f"EDIT the reference picture to produce the NEXT FRAME by CHANGING WHICH LIMB LEADS. "
                         f"POSTURE: Keep the SAME camera view (back view) and overall pose, but SWAP which leg is forward. If the LEG ON THE RIGHT SIDE OF THE REFERENCE PICTURE is forward, make the LEG ON THE LEFT SIDE forward instead (and vice versa). "
                         f"Also SWAP the arm swing accordingly: if the ARM ON THE RIGHT SIDE OF THE REFERENCE PICTURE was back, make the ARM ON THE LEFT SIDE back instead (and vice versa). Do not mirror or rotate the character. Do not change proportions. "
                         f"Body slightly leaned forward, back of head visible. "
                         f"This is frame 2 of a 3-frame walk cycle: stationary -> walk1 -> walk2 -> stationary. "
                         f"Show a light walking step, not sprinting. Keep the same character design, colors, and style. "
                         f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                         f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "right_walk2": f"EDIT the reference picture to produce the NEXT FRAME by CHANGING WHICH LIMB LEADS. "
                          f"POSTURE: Keep the SAME side profile and overall pose, but SWAP which leg is forward. If the LEG ON THE RIGHT SIDE OF THE REFERENCE PICTURE is forward, make the LEG ON THE LEFT SIDE forward instead (and vice versa). "
                          f"Also SWAP the arm swing accordingly: if the ARM ON THE RIGHT SIDE OF THE REFERENCE PICTURE was back, make the ARM ON THE LEFT SIDE back instead (and vice versa). Do not mirror or rotate the character. Do not change proportions. "
                          f"Body slightly leaned forward, head in side profile. "
                          f"This is frame 2 of a 3-frame walk cycle: stationary -> walk1 -> walk2 -> stationary. "
                          f"Show a light walking step, not sprinting. Keep the same character design, colors, and style. "
                          f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                          f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "left_walk2": f"EDIT the reference picture to produce the NEXT FRAME by CHANGING WHICH LIMB LEADS. "
                         f"POSTURE: Keep the SAME side profile and overall pose, but SWAP which leg is forward. If the LEG ON THE RIGHT SIDE OF THE REFERENCE PICTURE is forward, make the LEG ON THE LEFT SIDE forward instead (and vice versa). "
                         f"Also SWAP the arm swing accordingly: if the ARM ON THE RIGHT SIDE OF THE REFERENCE PICTURE was back, make the ARM ON THE LEFT SIDE back instead (and vice versa). Do not mirror or rotate the character. Do not change proportions. "
                         f"Body slightly leaned forward, head in side profile. "
                         f"This is frame 2 of a 3-frame walk cycle: stationary -> walk1 -> walk2 -> stationary. "
                         f"Show a light walking step, not sprinting. Keep the same character design, colors, and style. "
                         f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                         f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            # Sprint1 animations (right leg forward, more dynamic)
            "front_sprint1": f"Use the EXACT SAME character from the reference image. "
                            f"POSTURE: Sprinting pose with RIGHT LEG FORWARD, left leg back, more dynamic than walking. "
                            f"Arms should swing more aggressively - right arm back, left arm forward. "
                            f"Body leaned forward more, head facing forward with determined expression. "
                            f"This is frame 1 of a 3-frame sprint cycle: stationary -> sprint1 -> sprint2 -> stationary. "
                            f"Show a fast sprinting step with more dynamic movement than walking. Keep the same character design, colors, and style. "
                            f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                            f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "back_sprint1": f"Use the EXACT SAME character from the reference image. "
                           f"POSTURE: Sprinting pose with RIGHT LEG FORWARD, left leg back, facing away from viewer, more dynamic than walking. "
                           f"Arms should swing more aggressively - right arm back, left arm forward. "
                           f"Body leaned forward more, back of head visible. "
                           f"This is frame 1 of a 3-frame sprint cycle: stationary -> sprint1 -> sprint2 -> stationary. "
                           f"Show a fast sprinting step with more dynamic movement than walking. Keep the same character design, colors, and style. "
                           f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                           f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "right_sprint1": f"Use the EXACT SAME character from the reference image. "
                            f"POSTURE: Sprinting pose with RIGHT LEG FORWARD, left leg back, facing right (side profile), more dynamic than walking. "
                            f"Arms should swing more aggressively - right arm back, left arm forward. "
                            f"Body leaned forward more, head in right profile. "
                            f"This is frame 1 of a 3-frame sprint cycle: stationary -> sprint1 -> sprint2 -> stationary. "
                            f"Show a fast sprinting step with more dynamic movement than walking. Keep the same character design, colors, and style. "
                            f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                            f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "left_sprint1": f"Use the EXACT SAME character from the reference image. "
                           f"POSTURE: Sprinting pose with RIGHT LEG FORWARD, left leg back, facing left (side profile), more dynamic than walking. "
                           f"Arms should swing more aggressively - right arm back, left arm forward. "
                           f"Body leaned forward more, head in left profile. "
                           f"This is frame 1 of a 3-frame sprint cycle: stationary -> sprint1 -> sprint2 -> stationary. "
                           f"Show a fast sprinting step with more dynamic movement than walking. Keep the same character design, colors, and style. "
                           f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                           f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            # Sprint2 animations (alternate limb forward, more dynamic)
            "front_sprint2": f"EDIT the reference picture of the sprint pose to produce the NEXT FRAME by CHANGING WHICH LIMB LEADS. "
                            f"POSTURE: Keep the SAME camera view and overall pose, but SWAP which leg is forward. If the LEG ON THE RIGHT SIDE OF THE REFERENCE PICTURE is forward, make the LEG ON THE LEFT SIDE forward instead (and vice versa). "
                            f"Also SWAP the arm swing accordingly: if the ARM ON THE RIGHT SIDE OF THE REFERENCE PICTURE was back, make the ARM ON THE LEFT SIDE back instead (and vice versa). Do not mirror or rotate the character. Do not change proportions. "
                            f"Body leaned forward more, head facing forward with determined expression. "
                            f"This is frame 2 of a 3-frame sprint cycle: stationary -> sprint1 -> sprint2 -> stationary. "
                            f"Show a fast sprinting step with more dynamic movement than walking. Keep the same character design, colors, and style. "
                            f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                            f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "back_sprint2": f"EDIT the reference picture of the sprint pose to produce the NEXT FRAME by CHANGING WHICH LIMB LEADS. "
                           f"POSTURE: Keep the SAME camera view (back view) and overall pose, but SWAP which leg is forward. If the LEG ON THE RIGHT SIDE OF THE REFERENCE PICTURE is forward, make the LEG ON THE LEFT SIDE forward instead (and vice versa). "
                           f"Also SWAP the arm swing accordingly: if the ARM ON THE RIGHT SIDE OF THE REFERENCE PICTURE was back, make the ARM ON THE LEFT SIDE back instead (and vice versa). Do not mirror or rotate the character. Do not change proportions. "
                           f"Body leaned forward more, back of head visible. "
                           f"This is frame 2 of a 3-frame sprint cycle: stationary -> sprint1 -> sprint2 -> stationary. "
                           f"Show a fast sprinting step with more dynamic movement than walking. Keep the same character design, colors, and style. "
                           f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                           f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "right_sprint2": f"EDIT the reference picture of the sprint pose to produce the NEXT FRAME by CHANGING WHICH LIMB LEADS. "
                            f"POSTURE: Keep the SAME side profile and overall pose, but SWAP which leg is forward. If the LEG ON THE RIGHT SIDE OF THE REFERENCE PICTURE is forward, make the LEG ON THE LEFT SIDE forward instead (and vice versa). "
                            f"Also SWAP the arm swing accordingly: if the ARM ON THE RIGHT SIDE OF THE REFERENCE PICTURE was back, make the ARM ON THE LEFT SIDE back instead (and vice versa). Do not mirror or rotate the character. Do not change proportions. "
                            f"Body leaned forward more, head in side profile. "
                            f"This is frame 2 of a 3-frame sprint cycle: stationary -> sprint1 -> sprint2 -> stationary. "
                            f"Show a fast sprinting step with more dynamic movement than walking. Keep the same character design, colors, and style. "
                            f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                            f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            "left_sprint2": f"EDIT the reference picture of the sprint pose to produce the NEXT FRAME by CHANGING WHICH LIMB LEADS. "
                           f"POSTURE: Keep the SAME side profile and overall pose, but SWAP which leg is forward. If the LEG ON THE RIGHT SIDE OF THE REFERENCE PICTURE is forward, make the LEG ON THE LEFT SIDE forward instead (and vice versa). "
                           f"Also SWAP the arm swing accordingly: if the ARM ON THE RIGHT SIDE OF THE REFERENCE PICTURE was back, make the ARM ON THE LEFT SIDE back instead (and vice versa). Do not mirror or rotate the character. Do not change proportions. "
                           f"Body leaned forward more, head in side profile. "
                           f"This is frame 2 of a 3-frame sprint cycle: stationary -> sprint1 -> sprint2 -> stationary. "
                           f"Show a fast sprinting step with more dynamic movement than walking. Keep the same character design, colors, and style. "
                           f"Keep the WHOLE BACKGROUND EXACTLY {self.config.background_color} color and "
                           f"ensure the character is centered and well-proportioned for a {self.config.size} pixel art style."
        }
    
    def _get_reference_path(self, ref_name: str) -> Path:
        """Get the path to a reference image - Windows compatible."""
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / "schemas" / "excharacs" / ref_name
    
    def _generate_image_sync(self, prompt: str, output_name: str, reference_image: Optional[str] = None) -> bool:
        """Generate a single image with optional reference (synchronous)."""
        try:
            ref_path = None
            if reference_image:
                # Windows compatible path checking
                if "/" in reference_image or "\\" in reference_image:
                    ref_path = Path(reference_image)
                else:
                    ref_path = self._get_reference_path(reference_image)
                
                if not ref_path.exists():
                    print(f"⚠️ Reference image not found: {ref_path}")
                    ref_path = None
            
            # Generate the image with custom output name
            output_path = self.output_dir / f"{output_name}.png"
            if ref_path:
                generate(prompt, str(ref_path), str(output_path))
            else:
                generate(prompt, None, str(output_path))
            
            # Check if the file was created successfully
            if output_path.exists():
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to generate {output_name}: {e}")
            return False
    
    async def _generate_image(self, prompt: str, output_name: str, reference_image: Optional[str] = None) -> bool:
        """Generate a single image with optional reference (async wrapper)."""
        return await asyncio.to_thread(self._generate_image_sync, prompt, output_name, reference_image)
    
    async def generate_character_set(self, ctx: Optional[Context] = None) -> Dict[str, str]:
        """Generate complete character sprite set with animations."""
        if ctx:
            await ctx.info("🎨 Starting character sprite generation pipeline...")
        
        results = {}
        start_time = time.time()
        
        # Step 1: Generate front-facing character
        if ctx:
            await ctx.info("Step 1: Generating front-facing character...")
        
        ref_images = self.ref_images[self.config.gender]
        front_ref = ref_images[0]  # Use first reference image
        
        success = await self._generate_image(
            self.prompts["front"],
            f"{self.config.name}_front",
            front_ref
        )
        
        if not success:
            if ctx:
                await ctx.error("Failed to generate front-facing character")
            return {}
        
        results["front"] = f"{self.config.name}_front.png"
        
        # Use the generated front character as reference for all subsequent generations
        front_character_path = str(self.output_dir / f"{self.config.name}_front.png")
        
        # Step 2: Generate directional views concurrently
        if ctx:
            await ctx.info("Step 2: Generating directional views (back, left, right)...")
        
        directional_tasks = [
            self._generate_image(
                self.prompts["back"],
                f"{self.config.name}_back",
                front_character_path
            ),
            self._generate_image(
                self.prompts["right"],
                f"{self.config.name}_right",
                front_character_path
            ),
            self._generate_image(
                self.prompts["left"],
                f"{self.config.name}_left",
                front_character_path
            )
        ]
        
        directional_results = await asyncio.gather(*directional_tasks)
        directions = ["back", "right", "left"]
        
        for i, success in enumerate(directional_results):
            if success:
                results[directions[i]] = f"{self.config.name}_{directions[i]}.png"
        
        # Step 3: Generate walk1 animations concurrently
        if ctx:
            await ctx.info("Step 3: Generating walk1 animations...")
        
        # Use the correct directional references for each walk animation
        walk1_tasks = [
            self._generate_image(
                self.prompts["front_walk1"],
                f"{self.config.name}_front_walk1",
                front_character_path
            ),
            self._generate_image(
                self.prompts["back_walk1"],
                f"{self.config.name}_back_walk1",
                str(self.output_dir / f"{self.config.name}_back.png")
            ),
            self._generate_image(
                self.prompts["right_walk1"],
                f"{self.config.name}_right_walk1",
                str(self.output_dir / f"{self.config.name}_right.png")
            ),
            self._generate_image(
                self.prompts["left_walk1"],
                f"{self.config.name}_left_walk1",
                str(self.output_dir / f"{self.config.name}_left.png")
            )
        ]
        
        walk1_results = await asyncio.gather(*walk1_tasks)
        walk1_directions = ["front", "back", "right", "left"]
        
        for i, success in enumerate(walk1_results):
            if success:
                results[f"{walk1_directions[i]}_walk1"] = f"{self.config.name}_{walk1_directions[i]}_walk1.png"
        
        # Step 4: Generate walk2 animations concurrently
        if ctx:
            await ctx.info("Step 4: Generating walk2 animations...")
        
        walk2_tasks = [
            self._generate_image(
                self.prompts["front_walk2"],
                f"{self.config.name}_front_walk2",
                str(self.output_dir / f"{self.config.name}_front_walk1.png")
            ),
            self._generate_image(
                self.prompts["back_walk2"],
                f"{self.config.name}_back_walk2",
                str(self.output_dir / f"{self.config.name}_back_walk1.png")
            ),
            self._generate_image(
                self.prompts["right_walk2"],
                f"{self.config.name}_right_walk2",
                str(self.output_dir / f"{self.config.name}_right_walk1.png")
            ),
            self._generate_image(
                self.prompts["left_walk2"],
                f"{self.config.name}_left_walk2",
                str(self.output_dir / f"{self.config.name}_left_walk1.png")
            )
        ]
        
        walk2_results = await asyncio.gather(*walk2_tasks)
        walk2_directions = ["front", "back", "right", "left"]
        
        for i, success in enumerate(walk2_results):
            if success:
                results[f"{walk2_directions[i]}_walk2"] = f"{self.config.name}_{walk2_directions[i]}_walk2.png"
        
        # Step 5: Generate sprint1 animations concurrently
        if ctx:
            await ctx.info("Step 5: Generating sprint1 animations...")
        
        sprint1_tasks = [
            self._generate_image(
                self.prompts["front_sprint1"],
                f"{self.config.name}_front_sprint1",
                front_character_path
            ),
            self._generate_image(
                self.prompts["back_sprint1"],
                f"{self.config.name}_back_sprint1",
                str(self.output_dir / f"{self.config.name}_back.png")
            ),
            self._generate_image(
                self.prompts["right_sprint1"],
                f"{self.config.name}_right_sprint1",
                str(self.output_dir / f"{self.config.name}_right.png")
            ),
            self._generate_image(
                self.prompts["left_sprint1"],
                f"{self.config.name}_left_sprint1",
                str(self.output_dir / f"{self.config.name}_left.png")
            )
        ]
        
        sprint1_results = await asyncio.gather(*sprint1_tasks)
        sprint1_directions = ["front", "back", "right", "left"]
        
        for i, success in enumerate(sprint1_results):
            if success:
                results[f"{sprint1_directions[i]}_sprint1"] = f"{self.config.name}_{sprint1_directions[i]}_sprint1.png"
        
        # Step 6: Generate sprint2 animations concurrently
        if ctx:
            await ctx.info("Step 6: Generating sprint2 animations...")
        
        sprint2_tasks = [
            self._generate_image(
                self.prompts["front_sprint2"],
                f"{self.config.name}_front_sprint2",
                str(self.output_dir / f"{self.config.name}_front_sprint1.png")
            ),
            self._generate_image(
                self.prompts["back_sprint2"],
                f"{self.config.name}_back_sprint2",
                str(self.output_dir / f"{self.config.name}_back_sprint1.png")
            ),
            self._generate_image(
                self.prompts["right_sprint2"],
                f"{self.config.name}_right_sprint2",
                str(self.output_dir / f"{self.config.name}_right_sprint1.png")
            ),
            self._generate_image(
                self.prompts["left_sprint2"],
                f"{self.config.name}_left_sprint2",
                str(self.output_dir / f"{self.config.name}_left_sprint1.png")
            )
        ]
        
        sprint2_results = await asyncio.gather(*sprint2_tasks)
        sprint2_directions = ["front", "back", "right", "left"]
        
        for i, success in enumerate(sprint2_results):
            if success:
                results[f"{sprint2_directions[i]}_sprint2"] = f"{self.config.name}_{sprint2_directions[i]}_sprint2.png"
        
        # Generate metadata
        metadata = {
            "character": {
                "name": self.config.name,
                "gender": self.config.gender,
                "custom_prompt": self.config.custom_prompt,
                "background_color": self.config.background_color,
                "size": self.config.size
            },
            "sprites": results,
            "animations": {
                "walk_cycle": ["front", "front_walk1", "front_walk2"],
                "sprint_cycle": ["front", "front_sprint1", "front_sprint2"]
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
    gender: Literal["male", "female"],
    custom_prompt: str,
    ctx: Optional[Context] = None
) -> Dict[str, str]:
    """
    Generate complete character sprite set with animations.
    
    Args:
        name: Character name (used for file naming)
        gender: Character gender (male/female) - determines reference images
        custom_prompt: Character description ONLY - describe appearance, clothing, accessories, etc. 
                      Do NOT mention spritesheets, animations, frames, or technical details.
                      Example: "a female elf mage with blue robes and staff" - REQUIRED
        ctx: MCP context for logging
    
    Returns:
        Dictionary mapping sprite names to filenames
    """
    config = CharacterConfig(
        name=name,
        gender=gender,
        custom_prompt=custom_prompt
    )
    
    pipeline = SpritesheetPipeline(config)
    return await pipeline.generate_character_set(ctx)
