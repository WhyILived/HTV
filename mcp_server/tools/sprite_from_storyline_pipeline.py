#!/usr/bin/env python3
"""
Sprite generation pipeline for storyline characters.
Self-contained sprite generation with Gemini API integration.
"""

import asyncio
import json
import sys
import base64
import mimetypes
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()


def _save_binary_file(file_name, data):
    """Save binary data to file."""
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}", file=sys.stderr, flush=True)


def _generate_image_with_gemini(prompt: str, reference_image_path: str = None, output_name: str = None, max_retries: int = 3) -> bool:
    """Generate a single image using Gemini API with retry logic."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")

    client = genai.Client(api_key=api_key)
    model = "gemini-2.5-flash-image-preview"

    # Load reference image - Windows compatible path handling
    if reference_image_path is None:
        script_dir = Path(__file__).parent.parent.parent  # Go up to project root
        reference_image_path = script_dir / "schemas" / "excharacs" / "example_male_1.png"
    
    ref_path = Path(reference_image_path)
    if not ref_path.exists():
        raise FileNotFoundError(f"Reference image not found: {ref_path}")
    
    with open(ref_path, "rb") as f:
        ref_image_data = f.read()
    
    ref_mime_type = mimetypes.guess_type(str(ref_path))[0] or "image/png"

    # Create parts with image data
    parts = [types.Part.from_text(text=prompt)]
    
    # Add image part using the correct API structure
    image_part = types.Part()
    image_part.inline_data = types.Blob(
        mime_type=ref_mime_type,
        data=ref_image_data
    )
    parts.append(image_part)

    contents = [
        types.Content(
            role="user",
            parts=parts,
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )

    if output_name:
        # Windows compatible path handling
        out_dir = Path(output_name).parent.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = Path("mcp_output").resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating with model: {model}", file=sys.stderr, flush=True)
    print(f"Prompt: {prompt}", file=sys.stderr, flush=True)
    print(f"Reference image: {ref_path}", file=sys.stderr, flush=True)
    
    # Retry logic for API failures
    for attempt in range(max_retries):
        try:
            print(f"Starting Gemini API call (attempt {attempt + 1}/{max_retries})...", file=sys.stderr, flush=True)
            chunk_count = 0
            image_saved = False
            
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                chunk_count += 1
                print(f"Received chunk {chunk_count}", file=sys.stderr, flush=True)
                
                if (
                    not chunk.candidates
                    or not chunk.candidates[0].content
                    or not chunk.candidates[0].content.parts
                ):
                    print("Empty chunk received, continuing...", file=sys.stderr, flush=True)
                    continue
                    
                part0 = chunk.candidates[0].content.parts[0]
                
                if getattr(part0, "inline_data", None) and getattr(part0.inline_data, "data", None):
                    inline_data = part0.inline_data
                    data_buffer = inline_data.data
                    
                    if output_name:
                        file_path = Path(output_name).with_suffix(".png")
                    else:
                        file_name = f"generated_{chunk_count}"
                        file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                        file_path = out_dir / f"{file_name}{file_extension}"
                    
                    print(f"Saving image: {file_path}", file=sys.stderr, flush=True)
                    _save_binary_file(file_path, data_buffer)
                    image_saved = True
                    print("Image saved successfully!", file=sys.stderr, flush=True)
                    break  # Exit the loop once we have an image
                else:
                    # Text output
                    if getattr(chunk, "text", None):
                        print(f"Text output: {chunk.text}", file=sys.stderr, flush=True)
            
            if not image_saved:
                print("No image was generated from the API response", file=sys.stderr, flush=True)
                if attempt < max_retries - 1:
                    print(f"Retrying in 2 seconds... (attempt {attempt + 2}/{max_retries})", file=sys.stderr, flush=True)
                    import time
                    time.sleep(2)
                    continue
                return False
                
            return True
                
        except Exception as e:
            print(f"Error during Gemini API call (attempt {attempt + 1}/{max_retries}): {e}", file=sys.stderr, flush=True)
            if attempt < max_retries - 1:
                print(f"Retrying in 3 seconds... (attempt {attempt + 2}/{max_retries})", file=sys.stderr, flush=True)
                import time
                time.sleep(3)
                continue
            else:
                print("All retry attempts failed", file=sys.stderr, flush=True)
                import traceback
                traceback.print_exc()
                return False
    
    return False


class CharacterConfig:
    """Configuration for character generation."""
    def __init__(self, name: str, character_type: str, custom_prompt: str, background_color: str = "#ea00ff", size: str = "64"):
        self.name = name
        self.character_type = character_type
        self.custom_prompt = custom_prompt
        self.background_color = background_color
        self.size = size


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
                   f"MAKE SURE ITS TURNING AN ALMOST 45 DEGREES SIMILAR TO TOP DOWN GAMES. DONT HAVE ANY WEAPONS OR ITEMS IN ITS HANDS. "
                   f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}** - NO TRANSPARENCY, NO OTHER COLORS. "
                   f"The character must be **centered**, well-proportioned, and rendered in a **high-detail {self.config.size} pixel art style**.",
            
            # Idle animation - slight breathing movement
            "idle": f"EDIT the base character image to create a subtle idle breathing animation. "
                   f"Make a bit of change - the character should down a bit to show breathing. "
                   f"Keep the same pose, clothing, and all other details exactly the same. "
                   f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}** - NO TRANSPARENCY, NO OTHER COLORS. "
                   f"Ensure the character is centered and maintains the same proportions as the base image.",
            
            # Walk animation 1 - right leg forward, left leg back
            "walk1": f"EDIT the base character image to create a walking pose. "
                    f"POSTURE DETAILS: For the RIGHT SIDE of the picture, the leg should be FORWARD and the hand should be BACK. "
                    f"For the LEFT SIDE of the picture, the leg should be BENT and the hand should be FORWARD. "
                    f"Show a natural walking step with the right leg extended forward and left leg bent behind. "
                    f"Arms should swing naturally - right arm back, left arm forward. "
                    f"Body should be slightly leaned forward in a walking motion. "
                    f"Keep the same character design, colors, and style as the base image. "
                    f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}** - NO TRANSPARENCY, NO OTHER COLORS. "
                    f"Ensure the character is centered and well-proportioned for a {self.config.size} pixel art style.",
            
            # Walk animation 2 - opposite of walk1 (left leg forward, right leg back)
            "walk2": f"EDIT the base character image to create the second walking pose - the OPPOSITE of walk1. "
                    f"POSTURE DETAILS: For the LEFT SIDE of the picture, the leg should be FORWARD and the hand should be BACK. "
                    f"For the RIGHT SIDE of the picture, the leg should be BENT and the hand should be FORWARD. "
                    f"Show a natural walking step with the left leg extended forward and right leg bent behind. "
                    f"Arms should swing naturally - left arm back, right arm forward. "
                    f"Body should be slightly leaned forward in a walking motion. "
                    f"Keep the same character design, colors, and style as the base image. "
                    f"The **ENTIRE BACKGROUND MUST BE EXACTLY {self.config.background_color}** - NO TRANSPARENCY, NO OTHER COLORS. "
                    f"Ensure the character is centered and well-proportioned for a {self.config.size} pixel art style."
        }
    
    def _get_reference_path(self, ref_name: str) -> Path:
        """Get the path to a reference image - Windows compatible."""
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / "schemas" / "excharacs" / ref_name
    
    def _generate_image_sync(self, prompt: str, output_name: str, reference_image: Optional[str] = None) -> bool:
        """Generate a single image with optional reference (synchronous)."""
        try:
            print(f"Generating image: {output_name}", file=sys.stderr, flush=True)
            print(f"Prompt length: {len(prompt)} characters", file=sys.stderr, flush=True)
            
            ref_path = None
            if reference_image:
                # Windows compatible path checking
                if "/" in reference_image or "\\" in reference_image:
                    ref_path = Path(reference_image)
                else:
                    ref_path = self._get_reference_path(reference_image)
                
                if not ref_path.exists():
                    print(f"Reference image not found: {ref_path}", file=sys.stderr, flush=True)
                    ref_path = None
                else:
                    print(f"Using reference image: {ref_path}", file=sys.stderr, flush=True)
            
            # Generate the image with custom output name
            output_path = self.output_dir / f"{output_name}.png"
            print(f"Output path: {output_path}", file=sys.stderr, flush=True)
            
            print("Calling generate function...", file=sys.stderr, flush=True)
            success = _generate_image_with_gemini(prompt, str(ref_path) if ref_path else None, str(output_path))
            
            print("Generate function completed", file=sys.stderr, flush=True)
            
            # Check if the file was created successfully
            if output_path.exists():
                print(f"Image saved successfully: {output_path}", file=sys.stderr, flush=True)
                return True
            else:
                print(f"Image file not found after generation: {output_path}", file=sys.stderr, flush=True)
            return False
            
        except Exception as e:
            print(f"Failed to generate {output_name}: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()
            return False
    
    async def _generate_image(self, prompt: str, output_name: str, reference_image: Optional[str] = None) -> bool:
        """Generate a single image with optional reference (async wrapper)."""
        try:
            # Add timeout to prevent hanging
            return await asyncio.wait_for(
                asyncio.to_thread(self._generate_image_sync, prompt, output_name, reference_image),
                timeout=120  # 2 minute timeout per image
            )
        except asyncio.TimeoutError:
            print(f"Timeout generating {output_name}", file=sys.stderr, flush=True)
            return False
        except Exception as e:
            print(f"Error generating {output_name}: {e}", file=sys.stderr, flush=True)
            return False
    
    async def generate_character_set(self) -> Dict[str, str]:
        """Generate 4 character images: base, idle, walk1, walk2."""
        print("Starting simplified character generation pipeline...", file=sys.stderr, flush=True)
        
        results = {}
        start_time = asyncio.get_event_loop().time()
        
        # Step 1: Generate base character using example reference
        print("Step 1: Generating base character from example reference...", file=sys.stderr, flush=True)
        
        ref_image = self.ref_images[self.config.character_type]
        print(f"Using reference image: {ref_image}", file=sys.stderr, flush=True)
        
        print("Starting base image generation...", file=sys.stderr, flush=True)
        success = await self._generate_image(
            self.prompts["base"],
            f"{self.config.name}_base",
            ref_image
        )
        
        if not success:
            error_msg = "Failed to generate base character - check GEMINI_API_KEY and reference images"
            print(f"{error_msg}", file=sys.stderr, flush=True)
            raise RuntimeError(error_msg)
        
        print("Base character generated successfully", file=sys.stderr, flush=True)
        results["base"] = f"{self.config.name}_base.png"
        
        # Use the generated base character as reference for all subsequent generations
        base_character_path = str(self.output_dir / f"{self.config.name}_base.png")
        print(f"Base character path: {base_character_path}", file=sys.stderr, flush=True)
        
        # Ensure the base character file is fully written and accessible
        max_wait = 10  # Maximum wait time in seconds
        wait_time = 0
        while not self.output_dir.joinpath(f"{self.config.name}_base.png").exists() and wait_time < max_wait:
            # Use non-blocking sleep to avoid freezing the MCP server event loop
            await asyncio.sleep(0.1)
            wait_time += 0.1
        
        if not self.output_dir.joinpath(f"{self.config.name}_base.png").exists():
            raise RuntimeError(f"Base character file not found after generation: {base_character_path}")
        
        print(f"Base character file confirmed: {base_character_path}", file=sys.stderr, flush=True)
        
        # Step 2: Generate idle, walk1, and walk2 animations concurrently
        print("Step 2: Generating idle, walk1, and walk2 animations concurrently...", file=sys.stderr, flush=True)
        
        print("Starting concurrent animation generation...", file=sys.stderr, flush=True)
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
        
        print("Waiting for all animations to complete...", file=sys.stderr, flush=True)
        try:
            # Add timeout to prevent hanging
            animation_results = await asyncio.wait_for(
                asyncio.gather(*animation_tasks, return_exceptions=True),
                timeout=300  # 5 minute timeout
            )
            animation_names = ["idle", "walk1", "walk2"]
            
            # Process results and retry failed animations
            failed_animations = []
            for i, result in enumerate(animation_results):
                if isinstance(result, Exception):
                    print(f"Animation {animation_names[i]} failed: {result}", file=sys.stderr, flush=True)
                    failed_animations.append(i)
                elif result:
                    results[animation_names[i]] = f"{self.config.name}_{animation_names[i]}.png"
                    print(f"Animation {animation_names[i]} completed successfully", file=sys.stderr, flush=True)
                else:
                    print(f"Animation {animation_names[i]} returned False", file=sys.stderr, flush=True)
                    failed_animations.append(i)
            
            # Retry failed animations individually
            if failed_animations:
                print(f"Retrying {len(failed_animations)} failed animations...", file=sys.stderr, flush=True)
                for i in failed_animations:
                    animation_name = animation_names[i]
                    print(f"Retrying {animation_name}...", file=sys.stderr, flush=True)
                    retry_result = await self._generate_image(
                        self.prompts[animation_name],
                        f"{self.config.name}_{animation_name}",
                        base_character_path
                    )
                    if retry_result:
                        results[animation_name] = f"{self.config.name}_{animation_name}.png"
                        print(f"Animation {animation_name} retry successful", file=sys.stderr, flush=True)
                    else:
                        print(f"Animation {animation_name} retry failed", file=sys.stderr, flush=True)
                        
        except Exception as e:
            print(f"Error in animation generation: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()
        
        # Generate metadata asynchronously to avoid blocking
        try:
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
                "generated_at": asyncio.get_event_loop().time(),
                "total_sprites": len(results)
            }
            
            # Save metadata with error handling
            metadata_path = self.output_dir / f"{self.config.name}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Metadata saved: {metadata_path.name}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"Warning: Failed to save metadata for {self.config.name}: {e}", file=sys.stderr, flush=True)
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        print(f"Character generation complete! Generated {len(results)} sprites in {total_time:.2f}s", file=sys.stderr, flush=True)
        print(f"Output directory: {self.output_dir}", file=sys.stderr, flush=True)
        
        return results


async def generate_sprites_from_storyline(storyline_file: str = "storyline.json") -> str:
    """
    Generate sprites for all characters from a storyline JSON file.
    This is the exact same logic as the working test_sprite_generation.py
    """
    print("=== Generating Sprites from Storyline ===", file=sys.stderr, flush=True)
    
    # Load storyline
    storyline_path = Path(storyline_file)
    if not storyline_path.exists():
        return f"❌ {storyline_file} not found!"
    
    try:
        with open(storyline_path, 'r', encoding='utf-8') as f:
            storyline_data = json.load(f)
    except Exception as e:
        return f"❌ Error loading {storyline_file}: {e}"
    
    # Extract characters (same logic as test script)
    characters = []
    
    # Add main character
    if "main_character" in storyline_data:
        main_char_data = storyline_data["main_character"]
        if isinstance(main_char_data, dict) and "main_character" in main_char_data:
            main_char = main_char_data["main_character"]
        else:
            main_char = main_char_data
            
        characters.append({
            "name": main_char.get("name", "MainCharacter"),
            "description": main_char.get("visual_description", main_char.get("description", "Main character")),
            "character_type": main_char.get("type", "male")
        })
    
    # Add other characters
    if "characters" in storyline_data:
        chars_data = storyline_data["characters"]
        if isinstance(chars_data, dict) and "characters" in chars_data:
            chars_list = chars_data["characters"]
            if isinstance(chars_list, dict) and "items" in chars_list:
                chars_array = chars_list["items"]
            else:
                chars_array = chars_list
        else:
            chars_array = chars_data
        
        if isinstance(chars_array, list):
            for char in chars_array:
                char_type = char.get("type", "male")
                visual_desc = char.get("visual_description", char.get("description", "Character"))
                characters.append({
                    "name": char.get("name", "Character"),
                    "description": visual_desc,
                    "character_type": char_type
                })
    
    print(f"Found {len(characters)} characters for concurrent generation", file=sys.stderr, flush=True)
    
    if not characters:
        return "❌ No characters found in storyline!"
    
    # Generate sprites concurrently (exact same logic as test script)
    async def generate_character_async(char):
        try:
            print(f"Starting generation for: {char['name']}", file=sys.stderr, flush=True)
            
            config = CharacterConfig(
                name=char['name'].replace(' ', '_').lower(),
                character_type=char['character_type'],
                custom_prompt=char['description'],
                background_color="#ea00ff",
                size=64
            )
            
            pipeline = SpritesheetPipeline(config)
            char_result = await asyncio.wait_for(
                pipeline.generate_character_set(),
                timeout=600  # 10 minute timeout per character
            )
            
            if char_result and len(char_result) > 0:
                sprite_list = "\n".join([f"  - {name}: {filename}" for name, filename in char_result.items()])
                print(f"✅ {char['name']} completed successfully", file=sys.stderr, flush=True)
                return f"✅ {char['name']} sprites generated:\n{sprite_list}"
            else:
                print(f"❌ No sprites generated for {char['name']}", file=sys.stderr, flush=True)
                return f"❌ Failed to generate sprites for {char['name']}"
                
        except asyncio.TimeoutError:
            print(f"⏰ Timeout for {char['name']} (exceeded 10 minutes)", file=sys.stderr, flush=True)
            return f"⏰ Timeout generating sprites for {char['name']} (exceeded 10 minutes)"
        except Exception as e:
            print(f"❌ Exception for {char['name']}: {str(e)}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()
            return f"❌ Error generating sprites for {char['name']}: {str(e)}"
    
    # Create tasks for all characters
    tasks = [generate_character_async(char) for char in characters]
    
    # Run all character generations concurrently
    print(f"Starting concurrent generation for {len(characters)} characters...", file=sys.stderr, flush=True)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions that occurred
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append(f"❌ Error generating sprites for {characters[i]['name']}: {str(result)}")
        else:
            final_results.append(result)
    
    # Return results
    success_count = len([r for r in final_results if r.startswith("✅")])
    total_count = len(final_results)
    
    result_text = f"Character Sprites Generation Complete ({success_count}/{total_count} successful):\n\n" + "\n\n".join(final_results)
    
    print(f"Generation completed: {success_count}/{total_count} characters successful", file=sys.stderr, flush=True)
    
    return result_text
