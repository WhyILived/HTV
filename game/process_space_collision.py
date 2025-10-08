#!/usr/bin/env python3
"""
High-Tolerance Collision Processor for Background Space Key
Processes background_space_key.png with very high tolerance for collision detection.
This creates a more forgiving collision system that handles color variations and noise.
"""

import pygame
import os
from typing import Tuple, List, Set
import numpy as np

def color_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """Calculate Euclidean distance between two RGB colors"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))

def is_color_similar(color1: Tuple[int, int, int], color2: Tuple[int, int, int], tolerance: int) -> bool:
    """Check if two colors are similar within tolerance"""
    return color_distance(color1, color2) <= tolerance

def process_background_collision_with_tolerance(
    input_path: str, 
    output_path: str, 
    walkable_color: Tuple[int, int, int] = (234, 0, 249),
    tolerance: int = 50,
    min_group_size: int = 100
) -> bool:
    """
    Process background collision map with high tolerance for color variations.
    
    Args:
        input_path: Path to the background space key image
        output_path: Path to save the processed collision map
        walkable_color: The target walkable color to match
        tolerance: Color tolerance for matching (higher = more forgiving)
        min_group_size: Minimum number of pixels to consider a valid walkable area
    
    Returns:
        bool: True if processing was successful
    """
    try:
        # Load the image
        if not os.path.exists(input_path):
            print(f"Error: Input file {input_path} not found")
            return False
        
        # Load with pygame for consistency with game
        surface = pygame.image.load(input_path)
        width, height = surface.get_size()
        
        print(f"Processing {input_path}")
        print(f"Image size: {width}x{height}")
        print(f"Target walkable color: {walkable_color}")
        print(f"Tolerance: {tolerance}")
        print(f"Min group size: {min_group_size}")
        
        # Create output surface
        output_surface = pygame.Surface((width, height))
        output_surface.fill((0, 0, 0))  # Start with black (non-walkable)
        
        # Find all pixels that match the walkable color within tolerance
        walkable_pixels = set()
        total_pixels = width * height
        processed_pixels = 0
        
        print("Scanning for walkable pixels...")
        
        for y in range(height):
            for x in range(width):
                pixel_color = surface.get_at((x, y))[:3]  # Get RGB (ignore alpha)
                
                if is_color_similar(pixel_color, walkable_color, tolerance):
                    walkable_pixels.add((x, y))
                
                processed_pixels += 1
                if processed_pixels % (total_pixels // 10) == 0:
                    print(f"Progress: {(processed_pixels / total_pixels * 100):.1f}%")
        
        print(f"Found {len(walkable_pixels)} walkable pixels")
        
        # Group connected walkable pixels
        print("Grouping connected walkable areas...")
        groups = []
        visited = set()
        
        def flood_fill(start_x: int, start_y: int) -> Set[Tuple[int, int]]:
            """Flood fill to find connected pixels"""
            group = set()
            stack = [(start_x, start_y)]
            
            while stack:
                x, y = stack.pop()
                if (x, y) in visited or (x, y) not in walkable_pixels:
                    continue
                
                visited.add((x, y))
                group.add((x, y))
                
                # Check 8-connected neighbors
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < width and 0 <= ny < height and 
                            (nx, ny) not in visited and (nx, ny) in walkable_pixels):
                            stack.append((nx, ny))
            
            return group
        
        # Find all groups
        for x, y in walkable_pixels:
            if (x, y) not in visited:
                group = flood_fill(x, y)
                if len(group) >= min_group_size:
                    groups.append(group)
        
        print(f"Found {len(groups)} valid walkable groups")
        
        # Create the final collision map
        print("Creating final collision map...")
        
        # Set all walkable areas to the target color
        for group in groups:
            for x, y in group:
                output_surface.set_at((x, y), walkable_color)
        
        # Save the processed image
        pygame.image.save(output_surface, output_path)
        print(f"Saved processed collision map to {output_path}")
        
        # Print statistics
        total_walkable = sum(len(group) for group in groups)
        coverage = (total_walkable / total_pixels) * 100
        print(f"Final statistics:")
        print(f"  Total walkable pixels: {total_walkable}")
        print(f"  Coverage: {coverage:.1f}%")
        print(f"  Number of walkable areas: {len(groups)}")
        
        return True
        
    except Exception as e:
        print(f"Error processing collision map: {e}")
        return False

def create_enhanced_collision_detector(tolerance: int = 50):
    """
    Create an enhanced collision detection function with high tolerance.
    
    Args:
        tolerance: Color tolerance for collision detection
    
    Returns:
        function: Enhanced collision detection function
    """
    def enhanced_is_position_walkable(
        pos: Tuple[int, int], 
        color_key_surface: pygame.Surface, 
        walkable_color: Tuple[int, int, int]
    ) -> bool:
        """
        Enhanced position walkability check with high tolerance.
        
        Args:
            pos: Position to check (x, y)
            color_key_surface: The collision map surface
            walkable_color: Target walkable color
        
        Returns:
            bool: True if position is walkable
        """
        x, y = pos
        if 0 <= x < color_key_surface.get_width() and 0 <= y < color_key_surface.get_height():
            pixel_color = color_key_surface.get_at((x, y))[:3]
            return is_color_similar(pixel_color, walkable_color, tolerance)
        return False
    
    return enhanced_is_position_walkable

def main():
    """Main function to process the background space key"""
    input_file = "assets/background_space_key.png"
    output_file = "assets/background_space_key_processed.png"
    
    # Process with high tolerance
    #something
    success = process_background_collision_with_tolerance(
        input_file,
        output_file,
        walkable_color=(234, 0, 249),
        tolerance=80,  # High tolerance for forgiving collision detection
        min_group_size=50  # Smaller minimum group size
    )
    
    if success:
        print("SUCCESS: Collision processing completed successfully!")
        print(f"Processed file saved as: {output_file}")
        print("You can now use this processed file in your game for more forgiving collision detection.")
    else:
        print("ERROR: Collision processing failed!")

if __name__ == "__main__":
    import math
    main()
