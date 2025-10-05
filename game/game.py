import json
import os
import random
import pygame
import math
from typing import Dict, List, Any, Optional, Tuple

# ---------- CONFIG ----------
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 500
FPS = 30
PLAYER_SPEED = 250
NPC_SIZE = (36, 48)
PLAYER_SIZE = (36, 48)
WORLD_BOUNDS = pygame.Rect(0, 0, 1000, 700)  # Smaller world
INTERACT_DISTANCE = 48
MINIMAP_SIZE = 150
MINIMAP_POS = (WINDOW_WIDTH - MINIMAP_SIZE - 10, 10)
BACKGROUND = pygame.image.load("assets/background2.png")
BACKGROUND_COLOR_KEY = pygame.image.load("assets/background_color_key2.png")
WALKABLE_COLOR = (234, 0, 255)
CURRENT_DIALOGUE = ""
DIALOGUE_TIMER = 0.0
DIALOGUE_QUEUE = []

WHITE = (255, 255, 255)
BLUE = (100, 150, 255)
GREEN = (50, 200, 100)
RED = (255, 80, 80)

# Particle colors - autumn-like colors for leaf effect
PARTICLE_COLORS = [
    (255, 140, 0),   # Orange
    (255, 69, 0),    # Red-orange
    (255, 215, 0),   # Gold
    (255, 165, 0),   # Orange
    (255, 20, 147),  # Deep pink
    (50, 205, 50),   # Lime green
    (255, 192, 203), # Pink
    (255, 160, 122), # Light salmon
]

# ---------- SAMPLE DATA ----------
SAMPLE_DATA = {
    "game": {"title": "Frostvale Chronicles"},
    "main_character": {"name": "Elise"},
    "characters": {"items": [
        {"id":"lucinda","name":"Lucinda","role":"Ally","description":"Helpful sorceress."},
        {"id":"vornir","name":"Vornir","role":"Antagonist","description":"Ice king."},
        {"id":"frost_guardian","name":"Frost Guardian","role":"Antagonist","description":"Ancient ice guardian."}
    ]},
    "scenes": {"items": [
        {"id":1,"title":"Frozen Citadel","setting":"Elise enters the citadel.","characters":["vornir","frost_guardian"]},
        {"id":2,"title":"Blizzard Peak","setting":"Elise climbs the peak.","characters":["lucinda"]}
    ]}
}

# ---------- UTILITIES ----------
def is_position_walkable(pos: Tuple[int, int], color_key_surface, walkable_color: Tuple[int, int, int]) -> bool:
    """Check if a position is on a walkable color in the color key surface"""
    x, y = pos
    if 0 <= x < color_key_surface.get_width() and 0 <= y < color_key_surface.get_height():
        pixel_color = color_key_surface.get_at((x, y))
        # Compare RGB values (ignore alpha)
        return pixel_color[:3] != walkable_color
    return False

def load_storyline(filename="storyline.json") -> Dict[str, Any]:
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[INFO] Loaded storyline from {filename}")
            print(f"[DEBUG] Scenes in loaded data: {len(data.get('scenes', []))}")
            return data
        except Exception as e:
            print(f"[WARN] Failed to load {filename}: {e}")
    print("[INFO] Using SAMPLE_DATA.")
    return SAMPLE_DATA

