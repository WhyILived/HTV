#!/usr/bin/env python3
"""
Anti-Collision Process Script
Finds ALL groups of pink colors above a minimum pixel threshold and solidifies them completely.
This is useful for creating anti-collision maps by removing multiple pink areas.
"""

from PIL import Image
from collections import deque
import argparse


def is_pink_color(color, tolerance=100):
    """
    Check if a color is a shade of pink.
    Pink colors typically have high red, medium to high blue, and low to medium green.
    
    Args:
        color (tuple): RGB color (R, G, B)
        tolerance (int): Tolerance for pink detection
    
    Returns:
        bool: True if color is considered pink
    """
    r, g, b = color[:3]
    
    # Ultra lenient pink characteristics to catch maximum variations:
    # - Red component should be reasonably high (> 60)
    # - Green component should be lower than red
    # - Blue component should be reasonably high (> 60)
    # - Red and blue should be dominant over green
    # - Allow for maximum variation in the red-blue relationship
    
    return (r > 60 and 
            b > 60 and 
            r > g and 
            b > g and
            (r + b) > (1.2 * g) and  # Red and blue combined should be higher than green
            abs(r - b) <= tolerance * 5)  # Allow maximum variation between red and blue


def find_all_pink_groups(img, tolerance=100, min_pixels=1000):
    """
    Find ALL connected groups of pink colors above the minimum pixel threshold.
    
    Args:
        img (PIL.Image): Input image
        tolerance (int): Color tolerance for grouping similar pink colors
        min_pixels (int): Minimum number of pixels for a group to be included
    
    Returns:
        list: List of (representative_color, group_size, group_pixels) tuples
    """
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    pixels = img.load()
    visited = [[False for _ in range(width)] for _ in range(height)]
    
    pink_groups = []
    
    def is_pink_pixel(x, y):
        """Check if pixel is pink and not visited"""
        if x < 0 or x >= width or y < 0 or y >= height or visited[y][x]:
            return False
        pixel_color = pixels[x, y]
        return is_pink_color(pixel_color, tolerance)
    
    def flood_fill_pink(start_x, start_y):
        """Flood fill to find size of connected pink region"""
        if not is_pink_pixel(start_x, start_y):
            return 0, []
        
        stack = deque([(start_x, start_y)])
        count = 0
        group_pixels = []
        
        while stack:
            x, y = stack.popleft()
            if visited[y][x] or not is_pink_pixel(x, y):
                continue
            
            visited[y][x] = True
            count += 1
            group_pixels.append((x, y))
            
            # Check 4-connected neighbors (up, down, left, right)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                    if is_pink_pixel(nx, ny):
                        stack.append((nx, ny))
        
        return count, group_pixels
    
    # Find all pink color groups above minimum threshold
    for y in range(height):
        for x in range(width):
            if not visited[y][x] and is_pink_pixel(x, y):
                target_color = pixels[x, y]
                size, group_pixels = flood_fill_pink(x, y)
                
                if size >= min_pixels:  # Only include groups above threshold
                    pink_groups.append((target_color, size, group_pixels))
    
    return pink_groups


def solidify_all_groups(img, pink_groups, solid_color=(255, 255, 255)):
    """
    Solidify all pixels in the specified pink groups.
    
    Args:
        img (PIL.Image): Input image
        pink_groups (list): List of (color, size, pixels) tuples
        solid_color (tuple): Color to use for solidification
    
    Returns:
        PIL.Image: Modified image with all groups solidified
    """
    # Create a copy to avoid modifying the original
    result_img = img.copy()
    if result_img.mode != 'RGB':
        result_img = result_img.convert('RGB')
    
    width, height = result_img.size
    pixels = result_img.load()
    
    # Solidify all pixels in all groups
    total_solidified = 0
    for i, (representative_color, group_size, group_pixels) in enumerate(pink_groups):
        solidified_count = 0
        for x, y in group_pixels:
            if 0 <= x < width and 0 <= y < height:
                pixels[x, y] = solid_color
                solidified_count += 1
        
        total_solidified += solidified_count
        print(f"  Group {i+1}: {solidified_count} pixels (color: {representative_color})")
    
    print(f"Total solidified: {total_solidified} pixels with color {solid_color}")
    return result_img


def process_anti_collision_map(input_file, output_file, tolerance=100, min_pixels=1000, solid_color=(255, 255, 255)):
    """
    Process an image to create an anti-collision map by solidifying ALL pink color groups above threshold.
    
    Args:
        input_file (str): Path to input image
        output_file (str): Path to output image
        tolerance (int): Color tolerance for grouping similar pink colors
        min_pixels (int): Minimum number of pixels for a group to be included
        solid_color (tuple): Color to use for solidification (R, G, B)
    """
    # Load image
    img = Image.open(input_file)
    print(f"Processing: {input_file}")
    print(f"Original size: {img.size}")
    print(f"Original mode: {img.mode}")
    
    # Find all pink color groups above threshold
    print(f"Finding all pink color groups with tolerance ±{tolerance} and minimum {min_pixels} pixels...")
    pink_groups = find_all_pink_groups(img, tolerance, min_pixels)
    
    if not pink_groups:
        print(f"Warning: No pink color groups found with minimum {min_pixels} pixels!")
        return False
    
    print(f"Found {len(pink_groups)} pink groups above threshold:")
    total_pixels = 0
    for i, (representative_color, group_size, group_pixels) in enumerate(pink_groups):
        percentage = (group_size / (img.size[0] * img.size[1]) * 100)
        print(f"  Group {i+1}: {group_size} pixels ({percentage:.1f}%) - color: {representative_color}")
        total_pixels += group_size
    
    total_percentage = (total_pixels / (img.size[0] * img.size[1]) * 100)
    print(f"Total pixels to solidify: {total_pixels} ({total_percentage:.1f}% of image)")
    
    # Solidify all pink color groups
    print(f"Solidifying all groups with color {solid_color}...")
    result_img = solidify_all_groups(img, pink_groups, solid_color)
    
    # Save result
    result_img.save(output_file)
    print(f"Saved anti-collision map: {output_file}")
    print(f"Output size: {result_img.size}")
    print(f"Output mode: {result_img.mode}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Create anti-collision maps by solidifying ALL pink color groups above threshold')
    parser.add_argument('input', help='Input image file path')
    parser.add_argument('-o', '--output', help='Output image file path (default: input_anti_collision.png)')
    parser.add_argument('-t', '--tolerance', type=int, default=100, 
                       help='Color tolerance for grouping similar pink colors (default: 100)')
    parser.add_argument('-m', '--min-pixels', type=int, default=1000,
                       help='Minimum number of pixels for a group to be included (default: 1000)')
    parser.add_argument('-c', '--color', nargs=3, type=int, metavar=('R', 'G', 'B'),
                       default=[255, 255, 255], help='Solid color RGB values (default: 255 255 255)')
    
    args = parser.parse_args()
    
    # Set default output filename if not provided
    if args.output is None:
        input_path = args.input
        if '.' in input_path:
            name, ext = input_path.rsplit('.', 1)
            args.output = f"{name}_anti_collision.{ext}"
        else:
            args.output = f"{input_path}_anti_collision.png"
    
    # Process the image
    success = process_anti_collision_map(
        input_file=args.input,
        output_file=args.output,
        tolerance=args.tolerance,
        min_pixels=args.min_pixels,
        solid_color=tuple(args.color)
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
