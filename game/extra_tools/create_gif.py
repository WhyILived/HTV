#!/usr/bin/env python3
"""
GIF Creator Script
Creates animated GIFs from a collection of images with various customization options.
"""

import os
import sys
import glob
from PIL import Image, ImageSequence
import argparse
from pathlib import Path


def get_image_files(directory, extensions=None):
    """
    Get all image files from a directory.
    
    Args:
        directory (str): Path to directory containing images
        extensions (list): List of file extensions to include (default: common image formats)
    
    Returns:
        list: Sorted list of image file paths
    """
    if extensions is None:
        extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
    
    image_files = []
    for ext in extensions:
        pattern = os.path.join(directory, f"*{ext}")
        image_files.extend(glob.glob(pattern))
        pattern = os.path.join(directory, f"*{ext.upper()}")
        image_files.extend(glob.glob(pattern))
    
    # Remove duplicates and sort
    return sorted(list(set(image_files)))


def resize_images(images, max_size=None, target_size=None):
    """
    Resize images to a consistent size.
    
    Args:
        images (list): List of PIL Image objects
        max_size (tuple): Maximum size (width, height) - maintains aspect ratio
        target_size (tuple): Exact target size (width, height)
    
    Returns:
        list: List of resized PIL Image objects
    """
    if not images:
        return images
    
    resized_images = []
    
    for img in images:
        if target_size:
            # Resize to exact target size
            resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
        elif max_size:
            # Resize maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            resized_img = img
        else:
            resized_img = img
        
        resized_images.append(resized_img)
    
    return resized_images


def create_gif(image_paths, output_path, duration=500, loop=0, resize_mode=None, 
               max_size=None, target_size=None, optimize=True, quality=85):
    """
    Create a GIF from a list of image files.
    
    Args:
        image_paths (list): List of paths to image files
        output_path (str): Path where the GIF will be saved
        duration (int): Duration of each frame in milliseconds
        loop (int): Number of loops (0 = infinite)
        resize_mode (str): 'max' for max_size, 'target' for target_size, None for no resize
        max_size (tuple): Maximum size (width, height) for resize_mode='max'
        target_size (tuple): Target size (width, height) for resize_mode='target'
        optimize (bool): Whether to optimize the GIF
        quality (int): Quality for optimization (1-100)
    """
    if not image_paths:
        print("Error: No image files found!")
        return False
    
    print(f"Found {len(image_paths)} images")
    print("Loading images...")
    
    # Load images
    images = []
    for i, path in enumerate(image_paths):
        try:
            img = Image.open(path)
            # Convert to RGB if necessary (GIFs don't support RGBA)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            images.append(img)
            print(f"  Loaded: {os.path.basename(path)} ({img.size[0]}x{img.size[1]})")
        except Exception as e:
            print(f"  Error loading {path}: {e}")
            continue
    
    if not images:
        print("Error: No valid images could be loaded!")
        return False
    
    # Resize images if requested
    if resize_mode == 'max' and max_size:
        print(f"Resizing images to max size: {max_size}")
        images = resize_images(images, max_size=max_size)
    elif resize_mode == 'target' and target_size:
        print(f"Resizing images to target size: {target_size}")
        images = resize_images(images, target_size=target_size)
    
    # Create GIF
    print(f"Creating GIF with {len(images)} frames...")
    print(f"  Duration per frame: {duration}ms")
    print(f"  Loops: {'infinite' if loop == 0 else loop}")
    
    try:
        # Save as GIF
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=loop,
            optimize=optimize,
            quality=quality
        )
        
        # Get file size
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"GIF created successfully: {output_path}")
        print(f"  File size: {file_size_mb:.2f} MB")
        print(f"  Dimensions: {images[0].size[0]}x{images[0].size[1]}")
        print(f"  Total duration: {len(images) * duration / 1000:.1f} seconds")
        
        return True
        
    except Exception as e:
        print(f"Error creating GIF: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Create animated GIFs from images')
    parser.add_argument('input', help='Input directory or comma-separated list of image files')
    parser.add_argument('-o', '--output', default='output.gif', help='Output GIF file path')
    parser.add_argument('-d', '--duration', type=int, default=500, help='Duration per frame in milliseconds (default: 500)')
    parser.add_argument('-l', '--loop', type=int, default=0, help='Number of loops (0 = infinite, default: 0)')
    parser.add_argument('--max-size', type=int, nargs=2, metavar=('WIDTH', 'HEIGHT'), 
                       help='Maximum size (maintains aspect ratio)')
    parser.add_argument('--target-size', type=int, nargs=2, metavar=('WIDTH', 'HEIGHT'),
                       help='Exact target size')
    parser.add_argument('--no-optimize', action='store_true', help='Disable GIF optimization')
    parser.add_argument('--quality', type=int, default=85, help='Quality for optimization (1-100, default: 85)')
    parser.add_argument('--extensions', nargs='+', 
                       default=['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'],
                       help='File extensions to include')
    
    args = parser.parse_args()
    
    # Determine input files
    if ',' in args.input:
        # Comma-separated list of files
        image_paths = [path.strip() for path in args.input.split(',')]
        # Check if files exist
        valid_paths = []
        for path in image_paths:
            if os.path.exists(path):
                valid_paths.append(path)
            else:
                print(f"Warning: File not found: {path}")
        image_paths = valid_paths
    else:
        # Directory
        if not os.path.isdir(args.input):
            print(f"Error: Directory not found: {args.input}")
            return 1
        
        image_paths = get_image_files(args.input, args.extensions)
    
    if not image_paths:
        print("Error: No image files found!")
        return 1
    
    # Determine resize mode
    resize_mode = None
    if args.max_size:
        resize_mode = 'max'
    elif args.target_size:
        resize_mode = 'target'
    
    # Create GIF
    success = create_gif(
        image_paths=image_paths,
        output_path=args.output,
        duration=args.duration,
        loop=args.loop,
        resize_mode=resize_mode,
        max_size=tuple(args.max_size) if args.max_size else None,
        target_size=tuple(args.target_size) if args.target_size else None,
        optimize=not args.no_optimize,
        quality=args.quality
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