# ---------- PARTICLE SYSTEM ----------
class Particle:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.vx = random.uniform(-20, 20)  # Random horizontal drift
        self.vy = random.uniform(10, 30)   # Falling speed
        self.color = color
        self.life = 1.0
        self.decay = random.uniform(0.005, 0.015)  # How fast it fades
        self.size = random.uniform(2, 5)  # Random size
        self.rotation = 0
        self.rotation_speed = random.uniform(-2, 2)  # Gentle rotation
    
    def update(self, dt: float):
        # Apply gravity
        self.vy += 50 * dt  # Gravity acceleration
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Update rotation
        self.rotation += self.rotation_speed * dt
        
        # Fade out
        self.life -= self.decay * dt
        
        # Add some wind effect (slight horizontal drift)
        self.vx += random.uniform(-5, 5) * dt
        self.vx = max(-30, min(30, self.vx))  # Limit wind speed
    
    def is_alive(self) -> bool:
        return self.life > 0 and self.y < WINDOW_HEIGHT + 50
    
    def draw(self, screen: pygame.Surface, camera_offset: Tuple[int, int]):
        if self.life <= 0:
            return
        
        # Calculate screen position
        screen_x = int(self.x - camera_offset[0])
        screen_y = int(self.y - camera_offset[1])
        
        # Skip if off-screen
        if screen_x < -10 or screen_x > WINDOW_WIDTH + 10 or screen_y < -10 or screen_y > WINDOW_HEIGHT + 10:
            return
        
        # Create color with alpha based on life
        alpha = int(255 * self.life)
        color_with_alpha = (*self.color, alpha)
        
        # Draw particle as a small circle or rotated rectangle (leaf-like)
        if random.random() < 0.7:  # 70% chance to be a circle
            pygame.draw.circle(screen, self.color, (screen_x, screen_y), int(self.size))
        else:  # 30% chance to be a small rectangle (leaf-like)
            # Create a small surface for rotation
            leaf_surface = pygame.Surface((int(self.size * 2), int(self.size)), pygame.SRCALPHA)
            leaf_surface.fill(color_with_alpha)
            # Rotate the leaf
            rotated_leaf = pygame.transform.rotate(leaf_surface, self.rotation)
            leaf_rect = rotated_leaf.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated_leaf, leaf_rect)

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []
        self.spawn_timer = 0.0
        self.spawn_rate = 0.1  # Spawn a particle every 0.1 seconds
        self.max_particles = 100  # Limit particles for performance
    
    def update(self, dt: float):
        # Spawn new particles
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_rate and len(self.particles) < self.max_particles:
            # Spawn particle at random position along the top of the screen
            x = random.uniform(-50, WINDOW_WIDTH + 50)
            y = -20  # Start above the screen
            color = random.choice(PARTICLE_COLORS)
            self.particles.append(Particle(x, y, color))
            self.spawn_timer = 0.0
        
        # Update existing particles
        for particle in self.particles[:]:  # Use slice to avoid modification during iteration
            particle.update(dt)
            if not particle.is_alive():
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface, camera_offset: Tuple[int, int]):
        for particle in self.particles:
            particle.draw(screen, camera_offset)
    
    def clear(self):
        """Clear all particles"""
        self.particles.clear()

# ---------- ENTITIES ----------
class Entity:
    def __init__(self, name: str, rect: pygame.Rect, color: Tuple[int,int,int]=(200,200,200)):
        self.name = name
        self.rect = rect
        self.color = color
    def draw(self, surf, cam):
        r = self.rect.move(-cam[0], -cam[1])
        pygame.draw.rect(surf, self.color, r)

