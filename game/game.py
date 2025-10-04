import json
import os
import random
import pygame
from typing import Dict, List, Any, Optional, Tuple

# ---------- CONFIG ----------
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 30
PLAYER_SPEED = 180
NPC_SIZE = (36, 48)
PLAYER_SIZE = (36, 48)
WORLD_BOUNDS = pygame.Rect(0, 0, 1200, 1200)  # Smaller world
INTERACT_DISTANCE = 48
MINIMAP_SIZE = 150
MINIMAP_POS = (WINDOW_WIDTH - MINIMAP_SIZE - 10, 10)

WHITE = (255, 255, 255)
BLUE = (100, 150, 255)
GREEN = (50, 200, 100)
RED = (255, 80, 80)

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
        super().__init__(data.get("name","Player"), pygame.Rect(pos[0], pos[1], w,h), BLUE)
        self.speed = PLAYER_SPEED
    def update(self, dt, obstacles):
        keys = pygame.key.get_pressed()
        vx = vy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: vx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: vx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: vy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: vy += 1
        v = pygame.Vector2(vx, vy)
        if v.length_squared()>0: v = v.normalize() * self.speed
        new_rect = self.rect.copy()
        new_rect.x += int(v.x*dt)
        if not any(new_rect.colliderect(o) for o in obstacles) and WORLD_BOUNDS.contains(new_rect): self.rect = new_rect
        new_rect = self.rect.copy()
        new_rect.y += int(v.y*dt)
        if not any(new_rect.colliderect(o) for o in obstacles) and WORLD_BOUNDS.contains(new_rect): self.rect = new_rect

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

def handle_interaction_choice(choice, player, npc):
    """Handle the player's interaction choice"""
    name = npc.data.get("name", npc.name)
    role = npc.data.get("role", "Unknown")
    
    if choice == 1:  # Talk
        print(f"[TALK] {player.name} tries to talk to {name}")
        if "antagonist" in role.lower() or "enemy" in role.lower():
            print(f"[TALK] {name} glares menacingly: 'You dare speak to me?'")
        else:
            print(f"[TALK] {name} responds: 'Hello there! How can I help you?'")
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
    """Get character data for a specific scene based on character IDs"""
    scene_characters = []
    if not scene or "characters" not in scene:
        print(f"[DEBUG] No scene or no characters in scene: {scene}")
        return scene_characters
    
    print(f"[DEBUG] Scene has {len(scene.get('characters', []))} character IDs: {scene.get('characters', [])}")
    print(f"[DEBUG] Available characters: {[c.get('id', 'no-id') for c in all_characters]}")
    
    # Create a lookup dictionary for all characters
    char_lookup = {}
    for char in all_characters:
        char_lookup[char.get("id", "")] = char
    
    # Get characters for this scene
    for char_id in scene.get("characters", []):
        if char_id in char_lookup:
            scene_characters.append(char_lookup[char_id])
            print(f"[DEBUG] Found character: {char_id}")
        else:
            print(f"[DEBUG] Character not found: {char_id}")
    
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
    
    # Semi-transparent overlay
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
        for obstacle in obstacles:
            if test_rect.colliderect(obstacle):
                safe = False
                break
        
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
        pygame.Rect(500, 300, 150, 20),   # Moved away from center
        pygame.Rect(200, 500, 30, 200),   # Moved away from center  
        pygame.Rect(800, 200, 100, 30),   # Moved away from center
        pygame.Rect(100, 100, 80, 80),    # Corner obstacle
        pygame.Rect(1000, 1000, 100, 100) # Far corner obstacle
    ]

    # Player
    player = Player(storyline.get("main_character",{}), (WORLD_BOUNDS.centerx,WORLD_BOUNDS.centery))

    # Load all characters from storyline
    all_chars_section = storyline.get("characters",{})
    all_chars = []
    if isinstance(all_chars_section, dict):
        if "characters" in all_chars_section: all_chars_section = all_chars_section["characters"]
        if "items" in all_chars_section: all_chars = all_chars_section["items"]
    if not all_chars: all_chars = SAMPLE_DATA["characters"]["items"]

    # Scenes
    scenes_section = storyline.get("scenes",{})
    scenes = []
    if isinstance(scenes_section, dict):
        if "items" in scenes_section: scenes = scenes_section["items"]
        elif "scenes" in scenes_section and "items" in scenes_section["scenes"]:
            scenes = scenes_section["scenes"]["items"]
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

    interaction_text = ""
    interaction_timer = 0.0
    scene_active = None
    showing_interaction_menu = False
    current_interaction_npc = None
    current_scene_index = 0
    show_scene_intro = False
    scene_intro_timer = 0
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
                
                if show_scene_intro:
                    # Skip scene intro with any key
                    show_scene_intro = False
                    scene_intro_timer = 0

        # Update
        player.update(dt, obstacles)
        
        # Update scene intro timer
        if show_scene_intro and scene_intro_timer > 0:
            scene_intro_timer -= 1
            if scene_intro_timer <= 0:
                show_scene_intro = False

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
            box_rect = pygame.Rect(60,WINDOW_HEIGHT-100,WINDOW_WIDTH-120,80)
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
