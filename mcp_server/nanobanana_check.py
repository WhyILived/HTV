import base64
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")


def generate(prompt: str = "Make a pixelated art character based on King Arthur. Match the pixel art style and dimensions of the reference image exactly. Keep the WHOLE BACKGROUND EXACTLY #ea00ff color and ensure the character is centered and well-proportioned for a 16x16 pixel art style. MAKE SURE ITS TURNING AN ALMOST 45 DEGREES SIMILAR TO TOP DOWN GAMES. DONT HAVE ANY WEAPONS OR ITEMS IN ITS HANDS", reference_image_path: str = None, output_name: str = None):
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")

    client = genai.Client(api_key=api_key)
    model = "gemini-2.5-flash-image-preview"

    # Load reference image - Windows compatible path handling
    if reference_image_path is None:
        script_dir = Path(__file__).parent.parent  # Go up one level from mcp_server
        reference_image_path = script_dir / "schemas" / "excharacs" / "mp2.png"
    
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

    file_index = 0
    print(f"Generating with model: {model}")
    print(f"Prompt: {prompt}")
    print(f"Reference image: {ref_path}")
    
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            not chunk.candidates
            or not chunk.candidates[0].content
            or not chunk.candidates[0].content.parts
        ):
            continue
            
        part0 = chunk.candidates[0].content.parts[0]
        
        if getattr(part0, "inline_data", None) and getattr(part0.inline_data, "data", None):
            inline_data = part0.inline_data
            data_buffer = inline_data.data
            
            if output_name:
                file_path = Path(output_name).with_suffix(".png")
            else:
                file_name = f"nanobanana_{file_index}"
                file_index += 1
                file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                file_path = out_dir / f"{file_name}{file_extension}"
            
            print(f"Saving image: {file_path}")
            save_binary_file(file_path, data_buffer)
        else:
            # Text output
            if getattr(chunk, "text", None):
                print(chunk.text, end="")


if __name__ == "__main__":
    generate()


