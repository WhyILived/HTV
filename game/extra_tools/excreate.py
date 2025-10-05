from PIL import Image

def transparent_to_color(input_file, output_file, color="#ea00ff"):
    """
    Convert transparent pixels to the specified color.
    """
    # Load image
    img = Image.open(input_file)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Parse color
    color = color.lstrip('#')
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    
    # Create new image with background color
    width, height = img.size
    new_img = Image.new('RGB', (width, height), (r, g, b))
    
    # Paste original image on top (transparent areas will show background)
    new_img.paste(img, (0, 0), img)
    
    # Save result
    new_img.save(output_file)
    print(f"Converted transparent pixels to {color} in {output_file}")

if __name__ == "__main__":
    transparent_to_color("pictures/m2.png", "pictures/mp2.png")