class Player(Entity):
    def __init__(self, data: Dict[str, Any], pos: Tuple[int,int]):
        w,h = PLAYER_SIZE
        print("PLAYER NAME:", data)
        super().__init__(data.get("main_character").get("name", "Player"), pygame.Rect(pos[0], pos[1], w,h), BLUE)
        self.speed = PLAYER_SPEED
    def update(self, dt, obstacles, color_key_surface=None):
        keys = pygame.key.get_pressed()
        vx = vy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: vx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: vx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: vy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: vy += 1
        v = pygame.Vector2(vx, vy)
        if v.length_squared()>0: v = v.normalize() * self.speed
        
        # Check horizontal movement
        new_rect = self.rect.copy()
        new_rect.x += int(v.x*dt)
        if not any(new_rect.colliderect(o) for o in obstacles) and WORLD_BOUNDS.contains(new_rect):
            # Check if new position is on walkable color
            if color_key_surface is None or self._is_rect_walkable(new_rect, color_key_surface):
                self.rect = new_rect
        
        # Check vertical movement
        new_rect = self.rect.copy()
        new_rect.y += int(v.y*dt)
        if not any(new_rect.colliderect(o) for o in obstacles) and WORLD_BOUNDS.contains(new_rect):
            # Check if new position is on walkable color
            if color_key_surface is None or self._is_rect_walkable(new_rect, color_key_surface):
                self.rect = new_rect
    
    def _is_rect_walkable(self, rect, color_key_surface):
        """Check if a rectangle is on walkable terrain by sampling multiple points"""
        # Sample points around the player's feet and center
        sample_points = [
            (rect.centerx, rect.bottom - 5),  # Bottom center
            (rect.left + 5, rect.bottom - 5),  # Bottom left
            (rect.right - 5, rect.bottom - 5),  # Bottom right
            (rect.centerx, rect.centery),  # Center
        ]
        
        # Check if at least 3 out of 4 sample points are walkable
        walkable_count = 0
        for point in sample_points:
            if is_position_walkable(point, color_key_surface, WALKABLE_COLOR):
                walkable_count += 1
        
        return walkable_count >= 3

class NPC(Entity):
    def __init__(self, data: Dict[str, Any], pos: Tuple[int,int]):
        w,h = NPC_SIZE
        role = data.get("role","").lower()
        color = RED if "antagonist" in role or "outlaw" in role else GREEN
        super().__init__(data.get("name","NPC"), pygame.Rect(pos[0],pos[1],w,h), color)
        self.data = data

# ---------- GAME LOGIC ----------
def handle_interaction(player: Player, npc: NPC):
    name = npc.data.get("name", npc.name)
    role = npc.data.get("role","Unknown")
    desc = npc.data.get("description","")
    print(f"[INTERACT] {player.name} interacts with {name} ({role}): {desc}")
    return f"{name} ({role}): {desc}"

def show_interaction_menu(screen, font, npc_name, npc_role):
    """Show interaction menu with options"""
    menu_rect = pygame.Rect(50, WINDOW_HEIGHT - 200, WINDOW_WIDTH - 100, 150)
    
    # Draw menu background
    s = pygame.Surface((menu_rect.w, menu_rect.h), pygame.SRCALPHA)
    s.fill((10, 10, 20, 240))
    screen.blit(s, (menu_rect.x, menu_rect.y))
    pygame.draw.rect(screen, WHITE, menu_rect, 2)
    
    # Title
    title_text = font.render(f"Interacting with {npc_name} ({npc_role})", True, WHITE)
    screen.blit(title_text, (menu_rect.x + 10, menu_rect.y + 10))
    
    # Options
    options = [
        ("1 - Talk", "Press 1 to talk"),
        ("2 - Fight", "Press 2 to fight"), 
        ("3 - Flee", "Press 3 to flee")
    ]
    
    for i, (option, desc) in enumerate(options):
        y_pos = menu_rect.y + 40 + i * 30
        option_text = font.render(option, True, WHITE)
        desc_text = font.render(desc, True, (200, 200, 200))
        screen.blit(option_text, (menu_rect.x + 20, y_pos))
        screen.blit(desc_text, (menu_rect.x + 150, y_pos))

def update_dialogue(dt):
    """Updates the dialogue timer and moves to next line when time expires."""
    global CURRENT_DIALOGUE, DIALOGUE_TIMER, DIALOGUE_QUEUE

    if DIALOGUE_TIMER > 0:
        DIALOGUE_TIMER -= dt
    elif DIALOGUE_QUEUE:
        CURRENT_DIALOGUE, DIALOGUE_TIMER = DIALOGUE_QUEUE.pop(0)
    else:
        CURRENT_DIALOGUE = ""

