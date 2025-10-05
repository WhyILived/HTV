#!/usr/bin/env python3
"""
Batch script to process all PNG files in the spritesheets directory
using process_sprite_solidbackground and save them to trans_sprites directory.
"""

import os
import glob
from PIL import Image
from collections import deque, Counter

def sample_background_color_high_tolerance(img, tolerance=15):
    """
    Sample background color from the four corners of the image with higher tolerance.
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
    
    return background_color

def process_sprite_high_tolerance(input_file, output_file, target_size=(256, 384), detection_tolerance=15, removal_tolerance=25):
    """
    Complete sprite processing with higher tolerance settings.
    """
    # Load original image
    img = Image.open(input_file)
    print(f"Original: {img.size} (aspect ratio: {img.size[0]/img.size[1]:.3f})")
    
    # Sample background color with higher tolerance
    sampled_bg = sample_background_color_high_tolerance(img, detection_tolerance)
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
    
    # Remove background using higher tolerance
    width, height = downscaled_img.size
    pixels = downscaled_img.load()
    
    def is_background_color(x, y):
        """Check if pixel matches background color within tolerance"""
        if x < 0 or x >= width or y < 0 or y >= height:
            return False
        r, g, b, a = pixels[x, y]
        return (abs(r - bg_r) <= removal_tolerance and 
                abs(g - bg_g) <= removal_tolerance and 
                abs(b - bg_b) <= removal_tolerance)
    
    # Remove all background colors throughout the entire image
    background_pixels_removed = 0
    for y in range(height):
        for x in range(width):
            if is_background_color(x, y):
                r, g, b, a = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)  # Make transparent
                background_pixels_removed += 1
    
    print(f"Removed {background_pixels_removed} background pixels using tolerance ±{removal_tolerance}")
    
    # Clean edges: make outermost 2 pixels black
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

def main():
    # Define paths
    spritesheets_dir = "spritesheets"
    output_dir = "trans_sprites_high_tolerance"
    
    # Higher tolerance settings
    detection_tolerance = 15  # Increased from default 5
    removal_tolerance = 25    # Increased from default 10
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Find all PNG files in spritesheets directory
    png_pattern = os.path.join(spritesheets_dir, "*.png")
    png_files = glob.glob(png_pattern)
    
    if not png_files:
        print(f"No PNG files found in {spritesheets_dir} directory")
        return
    
    print(f"Found {len(png_files)} PNG files to process:")
    for png_file in png_files:
        print(f"  - {png_file}")
    
    print(f"\nUsing higher tolerance settings:")
    print(f"  - Detection tolerance: ±{detection_tolerance}")
    print(f"  - Removal tolerance: ±{removal_tolerance}")
    print("\nStarting batch processing...")
    
    # Process each PNG file
    processed_count = 0
    failed_count = 0
    
    for input_file in png_files:
        try:
            # Get the filename without path
            filename = os.path.basename(input_file)
            
            # Create output filename (keep the same name)
            output_file = os.path.join(output_dir, filename)
            
            print(f"\nProcessing: {filename}")
            print(f"Input: {input_file}")
            print(f"Output: {output_file}")
            
            # Process the sprite with higher tolerance
            process_sprite_high_tolerance(input_file, output_file, detection_tolerance=detection_tolerance, removal_tolerance=removal_tolerance)
            
            processed_count += 1
            print(f"✓ Successfully processed {filename}")
            
        except Exception as e:
            failed_count += 1
            print(f"✗ Failed to process {filename}: {str(e)}")
            continue
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Batch processing complete!")
    print(f"Successfully processed: {processed_count} files")
    print(f"Failed: {failed_count} files")
    print(f"Output directory: {output_dir}")
    
    if processed_count > 0:
        print(f"\nProcessed files saved in {output_dir}/:")
        output_files = glob.glob(os.path.join(output_dir, "*.png"))
        for output_file in sorted(output_files):
            print(f"  - {os.path.basename(output_file)}")

if __name__ == "__main__":
    main()
