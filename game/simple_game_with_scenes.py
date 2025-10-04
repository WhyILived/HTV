import pygame
import random
import sys

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Frostvale Chronicles Demo")
clock = pygame.time.Clock()

# --- Colors ---
WHITE = (255, 255, 255)
BLUE = (100, 150, 255)
GREEN = (50, 200, 100)
RED = (255, 80, 80)
GRAY = (180, 180, 200)
DARK_BLUE = (30, 30, 80)

# --- Scene Data (from your JSON) ---
scenes = [
    {
        "id": 1,
        "title": "The Frozen Citadel",
        "setting": "Elise arrives at the Frozen Citadel, a massive ice fortress where Vornir, the Ice King, resides.",
    },
    {
        "id": 2,
        "title": "The Frozen Forest",
        "setting": "Elise ventures into the Frozen Forest, where ancient spirits roam and icy creatures lurk.",
    },
    {
        "id": 3,
        "title": "The Blizzard Peak",
        "setting": "Elise climbs the treacherous Blizzard Peak through biting winds and howling blizzards.",
    },
    {
        "id": 4,
        "title": "The Ice Caverns",
        "setting": "Elise delves into the Ice Caverns, where Vornir's minions await.",
    },
    {
        "id": 5,
        "title": "The Frozen Throne Room",
        "setting": "Elise confronts Vornir in his Frozen Throne Room — the final battle begins.",
    },
]

# --- Player setup ---
player = pygame.Rect(100, 100, 40, 50)
player_color = BLUE
PLAYER_SPEED = 5

# --- World / camera ---
walls = [
    pygame.Rect(300, 300, 200, 50),
    pygame.Rect(600, 450, 50, 150),
    pygame.Rect(150, 150, 100, 200)
]

characters = [
    {"name": "Riven", "color": (200, 200, 255)},
    {"name": "Lynnea", "color": (255, 200, 255)},
    {"name": "Thorne", "color": (255, 150, 150)},
    {"name": "Sylas", "color": (150, 100, 255)},
]

# --- Generate NPCs ---
def generate_npcs():
    npc_rects = []
    for c in characters:
        x = random.randint(100, WIDTH - 100)
        y = random.randint(100, HEIGHT - 100)
        npc_rects.append((pygame.Rect(x, y, 40, 50), c["name"], c["color"]))
    return npc_rects

npc_rects = generate_npcs()

# --- Collision handling ---
def handle_collision(rect, dx, dy, obstacles):
    rect.x += dx
    for wall in obstacles:
        if rect.colliderect(wall):
            if dx > 0: rect.right = wall.left
            if dx < 0: rect.left = wall.right
    rect.y += dy
    for wall in obstacles:
        if rect.colliderect(wall):
            if dy > 0: rect.bottom = wall.top
            if dy < 0: rect.top = wall.bottom

# --- Movement ---
def move_player(keys, rect, speed):
    dx, dy = 0, 0
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        dy -= speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        dy += speed
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        dx -= speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        dx += speed
    return dx, dy

# --- Draw scene intro ---
def draw_scene_intro(scene, timer):
    font = pygame.font.SysFont(None, 36)
    title = font.render(scene["title"], True, WHITE)
    desc_font = pygame.font.SysFont(None, 24)
    desc = desc_font.render(scene["setting"], True, WHITE)

    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(desc, (WIDTH // 2 - desc.get_width() // 2, HEIGHT // 2))

# --- Get scene background color ---
def get_scene_background_color(scene_index):
    colors = [
        (30, 30, 80),   # Dark blue for Frozen Citadel
        (20, 40, 20),   # Dark green for Frozen Forest  
        (60, 60, 80),   # Gray for Blizzard Peak
        (40, 20, 40),   # Purple for Ice Caverns
        (80, 20, 20),   # Dark red for Frozen Throne Room
    ]
    return colors[scene_index % len(colors)]

# --- Scene management ---
current_scene_index = 0
show_scene_intro = True
scene_intro_timer = 120  # frames (~2 seconds)

font = pygame.font.SysFont(None, 24)
interaction_text = ""

# --- Main loop ---
running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # --- Scene switching ---
    if keys[pygame.K_n]:
        current_scene_index = (current_scene_index + 1) % len(scenes)
        npc_rects = generate_npcs()
        player.topleft = (100, 100)
        show_scene_intro = True
        scene_intro_timer = 120
        pygame.time.wait(200)  # prevent key hold skip

    if keys[pygame.K_b]:
        current_scene_index = (current_scene_index - 1) % len(scenes)
        npc_rects = generate_npcs()
        player.topleft = (100, 100)
        show_scene_intro = True
        scene_intro_timer = 120
        pygame.time.wait(200)

    dx, dy = move_player(keys, player, PLAYER_SPEED)
    handle_collision(player, dx, dy, walls)

    # Interaction check
    interaction_text = ""
    for npc_rect, name, color in npc_rects:
        if player.colliderect(npc_rect.inflate(20, 20)):
            interaction_text = f"Press [E] to talk to {name}"
            if keys[pygame.K_e]:
                interaction_text = f"You talk to {name}. (placeholder dialogue)"
                break

    # --- Drawing ---
    # Use scene-specific background color instead of alternating
    screen.fill(get_scene_background_color(current_scene_index))

    for wall in walls:
        pygame.draw.rect(screen, (120, 120, 120), wall)

    for npc_rect, name, color in npc_rects:
        pygame.draw.rect(screen, color, npc_rect)

    pygame.draw.rect(screen, player_color, player)

    # Draw scene info
    current_scene = scenes[current_scene_index]
    scene_label = font.render(f"Scene {current_scene['id']}: {current_scene['title']}", True, WHITE)
    screen.blit(scene_label, (20, 20))

    if interaction_text:
        text_surf = font.render(interaction_text, True, WHITE)
        screen.blit(text_surf, (20, HEIGHT - 40))

    # Scene intro overlay
    if show_scene_intro:
        draw_scene_intro(current_scene, scene_intro_timer)
        scene_intro_timer -= 1
        if scene_intro_timer <= 0:
            show_scene_intro = False

    # Scene switching instructions
    if not show_scene_intro:
        switch_text = font.render("Press [N] for next scene, [B] for previous scene", True, WHITE)
        screen.blit(switch_text, (20, HEIGHT - 70))

    pygame.display.flip()

pygame.quit()
sys.exit()