def display_text(dialogue, seconds=3):
    """
    Displays dialogue lines one after another.
    - If given a list, cycles through them.
    - Each line lasts 'seconds' unless a tuple (line, custom_seconds) is given.
    """
    global DIALOGUE_QUEUE, CURRENT_DIALOGUE, DIALOGUE_TIMER

    DIALOGUE_QUEUE = []  # reset queue

    # Normalize input
    if isinstance(dialogue, str):
        DIALOGUE_QUEUE.append((dialogue, seconds))
    elif isinstance(dialogue, list):
        for item in dialogue:
            if isinstance(item, tuple):
                DIALOGUE_QUEUE.append(item)
            else:
                DIALOGUE_QUEUE.append((str(item), seconds))
    else:
        DIALOGUE_QUEUE.append((str(dialogue), seconds))

    # Start with the first line
    if DIALOGUE_QUEUE:
        CURRENT_DIALOGUE, DIALOGUE_TIMER = DIALOGUE_QUEUE.pop(0)

def handle_interaction_choice(choice, player, npc):
    """Handle the player's interaction choice"""
    name = npc.data.get("name", npc.name)
    role = npc.data.get("role", "Unknown")
    print(npc.data)
    dialogue = npc.data.get("dialogue", "Unknown")
    print(dialogue)
    
    if choice == 1:  # Talk
        display_text(dialogue, 3)
        return f"Talked to {name}"
        
    elif choice == 2:  # Fight
        print(f"[FIGHT] {player.name} prepares to fight {name}")
        if "antagonist" in role.lower() or "enemy" in role.lower():
            print(f"[FIGHT] {name} snarls: 'Finally! Let's settle this!'")
        else:
            print(f"[FIGHT] {name} looks shocked: 'Why are you attacking me?!'")
        return f"Fought {name}"
        
    elif choice == 3:  # Flee
        print(f"[FLEE] {player.name} decides to flee from {name}")
        if "antagonist" in role.lower() or "enemy" in role.lower():
            print(f"[FLEE] {name} calls after you: 'Running away? How cowardly!'")
        else:
            print(f"[FLEE] {name} waves: 'Come back when you're ready to talk!'")
        return f"Fled from {name}"
    
    return "Invalid choice"

def check_scene_triggers(player: Player, scenes: List[Dict[str,Any]]) -> Optional[Dict[str,Any]]:
    if player.rect.centerx > WORLD_BOUNDS.width - 300:
        return scenes[0] if scenes else None
    return None

def get_characters_for_scene(scene, all_characters):
    """Get character data for a specific scene based on character names"""
    scene_characters = []
    if not scene or "characters" not in scene:
        print(f"[DEBUG] No scene or no characters in scene: {scene}")
        return scene_characters
    
    print(f"[DEBUG] Scene has {len(scene.get('characters', []))} character Names: {scene.get('characters', [])}")
    print(f"[DEBUG] Available characters: {[c.get('name', 'no-name') for c in all_characters]}")
    
    # Create a lookup dictionary for all characters
    char_lookup = {}
    for char in all_characters:
        print("CHAR: ", char)
        char_lookup[char.get("name", "")] = char
    
    # Get characters for this scene
    for char_name in scene.get("characters", []):
        if char_name in char_lookup:
            scene_characters.append(char_lookup[char_name])
            print(f"[DEBUG] Found character: {char_name}")
        else:
            print(f"[DEBUG] Character not found: {char_name}")
    
    return scene_characters

def switch_to_scene(scene_index, scenes, player, obstacles, npcs, all_characters):
    """Switch to a specific scene and reset world state"""
    if not scenes or scene_index < 0 or scene_index >= len(scenes):
        return False
    
    # Reset player position to center
    player.rect.centerx = WORLD_BOUNDS.centerx
    player.rect.centery = WORLD_BOUNDS.centery
    
    # Get characters for this specific scene
    current_scene = scenes[scene_index]
    scene_chars = get_characters_for_scene(current_scene, all_characters)
    
    # Regenerate NPCs in safe positions using scene-specific characters
    npcs.clear()
    for c in scene_chars:
        x, y = find_safe_spawn_position(obstacles, player.rect)
        npcs.append(NPC(c, (x, y)))
    
    return True

