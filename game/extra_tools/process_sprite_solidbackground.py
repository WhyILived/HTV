from PIL import Image
from collections import deque, Counter

def sample_background_color(img, tolerance=5):
    """
    Sample background color from the four corners of the image.
    Returns the most common color among the corners with RGB tolerance.
    """
    width, height = img.size
    
    # Get corner pixels
    corners = [
        img.getpixel((0, 0)),  # Top-left
        img.getpixel((width-1, 0)),  # Top-right
        img.getpixel((0, height-1)),  # Bottom-left
        img.getpixel((width-1, height-1))  # Bottom-right
    ]
    
    print(f"Corner colors: {corners}")
    
    # Convert to RGB if needed
    if img.mode == 'RGBA':
        corners = [(r, g, b) for r, g, b, a in corners]
    elif img.mode == 'L':
        corners = [(c, c, c) for c in corners]
    
    def colors_are_similar(color1, color2, tolerance):
        """Check if two colors are similar within tolerance for each RGB component"""
        return (abs(color1[0] - color2[0]) <= tolerance and
                abs(color1[1] - color2[1]) <= tolerance and
                abs(color1[2] - color2[2]) <= tolerance)
    
    # Group similar colors together
    color_groups = []
    for corner_color in corners:
        # Check if this color is similar to any existing group
        added_to_group = False
        for group in color_groups:
            # Check if this color is similar to the group's representative color
            rep_color = group[0]
            if colors_are_similar(corner_color, rep_color, tolerance):
                group.append(corner_color)
                added_to_group = True
                break
        
        if not added_to_group:
            color_groups.append([corner_color])
    
    # Find the largest group
    largest_group = max(color_groups, key=len)
    
    # Calculate average color for the largest group to get a more representative color
    if len(largest_group) > 1:
        avg_r = sum(color[0] for color in largest_group) // len(largest_group)
        avg_g = sum(color[1] for color in largest_group) // len(largest_group)
        avg_b = sum(color[2] for color in largest_group) // len(largest_group)
        background_color = (avg_r, avg_g, avg_b)
    else:
        background_color = largest_group[0]
    
    print(f"Background color detected: {background_color} (appears in {len(largest_group)}/4 corners, tolerance: ±{tolerance})")
    
    # If we only found 1-2 corners matching, try with a larger tolerance to be more inclusive
    if len(largest_group) < 3:
        print("Few corners matched, trying with larger tolerance...")
        larger_tolerance = tolerance * 2
        color_groups_large = []
        for corner_color in corners:
            added_to_group = False
            for group in color_groups_large:
                rep_color = group[0]
                if colors_are_similar(corner_color, rep_color, larger_tolerance):
                    group.append(corner_color)
                    added_to_group = True
                    break
            if not added_to_group:
                color_groups_large.append([corner_color])
        
        largest_group_large = max(color_groups_large, key=len)
        if len(largest_group_large) > len(largest_group):
            if len(largest_group_large) > 1:
                avg_r = sum(color[0] for color in largest_group_large) // len(largest_group_large)
                avg_g = sum(color[1] for color in largest_group_large) // len(largest_group_large)
                avg_b = sum(color[2] for color in largest_group_large) // len(largest_group_large)
                background_color = (avg_r, avg_g, avg_b)
            else:
                background_color = largest_group_large[0]
            print(f"Updated background color: {background_color} (appears in {len(largest_group_large)}/4 corners, tolerance: ±{larger_tolerance})")
    
    return background_color

def process_sprite_solidbackground(input_file, output_file, target_size=(256, 384), background_color=None):
    """
    Complete sprite processing: crop to correct aspect ratio, downscale, and remove solid background.
    """
    # Load original image
    img = Image.open(input_file)
    print(f"Original: {img.size} (aspect ratio: {img.size[0]/img.size[1]:.3f})")
    
    # Sample background color if not provided
    if background_color is None:
        sampled_bg = sample_background_color(img)
        background_color = f"#{sampled_bg[0]:02x}{sampled_bg[1]:02x}{sampled_bg[2]:02x}"
        print(f"Using sampled background color: {background_color}")
    
    # Calculate crop to match target aspect ratio
    original_width, original_height = img.size
    target_aspect_ratio = target_size[0] / target_size[1]
    original_aspect_ratio = original_width / original_height
    
    if original_aspect_ratio > target_aspect_ratio:
        # Crop sides
        new_width = int(original_height * target_aspect_ratio)
        left = (original_width - new_width) // 2
        cropped_img = img.crop((left, 0, left + new_width, original_height))
    else:
        # Crop top/bottom
        new_height = int(original_width / target_aspect_ratio)
        top = (original_height - new_height) // 2
        cropped_img = img.crop((0, top, original_width, top + new_height))
    
    print(f"Cropped: {cropped_img.size} (aspect ratio: {cropped_img.size[0]/cropped_img.size[1]:.3f})")
    
    # Downscale to target size
    downscaled_img = cropped_img.resize(target_size, Image.NEAREST)
    print(f"Downscaled: {downscaled_img.size}")
    
    # Convert to RGBA for transparency
    if downscaled_img.mode != 'RGBA':
        downscaled_img = downscaled_img.convert('RGBA')
    
    # Parse background color
    bg_color = background_color.lstrip('#')
    bg_r = int(bg_color[0:2], 16)
    bg_g = int(bg_color[2:4], 16)
    bg_b = int(bg_color[4:6], 16)
    
    # Remove background using tolerance-based color matching
    width, height = downscaled_img.size
    pixels = downscaled_img.load()
    color_tolerance = 10  # Use larger tolerance for removal to catch more similar colors
    
    def is_background_color(x, y):
        """Check if pixel matches background color within tolerance"""
        if x < 0 or x >= width or y < 0 or y >= height:
            return False
        r, g, b, a = pixels[x, y]
        return (abs(r - bg_r) <= color_tolerance and 
                abs(g - bg_g) <= color_tolerance and 
                abs(b - bg_b) <= color_tolerance)
    
    # Remove all background colors throughout the entire image
    background_pixels_removed = 0
    for y in range(height):
        for x in range(width):
            if is_background_color(x, y):
                r, g, b, a = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)  # Make transparent
                background_pixels_removed += 1
    
    print(f"Removed {background_pixels_removed} background pixels using tolerance ±{color_tolerance}")
    
    # Clean edges: make outermost 2 pixels black
    # This finds actual edges of the character shape, not just bounding box edges
    def is_edge_pixel(x, y):
        """Check if a pixel is on the edge of the character (has transparent neighbors)"""
        if pixels[x, y][3] == 0:  # Skip transparent pixels
            return False
        
        # Check 8-connected neighbors
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if pixels[nx, ny][3] == 0:  # Has transparent neighbor
                        return True
        return False
    
    # Find all edge pixels
    edge_pixels = []
    for y in range(height):
        for x in range(width):
            if is_edge_pixel(x, y):
                edge_pixels.append((x, y))
    
    print(f"Found {len(edge_pixels)} edge pixels")
    
    # For each edge pixel, make it and its neighbors within 2 pixels black
    for edge_x, edge_y in edge_pixels:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = edge_x + dx, edge_y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if pixels[nx, ny][3] > 0:  # Only modify non-transparent pixels
                        distance = max(abs(dx), abs(dy))  # Chebyshev distance
                        if distance < 2:
                            pixels[nx, ny] = (0, 0, 0, 255)  # Black
    
    # Save result
    downscaled_img.save(output_file)
    print(f"Saved: {output_file}")

if __name__ == "__main__":
    process_sprite_solidbackground("test/m1.png", "test/m11.png")

