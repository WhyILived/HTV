#!/usr/bin/env python3
"""
Map/background generation pipeline for storyline scenes.
Self-contained background generation with Gemini API integration.
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
    """Generate a single background image using Gemini API with retry logic."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")

    client = genai.Client(api_key=api_key)
    model = "gemini-2.5-flash-image-preview"

    # Load reference image - Windows compatible path handling
    if reference_image_path is None:
        script_dir = Path(__file__).parent.parent.parent  # Go up to project root
        reference_image_path = script_dir / "schemas" / "exmaps" / "room.png"
    
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
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            )
        ]
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


class MapConfig:
    """Configuration for map/background generation."""
    def __init__(self, name: str, scene_type: str, custom_prompt: str, background_color: str = "#ea00ff", size: str = "64"):
        self.name = name
        self.scene_type = scene_type
        self.custom_prompt = custom_prompt
        self.background_color = background_color
        self.size = size


class MapPipeline:
    """Generates background images for different scene types."""
    
    def __init__(self, config: MapConfig):
        self.config = config
        self.output_dir = Path("mcp_output/maps")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Reference images based on scene type
        self.ref_images = {
            "room": "room.png",      # Use existing reference
            "futuristic_room": "futuristic_room.png",  # Use existing reference
            "nature": "nature.png",    # Use existing reference
            "halls": "halls.png",     # Use existing reference
            "market": "market.png",    # Use existing reference
            "misc": "room.png"       # Use room as reference for misc
        }
        
        # Prompts for each scene type
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompts for different scene types."""
        base_description = self.config.custom_prompt if self.config.custom_prompt else f"a {self.config.scene_type} scene"
        
        scene_prompts = {
            "room": f"create a **High-detail pixel art** 2D top-down indoor room scene in a similar style to the reference image based on this additional context: " 
                f"{base_description}. "
                f"**Reference character style and color palette**."
                f"Include detailed walls, floor, furniture, and game-ready architectural elements while making sure there is enough space for the character to move around. "
                f"Use a clear **top-down** perspective similar to the reference image. "
                f"Fill the entire aspect ratio. as the reference image.",
            
            "futuristic_room": f"create a **High-detail pixel art** 2D top-down indoor futuristic room scene in a similar style to the reference image based on this additional context: " 
                f"{base_description}. "
                f"**Reference character style and color palette**."
                f"Include detailed walls, floor, futuristic furniture, advanced technology, holographic displays, and game-ready architectural elements while making sure there is enough space for the character to move around. "
                f"Use a clear **top-down** perspective similar to the reference image. "
                f"Fill the entire aspect ratio. as the reference image.",
            
            "nature": f"create a **High-detail pixel art** 2D **top-down** outdoor **natural landscape** background. based on this additional context: "
                f"{base_description}. "
                f"**Reference character style and color palette**"
                f"Include detailed terrain, vegetation (trees, lakes, etc.), and environmental features. "
                f"Use a clear **top-down** perspective similar to the reference image. "
                f"Fill the entire aspect ratio. as the reference image. ",
            
            "halls": f"create a **High-detail pixel art** 2D top-down indoor hallway/corridor scene in a similar style to the reference image based on this additional context: " 
                    f"{base_description}. "
                    f"**Reference character style and color palette**."
                    f"Include detailed walls, floor, ceiling, doors, and corridor features while making sure there is enough space for the character to move around. "
                    f"Use a clear **top-down** perspective similar to the reference image. "
                    f"Fill the entire aspect ratio. as the reference image.",
            
            "market": f"create a **High-detail pixel art** 2D **top-down** outdoor marketplace background in a similar style to the reference image based on this additional context: "
                     f"{base_description}. "
                     f"**Reference character style and color palette**"
                     f"Include detailed stalls, vendors, goods, and market atmosphere while making sure there is enough space for the character to move around. "
                     f"Use a clear **top-down** perspective similar to the reference image. "
                     f"Fill the entire aspect ratio. as the reference image.",
            
            "misc": f"create a **High-detail pixel art** 2D top-down miscellaneous scene using the **art style and color palette** of the reference image but be **creative and heavily based on this custom description**: " 
                   f"{base_description}. "
                   f"**Use only the reference image's art style and color palette** - do not copy the room layout or furniture. "
                   f"Design a unique scene based heavily on the custom description with appropriate environmental elements while making sure there is enough space for the character to move around. "
                   f"Use a clear **top-down** perspective similar to the reference image. "
                   f"Fill the entire aspect ratio. as the reference image."
        }
        
        return scene_prompts
    
    def _get_reference_path(self, ref_name: str) -> Path:
        """Get the path to a reference image - Windows compatible."""
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / "schemas" / "exmaps" / ref_name
    
    def _generate_image_sync(self, prompt: str, output_name: str, reference_image: Optional[str] = None) -> bool:
        """Generate a single background image with optional reference (synchronous)."""
        try:
            print(f"Generating background: {output_name}", file=sys.stderr, flush=True)
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
                print(f"Background saved successfully: {output_path}", file=sys.stderr, flush=True)
                return True
            else:
                print(f"Background file not found after generation: {output_path}", file=sys.stderr, flush=True)
            return False
            
        except Exception as e:
            print(f"Failed to generate {output_name}: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()
            return False
    
    async def _generate_image(self, prompt: str, output_name: str, reference_image: Optional[str] = None) -> bool:
        """Generate a single background image with optional reference (async wrapper)."""
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
    
    async def generate_background(self) -> Dict[str, str]:
        """Generate a background image for the specified scene type."""
        print(f"Starting background generation for {self.config.scene_type} scene...", file=sys.stderr, flush=True)
        
        results = {}
        start_time = asyncio.get_event_loop().time()
        
        # Generate background using scene-specific prompt
        print(f"Generating {self.config.scene_type} background...", file=sys.stderr, flush=True)
        
        ref_image = self.ref_images[self.config.scene_type]
        print(f"Using reference image: {ref_image}", file=sys.stderr, flush=True)
        
        print("Starting background generation...", file=sys.stderr, flush=True)
        success = await self._generate_image(
            self.prompts[self.config.scene_type],
            f"{self.config.name}_{self.config.scene_type}",
            ref_image
        )
        
        if not success:
            error_msg = "Failed to generate background - check GEMINI_API_KEY and reference images"
            print(f"{error_msg}", file=sys.stderr, flush=True)
            raise RuntimeError(error_msg)
        
        print("Background generated successfully", file=sys.stderr, flush=True)
        results["background"] = f"{self.config.name}_{self.config.scene_type}.png"
        
        # Generate metadata
        try:
            metadata = {
                "map": {
                    "name": self.config.name,
                    "scene_type": self.config.scene_type,
                    "custom_prompt": self.config.custom_prompt,
                    "background_color": self.config.background_color,
                    "size": self.config.size
                },
                "background": results,
                "generated_at": asyncio.get_event_loop().time()
            }
            
            # Save metadata with error handling
            metadata_path = self.output_dir / f"{self.config.name}_{self.config.scene_type}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Metadata saved: {metadata_path.name}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"Warning: Failed to save metadata for {self.config.name}: {e}", file=sys.stderr, flush=True)
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        print(f"Background generation complete! Generated in {total_time:.2f}s", file=sys.stderr, flush=True)
        print(f"Output directory: {self.output_dir}", file=sys.stderr, flush=True)
        
        return results


async def generate_background_from_prompt(user_prompt: str, scene_type: str, custom_name: str = None) -> str:
    """
    Generate a background image from user prompt and scene type.
    
    Args:
        user_prompt: Custom description for the background
        scene_type: One of "room", "futuristic_room", "nature", "halls", "market", "misc"
        custom_name: Optional custom name for the generated file (defaults to background_{scene_type})
    
    Returns:
        Result message with generation status
    """
    print("=== Generating Background from Prompt ===", file=sys.stderr, flush=True)
    
    # Validate scene type
    valid_scene_types = ["room", "futuristic_room", "nature", "halls", "market", "misc"]
    if scene_type not in valid_scene_types:
        return f"ERROR: Invalid scene type: {scene_type}. Must be one of: {valid_scene_types}"
    
    try:
        # Create config with custom name if provided
        name = custom_name if custom_name else f"background_{scene_type}"
        config = MapConfig(
            name=name,
            scene_type=scene_type,
            custom_prompt=user_prompt,
            background_color="#ea00ff",
            size=64
        )
        
        # Generate background
        pipeline = MapPipeline(config)
        result = await pipeline.generate_background()
        
        if result and len(result) > 0:
            background_file = list(result.values())[0]
            return f"SUCCESS: Background generated successfully: {background_file}"
        else:
            return "ERROR: Failed to generate background - no output produced"
            
    except Exception as e:
        print(f"ERROR: Error generating background: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        return f"ERROR: Error generating background: {str(e)}"