def draw_scene_intro(screen, scene, timer):
    """Draw scene introduction overlay"""
    if not scene or timer <= 0:
        return
    
    # # Semi-transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    # Scene title
    title_font = pygame.font.SysFont(None, 48)
    title_text = title_font.render(scene.get("title", "Unknown Scene"), True, WHITE)
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
    screen.blit(title_text, title_rect)
    
    # Scene description
    desc_font = pygame.font.SysFont(None, 24)
    desc_text = desc_font.render(scene.get("setting", "A mysterious place"), True, WHITE)
    desc_rect = desc_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 20))
    screen.blit(desc_text, desc_rect)
    
    # Instructions
    inst_font = pygame.font.SysFont(None, 20)
    inst_text = inst_font.render("Press any key to continue...", True, (200, 200, 200))
    inst_rect = inst_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 80))
    screen.blit(inst_text, inst_rect)

def find_safe_spawn_position(obstacles, player_rect, min_distance=100):
    """Find a safe position for spawning NPCs that doesn't overlap with obstacles or player"""
    for _ in range(100):  # Try up to 100 times
        x = random.randint(50, WORLD_BOUNDS.width - 100)
        y = random.randint(50, WORLD_BOUNDS.height - 100)
        test_rect = pygame.Rect(x, y, NPC_SIZE[0], NPC_SIZE[1])
        
        # Check if position is safe
        safe = True
        if test_rect.colliderect(player_rect.inflate(min_distance, min_distance)):
            safe = False
        
        if 0 <= x < BACKGROUND_COLOR_KEY.get_width() and 0 <= y < BACKGROUND_COLOR_KEY.get_height():
            pixel_color = BACKGROUND_COLOR_KEY.get_at((x, y))
            # Compare RGB values (ignore alpha)
            if pixel_color[:3] != WALKABLE_COLOR:
                safe = True
            else:
                safe = False
        
        if safe:
            return (x, y)
    
    # Fallback: return a position far from player
    return (player_rect.x + 200, player_rect.y + 200)

def draw_minimap(screen, player, npcs, obstacles, cam):
    """Draw minimap showing player, NPCs, and obstacles"""
    minimap_rect = pygame.Rect(MINIMAP_POS[0], MINIMAP_POS[1], MINIMAP_SIZE, MINIMAP_SIZE)
    
    # Draw minimap background
    pygame.draw.rect(screen, (20, 20, 30), minimap_rect)
    pygame.draw.rect(screen, WHITE, minimap_rect, 2)
    
    # Scale factor for world to minimap
    scale_x = MINIMAP_SIZE / WORLD_BOUNDS.width
    scale_y = MINIMAP_SIZE / WORLD_BOUNDS.height
    
    # Draw obstacles on minimap
    for obstacle in obstacles:
        mini_x = minimap_rect.x + int(obstacle.x * scale_x)
        mini_y = minimap_rect.y + int(obstacle.y * scale_y)
        mini_w = max(1, int(obstacle.width * scale_x))
        mini_h = max(1, int(obstacle.height * scale_y))
        pygame.draw.rect(screen, (100, 100, 100), (mini_x, mini_y, mini_w, mini_h))
    
    # Draw NPCs on minimap
    for npc in npcs:
        mini_x = minimap_rect.x + int(npc.rect.centerx * scale_x)
        mini_y = minimap_rect.y + int(npc.rect.centery * scale_y)
        pygame.draw.circle(screen, npc.color, (mini_x, mini_y), 2)
    
    # Draw player on minimap
    player_x = minimap_rect.x + int(player.rect.centerx * scale_x)
    player_y = minimap_rect.y + int(player.rect.centery * scale_y)
    pygame.draw.circle(screen, BLUE, (player_x, player_y), 3)
    
    # Draw camera view indicator
    cam_x = minimap_rect.x + int(cam[0] * scale_x)
    cam_y = minimap_rect.y + int(cam[1] * scale_y)
    cam_w = int(WINDOW_WIDTH * scale_x)
    cam_h = int(WINDOW_HEIGHT * scale_y)
    pygame.draw.rect(screen, (255, 255, 0), (cam_x, cam_y, cam_w, cam_h), 1)

