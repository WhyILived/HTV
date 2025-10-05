from PIL import Image
from collections import deque

def process_sprite(input_file, output_file, target_size=(256, 384)):
    """
    Complete sprite processing: crop to correct aspect ratio, downscale, and remove background.
    """
    # Load original image
    img = Image.open(input_file)
    print(f"Original: {img.size} (aspect ratio: {img.size[0]/img.size[1]:.3f})")
    
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
    
    # Remove background using largest white region
    width, height = downscaled_img.size
    pixels = downscaled_img.load()
    white_threshold = 200
    
    # Find largest white region (background)
    visited = [[False for _ in range(width)] for _ in range(height)]
    largest_region = (0, 0, 0)
    
    def is_white(x, y):
        if x < 0 or x >= width or y < 0 or y >= height or visited[y][x]:
            return False
        r, g, b, a = pixels[x, y]
        return r >= white_threshold and g >= white_threshold and b >= white_threshold
    
    def flood_fill_size(start_x, start_y):
        if not is_white(start_x, start_y):
            return 0
        stack = deque([(start_x, start_y)])
        count = 0
        while stack:
            x, y = stack.popleft()
            if visited[y][x] or not is_white(x, y):
                continue
            visited[y][x] = True
            count += 1
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                    if is_white(nx, ny):
                        stack.append((nx, ny))
        return count
    
    # Find all white regions
    for y in range(height):
        for x in range(width):
            if not visited[y][x] and is_white(x, y):
                size = flood_fill_size(x, y)
                if size > largest_region[2]:
                    largest_region = (x, y, size)
    
    print(f"Found background region: {largest_region[2]} pixels")
    
    # Remove background
    visited = [[False for _ in range(width)] for _ in range(height)]
    def flood_fill_remove(start_x, start_y):
        stack = deque([(start_x, start_y)])
        while stack:
            x, y = stack.popleft()
            if visited[y][x] or not is_white(x, y):
                continue
            visited[y][x] = True
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                    if is_white(nx, ny):
                        stack.append((nx, ny))
    
    flood_fill_remove(largest_region[0], largest_region[1])
    
    # Make background transparent
    for y in range(height):
        for x in range(width):
            if visited[y][x]:
                r, g, b, a = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)
    
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
    
    # For each edge pixel, make it and its neighbors within 2 pixels green
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
    process_sprite("pictures/1m.png", "pictures/m2.png")