# ---------- MAIN GAME ----------
def run_game(storyline):
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
    pygame.display.set_caption(storyline.get("game",{}).get("title","RPG"))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)
    bigfont = pygame.font.SysFont(None, 28)

    # Obstacles - positioned to avoid player spawn area
    obstacles = [
        # pygame.Rect(500, 300, 150, 20),   # Moved away from center
        # pygame.Rect(200, 500, 30, 200),   # Moved away from center  
        # pygame.Rect(800, 200, 100, 30),   # Moved away from center
        # pygame.Rect(100, 100, 80, 80),    # Corner obstacle
        # pygame.Rect(1000, 1000, 100, 100) # Far corner obstacle
    ]

    # Player
    player = Player(storyline.get("main_character",{}), (WORLD_BOUNDS.centerx,WORLD_BOUNDS.centery))

    # Load all characters from storyline
    all_chars_section = storyline.get("characters",{})
    all_chars = []
    if isinstance(all_chars_section, dict):
        all_chars_section = all_chars_section["characters"]
    if not all_chars: all_chars = all_chars_section
    print("ALL CHARS", all_chars)

    # Scenes
    scenes_section = storyline.get("scenes",{})
    scenes = []
    if isinstance(scenes_section, dict):
        print("YES")
        scenes = scenes_section["scenes"]
        print(scenes)
    if not scenes: 
        print("[DEBUG] Using SAMPLE_DATA scenes")
        scenes = SAMPLE_DATA["scenes"]["items"]
    else:
        print(f"[DEBUG] Using loaded scenes: {len(scenes)} scenes")
    
    # NPCs - start with characters from first scene
    npcs = []
    if scenes and len(scenes) > 0:
        scene_chars = get_characters_for_scene(scenes[0], all_chars)
        print(f"[DEBUG] Scene 0: {scenes[0].get('title', 'Unknown')}")
        print(f"[DEBUG] Scene characters: {scenes[0].get('characters', [])}")
        print(f"[DEBUG] Found {len(scene_chars)} characters for scene")
        for c in scene_chars:
            print(f"[DEBUG] Creating NPC: {c.get('name', 'Unknown')}")
            x, y = find_safe_spawn_position(obstacles, player.rect)
            npcs.append(NPC(c, (x, y)))
    else:
        # Fallback to all characters if no scenes
        print(f"[DEBUG] No scenes found, using all {len(all_chars)} characters")
        for c in all_chars:
            x, y = find_safe_spawn_position(obstacles, player.rect)
            npcs.append(NPC(c, (x, y)))
    
    print(f"[DEBUG] Total NPCs created: {len(npcs)}")

    # Camera
    cam = [player.rect.centerx - WINDOW_WIDTH//2, player.rect.centery - WINDOW_HEIGHT//2]

    # Particle system
    particle_system = ParticleSystem()

    interaction_text = ""
    interaction_timer = 0.0
    scene_active = None
    showing_interaction_menu = False
    current_interaction_npc = None
    current_scene_index = 0
    show_scene_intro = False
    scene_intro_timer = 0
    scene_intro_can_skip = False
    running = True

    while running:
        dt = clock.tick(FPS)/1000
        for event in pygame.event.get():
            if event.type==pygame.QUIT: running=False
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE: 
                    if showing_interaction_menu:
                        showing_interaction_menu = False
                        current_interaction_npc = None
                    elif show_scene_intro:
                        show_scene_intro = False
                        scene_intro_timer = 0
                    else:
                        running=False
                
                # Scene switching controls (only when not in interaction menu or scene intro)
                if not showing_interaction_menu and not show_scene_intro:
                    if event.key==pygame.K_n:  # Next scene
                        current_scene_index = (current_scene_index + 1) % len(scenes)
                        if switch_to_scene(current_scene_index, scenes, player, obstacles, npcs, all_chars):
                            show_scene_intro = True
                            scene_intro_timer = 180  # 3 seconds at 60 FPS
                            print(f"[SCENE] Switched to scene {current_scene_index + 1}: {scenes[current_scene_index].get('title', 'Unknown')}")
                    
                    elif event.key==pygame.K_b:  # Previous scene
                        current_scene_index = (current_scene_index - 1) % len(scenes)
                        if switch_to_scene(current_scene_index, scenes, player, obstacles, npcs, all_chars):
                            show_scene_intro = True
                            scene_intro_timer = 180  # 3 seconds at 60 FPS
                            print(f"[SCENE] Switched to scene {current_scene_index + 1}: {scenes[current_scene_index].get('title', 'Unknown')}")
                    
                    elif event.key==pygame.K_e:  # Normal interaction
                        nearest = None
                        nearest_dist = 1e9
                        for npc in npcs:
                            dist = (player.rect.centerx - npc.rect.centerx)**2 + (player.rect.centery - npc.rect.centery)**2
                            if dist<nearest_dist:
                                nearest_dist=dist
                                nearest=npc
                        if nearest and nearest_dist**0.5 <= INTERACT_DISTANCE:
                            showing_interaction_menu = True
                            current_interaction_npc = nearest
                        else:
                            interaction_text = "No one nearby."
                            interaction_timer = 2.0
                
                if showing_interaction_menu:
                    # Handle interaction menu choices
                    if event.key==pygame.K_1:  # Talk
                        interaction_text = handle_interaction_choice(1, player, current_interaction_npc)
                        interaction_timer = 3.0
                        showing_interaction_menu = False
                        current_interaction_npc = None
                    elif event.key==pygame.K_2:  # Fight
                        interaction_text = handle_interaction_choice(2, player, current_interaction_npc)
                        interaction_timer = 3.0
                        showing_interaction_menu = False
                        current_interaction_npc = None
                    elif event.key==pygame.K_3:  # Flee
                        interaction_text = handle_interaction_choice(3, player, current_interaction_npc)
                        interaction_timer = 3.0
                        showing_interaction_menu = False
                        current_interaction_npc = None
                
                if show_scene_intro and scene_intro_can_skip:
                    # Skip scene intro with any key
                    show_scene_intro = False
                    scene_intro_timer = 0
                    scene_intro_can_skip = False

        # Update
        player.update(dt, obstacles, BACKGROUND_COLOR_KEY)
        update_dialogue(dt)
        particle_system.update(dt)
        
        # Update scene intro timer
        if show_scene_intro and scene_intro_timer > 0:
            scene_intro_timer -= 1
            if scene_intro_timer <= 0:
                show_scene_intro = False
            elif scene_intro_timer < 170:
                scene_intro_can_skip = True

        # Scene triggers (legacy - keeping for compatibility)
        if scene_active is None:
            sc = check_scene_triggers(player, scenes)
            if sc:
                scene_active = sc
                interaction_text = f"Scene triggered: {sc.get('title','(no title)')}"
                interaction_timer = 4.0

        # Camera
        cam[0] = max(0,min(player.rect.centerx - WINDOW_WIDTH//2, WORLD_BOUNDS.width-WINDOW_WIDTH))
        cam[1] = max(0,min(player.rect.centery - WINDOW_HEIGHT//2, WORLD_BOUNDS.height-WINDOW_HEIGHT))

        # Draw
        screen.fill((20,24,30))
        screen.blit(BACKGROUND, (-cam[0], -cam[1]))

        # Obstacles
        for o in obstacles: pygame.draw.rect(screen,(120,120,120),o.move(-cam[0],-cam[1]))

        # NPCs
        for npc in npcs:
            npc.draw(screen,cam)
            tag = font.render(npc.name,True,WHITE)
            screen.blit(tag,(npc.rect.x-cam[0], npc.rect.y-16-cam[1]))

        # Player
        player.draw(screen,cam)
        screen.blit(font.render(player.name,True,WHITE),(player.rect.x-cam[0],player.rect.y-16-cam[1]))

        # Particle effects (drawn after game objects but before UI)
        particle_system.draw(screen, cam)

        # UI
        screen.blit(bigfont.render(storyline.get("game",{}).get("title","RPG"),True,WHITE),(8,8))
        
        # Scene info
        if scenes and current_scene_index < len(scenes):
            current_scene = scenes[current_scene_index]
            scene_info = f"Scene {current_scene_index + 1}/{len(scenes)}: {current_scene.get('title', 'Unknown')}"
            screen.blit(font.render(scene_info, True, WHITE), (8, 40))
        
        # Controls info
        if showing_interaction_menu:
            screen.blit(font.render("Choose an action: 1-Talk, 2-Fight, 3-Flee, ESC-Cancel",True,WHITE),(8,70))
        elif show_scene_intro:
            screen.blit(font.render("Press any key to continue...",True,WHITE),(8,70))
        else:
            screen.blit(font.render("Move: WASD/Arrows, Interact: E, Scenes: N/B, Quit: ESC",True,WHITE),(8,70))

        # Draw active dialogue text (from display_text)
        global CURRENT_DIALOGUE, DIALOGUE_TIMER
        if DIALOGUE_TIMER > 0 and CURRENT_DIALOGUE:
            box_rect = pygame.Rect(60, WINDOW_HEIGHT - 120, WINDOW_WIDTH - 120, 80)
            s = pygame.Surface((box_rect.w, box_rect.h), pygame.SRCALPHA)
            s.fill((10, 10, 20, 220))
            screen.blit(s, (box_rect.x, box_rect.y))

            # Word wrap (so long lines break correctly)
            words = CURRENT_DIALOGUE.split()
            lines = []
            line = ""
            for w in words:
                test = (line + " " + w).strip()
                if len(test) * 10 > box_rect.w - 20:
                    lines.append(line)
                    line = w
                else:
                    line = test
            if line:
                lines.append(line)

            for i, l in enumerate(lines[:4]):
                screen.blit(font.render(l, True, WHITE), (box_rect.x + 10, box_rect.y + 10 + i * 20))

            DIALOGUE_TIMER -= dt
        else:
            CURRENT_DIALOGUE = ""

                
        # Draw minimap
        draw_minimap(screen, player, npcs, obstacles, cam)
        
        # Show interaction menu if active
        if showing_interaction_menu and current_interaction_npc:
            npc_name = current_interaction_npc.data.get("name", current_interaction_npc.name)
            npc_role = current_interaction_npc.data.get("role", "Unknown")
            show_interaction_menu(screen, font, npc_name, npc_role)
        
        # Show scene intro if active
        if show_scene_intro and scenes and current_scene_index < len(scenes):
            draw_scene_intro(screen, scenes[current_scene_index], scene_intro_timer)

        # Interaction box
        if interaction_timer>0 and interaction_text:
            box_rect = pygame.Rect(60,50,WINDOW_WIDTH-120,60)
            s = pygame.Surface((box_rect.w,box_rect.h),pygame.SRCALPHA)
            s.fill((10,10,20,220))
            screen.blit(s,(box_rect.x,box_rect.y))

            # simple wrap
            words = interaction_text.split()
            lines=[]
            line=""
            for w in words:
                test = (line+" "+w).strip()
                if len(test)*10>box_rect.w-20:
                    lines.append(line)
                    line=w
                else:
                    line=test
            if line: lines.append(line)
            for i,l in enumerate(lines[:4]):
                screen.blit(font.render(l,True,WHITE),(box_rect.x+10,box_rect.y+8+i*20))
            interaction_timer-=dt
        else:
            interaction_text=""

        pygame.display.flip()
    pygame.quit()

if __name__=="__main__":
    data = load_storyline("storyline.json")
    run_game(data)
