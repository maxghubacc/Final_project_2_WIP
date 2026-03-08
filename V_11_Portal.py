import sys
import os
import pygame

# ---------- Settings ----------
CELL_SIZE = 24
FPS = 5
STARTING_LIVES = 5

# Player image settings
PLAYER_IMAGE_FILENAME = "method.png"

# Enemy image settings
ENEMY_IMAGE_FILENAME = "pac.png"

# HUD / layout
HUD_HEIGHT = 58

# Fog of war settings (Level 2 only)
FOG_LEVEL_INDEX = 1
FOG_RADIUS = 5

# Enemy settings (map-driven: any level with 'E' has enemies)
ENEMY_MOVE_EVERY_TICKS = 1

# Bonus settings (map-driven: any level with 'B' has bonuses)
BONUS_POINTS = 200
BONUS_POPUP_TICKS = 16

# Key + Locked Exit settings (Level 4 only — still level-driven)
KEY_LEVEL_INDEX = 3
KEY_POPUP_TICKS = 18

# Portal settings (Level 5)
PORTAL_LEVEL_INDEX = 4
PORTAL_POPUP_TICKS = 14

# Characters:
# # = wall, S = start, G = exit/goal, . = empty, E = enemy spawn, B = bonus, K = key
# P / Q = portal pair 1
# R / T = portal pair 2

LEVELS = [
    {
        "name": "Level 1",
        "maze": [
            "##########################",
            "#S....#.............#....#",
            "###.#.#.###########.#.##.#",
            "#...#.#.....#.......#..#.#",
            "#.###.#####.#.########.#.#",
            "#.....#...#.#........#.#.#",
            "#####.#.#.#.########.#.#.#",
            "#.....#.#...#......#...#.#",
            "#.#####.#####.####.#####.#",
            "#.......#.....#..#.......#",
            "#######.#.#####.##########",
            "#.......#.....#..........#",
            "#.#############.########.#",
            "#...............#......#G#",
            "##########################",
        ],
    },
    {
        "name": "Level 2 (Fog of War)",
        "maze": [
            "##########################",
            "#S.....B...#.............#",
            "###.#####.##.###########.#",
            "#...#...#....#.......#...#",
            "#.###.#.######.#####.#.###",
            "#.....#......#.#.....#...#",
            "#####.######.#.#.#######.#",
            "#...#........#.#.....#...#",
            "#.#.##########.#####.#.###",
            "#.#..........#.....#.#...#",
            "#.##########.#####.#.###.#",
            "#..........#.....#.#...#.#",
            "##########.#####.#.###.#.#",
            "#.....................#G.#",
            "##########################",
        ],
    },
    {
        "name": "Level 3 (Enemies)",
        "maze": [
            "##########################",
            "#S#.....B........#.......#",
            "#.#.###########..#.#####.#",
            "#.#.....#........#.....#.#",
            "#.#####.#.###########.#.#.",
            "#.....#.#.....#.......#..#",
            "#####.#.#####.#.########.#",
            "#........E....#........#.#",
            "#.#########.#.########.#.#",
            "#.....#.....#.....#....#.#",
            "###.#.#.#########.#.####.#",
            "#...#.#.....#.....E......#",
            "#.###.#####.#.##########.#",
            "#...........#...........G#",
            "##########################",
        ],
    },
    {
        "name": "Level 4 (Find the Key)",
        "maze": [
            "##########################",
            "#S..............#........#",
            "#####.#######.#.#####.#..G",
            "#.....#.....#.#.....#.#..#",
            "#.###.#.###.#.#####.#.##.#",
            "#...#.#...#.#.....#.#....#",
            "###.#.###.#.#####.#.####.#",
            "#...#.....#.....#.#......#",
            "#.###########.#.#.######.#",
            "#.....#.......#.#......#.#",
            "#####.#.#######.######.#.#",
            "#.....#.....#....K....#..#",
            "#.#########.#.##########.#",
            "#....B......#............#",
            "##########################",
        ],
    },
    {
        "name": "Level 5 (Portals)",
        "maze": [
            "##########################",
            "#S........#.........#....#",
            "#####.###.#.#######.#.##.#",
            "#.....#...#.....P.#.#.##.#",
            "#.#####.#######.#.#.#.##.#",
            "#.#...........#.#.#.#....#",
            "#.#.#########.#.#.#.######",
            "#.#.#.......#.#.#.#......#",
            "#.#.#.#####.#.#.#.######.#",
            "#...#.#Q..#...#.#..R..#..#",
            "#####.#.#######.######.#.#",
            "#.....#.........#....#.#.#",
            "#.###############.##.#.#.#",
            "#.................##.T..G#",
            "##########################",
        ],
    },
]

# ---------- Colors ----------
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)

# Retro dungeon palette
BG_DARK = (10, 8, 20)
BG_MID = (22, 18, 38)
STONE = (58, 50, 72)
STONE_DARK = (34, 28, 46)
STONE_LIGHT = (88, 78, 104)
MORTAR = (28, 22, 40)

PURPLE_NEON = (185, 90, 255)
CYAN_NEON = (80, 220, 255)
MAGENTA_NEON = (255, 90, 220)
GOLD = (255, 205, 90)
RED_NEON = (255, 85, 85)
LIME = (160, 255, 120)

BLUE = (80, 170, 255)
BONUS_COLOR = CYAN_NEON
KEY_COLOR = GOLD
HUD_TEXT = (230, 225, 255)

PORTAL1_COLOR = (110, 255, 255)
PORTAL2_COLOR = (255, 110, 255)

# ---------- Helpers ----------
def draw_text(surface, text, size, color, center):
    font = pygame.font.SysFont("consolas", size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    surface.blit(surf, rect)

def draw_glow_text(surface, text, size, color, glow_color, center):
    font = pygame.font.SysFont("consolas", size, bold=True)
    base = font.render(text, True, color)
    rect = base.get_rect(center=center)

    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
        glow = font.render(text, True, glow_color)
        glow_rect = glow.get_rect(center=(center[0] + dx, center[1] + dy))
        surface.blit(glow, glow_rect)

    surface.blit(base, rect)

def validate_maze(maze):
    if not maze:
        raise ValueError("Maze is empty.")
    width = len(maze[0])
    for i, row in enumerate(maze):
        if len(row) != width:
            raise ValueError(f"Maze row {i} has length {len(row)} but expected {width}.")
    flat = "".join(maze)
    if "S" not in flat:
        raise ValueError("Maze missing start 'S'.")
    if "G" not in flat:
        raise ValueError("Maze missing exit/goal 'G'.")

def find_cell(maze, ch: str):
    rows = len(maze)
    cols = len(maze[0])
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == ch:
                return (c, r)
    raise ValueError(f"Character {ch} not found in maze")

def find_all_cells(maze, ch: str):
    out = []
    rows = len(maze)
    cols = len(maze[0])
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == ch:
                out.append((c, r))
    return out

def cell_to_px(cell):
    return (cell[0] * CELL_SIZE, cell[1] * CELL_SIZE + HUD_HEIGHT)

def px_to_cell(px):
    return (px[0] // CELL_SIZE, (px[1] - HUD_HEIGHT) // CELL_SIZE)

def in_bounds(cell, rows, cols):
    c, r = cell
    return 0 <= c < cols and 0 <= r < rows

def is_wall(maze, cell):
    c, r = cell
    return maze[r][c] == "#"

def tile_at(maze, cell):
    c, r = cell
    return maze[r][c]

def allow_backtrack_direction(current_dir, new_dir):
    if new_dir == (0, 0):
        return current_dir
    return new_dir

def apply_fog_of_war(surface, rows, cols, head_cell, radius):
    hx, hy = head_cell
    fog = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    for r in range(rows):
        for c in range(cols):
            dist = abs(c - hx) + abs(r - hy)
            x, y = cell_to_px((c, r))
            if dist > radius:
                alpha = 245
            elif dist == radius:
                alpha = 180
            elif dist == radius - 1:
                alpha = 100
            else:
                alpha = 0
            if alpha > 0:
                pygame.draw.rect(fog, (0, 0, 0, alpha), (x, y, CELL_SIZE, CELL_SIZE))

    surface.blit(fog, (0, 0))

def choose_enemy_initial_dir(maze, cell, rows, cols):
    candidates = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    cx, cy = cell
    for dx, dy in candidates:
        nxt = (cx + dx, cy + dy)
        if in_bounds(nxt, rows, cols) and not is_wall(maze, nxt):
            return (dx, dy)
    return (0, 0)

def move_enemy_bounce(maze, pos, direction, rows, cols):
    x, y = pos
    dx, dy = direction
    if (dx, dy) == (0, 0):
        return pos, direction

    nxt = (x + dx, y + dy)
    if in_bounds(nxt, rows, cols) and not is_wall(maze, nxt):
        return nxt, direction

    rdx, rdy = (-dx, -dy)
    nxt2 = (x + rdx, y + rdy)
    if in_bounds(nxt2, rows, cols) and not is_wall(maze, nxt2):
        return nxt2, (rdx, rdy)

    return pos, direction

def load_sprite(filename: str, cell_size: int):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(script_dir, filename)

    if not os.path.exists(img_path):
        raise FileNotFoundError(
            f"Couldn't find '{filename}' next to your .py file.\n"
            f"Move {filename} into the same folder as this script.\n"
            f"Looked here: {img_path}"
        )

    img = pygame.image.load(img_path).convert_alpha()
    img = pygame.transform.smoothscale(img, (cell_size, cell_size))
    return img

def rotated_sprite(img, direction):
    if direction == (0, -1):
        return pygame.transform.rotate(img, 90)
    if direction == (0, 1):
        return pygame.transform.rotate(img, -90)
    if direction == (-1, 0):
        return pygame.transform.rotate(img, 180)
    return img

# ---------- Retro Dungeon Drawing ----------
def draw_dungeon_floor(surface, width, height):
    surface.fill(BG_DARK)
    tile = CELL_SIZE
    for y in range(HUD_HEIGHT, height, tile):
        for x in range(0, width, tile):
            base = BG_MID if ((x // tile) + ((y - HUD_HEIGHT) // tile)) % 2 == 0 else BG_DARK
            pygame.draw.rect(surface, base, (x, y, tile, tile))
            pygame.draw.line(surface, (18, 14, 28), (x, y), (x + tile, y), 1)
            pygame.draw.line(surface, (8, 6, 14), (x, y + tile - 1), (x + tile, y + tile - 1), 1)

def draw_wall_tile(surface, x, y, size):
    pygame.draw.rect(surface, STONE, (x, y, size, size))
    pygame.draw.rect(surface, STONE_DARK, (x, y, size, size), 2)
    pygame.draw.line(surface, STONE_LIGHT, (x + 1, y + 1), (x + size - 2, y + 1), 1)
    pygame.draw.line(surface, STONE_LIGHT, (x + 1, y + 1), (x + 1, y + size - 2), 1)

    half = size // 2
    pygame.draw.line(surface, MORTAR, (x, y + half), (x + size, y + half), 2)

    if (y // size) % 2 == 0:
        pygame.draw.line(surface, MORTAR, (x + half, y), (x + half, y + half), 2)
    else:
        quarter = size // 4
        pygame.draw.line(surface, MORTAR, (x + quarter, y), (x + quarter, y + half), 2)
        pygame.draw.line(surface, MORTAR, (x + 3 * quarter, y), (x + 3 * quarter, y + half), 2)

    if (y // size) % 2 == 1:
        pygame.draw.line(surface, MORTAR, (x + half, y + half), (x + half, y + size), 2)
    else:
        quarter = size // 4
        pygame.draw.line(surface, MORTAR, (x + quarter, y + half), (x + quarter, y + size), 2)
        pygame.draw.line(surface, MORTAR, (x + 3 * quarter, y + half), (x + 3 * quarter, y + size), 2)

def draw_bonus_orb(surface, center, radius):
    pygame.draw.circle(surface, CYAN_NEON, center, radius)
    pygame.draw.circle(surface, WHITE, center, max(2, radius // 2))
    pygame.draw.circle(surface, PURPLE_NEON, center, radius, 1)

def draw_key_orb(surface, center, radius):
    pygame.draw.circle(surface, GOLD, center, radius)
    pygame.draw.circle(surface, WHITE, center, max(2, radius // 2))
    pygame.draw.circle(surface, (120, 80, 10), center, radius, 1)

def draw_portal(surface, rect, color, label):
    cx, cy = rect.center
    radius = rect.width // 2 - 2
    pygame.draw.circle(surface, color, (cx, cy), radius)
    pygame.draw.circle(surface, WHITE, (cx, cy), radius - 5, 2)
    pygame.draw.circle(surface, BG_DARK, (cx, cy), radius - 8)
    pygame.draw.circle(surface, color, (cx, cy), radius - 10, 2)
    draw_glow_text(surface, label, 16, WHITE, color, rect.center)

def draw_start_tile(surface, rect):
    pygame.draw.rect(surface, (40, 30, 60), rect)
    pygame.draw.rect(surface, PURPLE_NEON, rect, 2)
    draw_glow_text(surface, "A", 18, WHITE, PURPLE_NEON, rect.center)

def draw_exit_tile(surface, rect, locked=False):
    if locked:
        pygame.draw.rect(surface, (35, 45, 70), rect)
        pygame.draw.rect(surface, MAGENTA_NEON, rect, 2)
        draw_glow_text(surface, "LOCK", 12, WHITE, MAGENTA_NEON, rect.center)
    else:
        pygame.draw.rect(surface, (25, 55, 50), rect)
        pygame.draw.rect(surface, CYAN_NEON, rect, 2)
        draw_glow_text(surface, "EXIT", 12, WHITE, CYAN_NEON, rect.center)

def draw_menu_background(surface):
    w, h = surface.get_size()
    surface.fill(BG_DARK)

    for y in range(0, h, 8):
        color = (12 + (y % 24), 8, 24 + (y % 32))
        pygame.draw.line(surface, color, (0, y), (w, y))

    frame = pygame.Rect(70, 55, w - 140, h - 110)
    pygame.draw.rect(surface, (16, 10, 30), frame)
    pygame.draw.rect(surface, PURPLE_NEON, frame, 3)
    inner = frame.inflate(-18, -18)
    pygame.draw.rect(surface, (8, 6, 18), inner)
    pygame.draw.rect(surface, CYAN_NEON, inner, 1)

    for x in range(inner.left, inner.right, 24):
        pygame.draw.line(surface, (18, 12, 34), (x, inner.top), (x, inner.bottom), 1)
    for y in range(inner.top, inner.bottom, 24):
        pygame.draw.line(surface, (18, 12, 34), (inner.left, y), (inner.right, y), 1)

# ---------- Game ----------
def main():
    pygame.init()
    pygame.display.set_caption("Method Man Maze Madness - Level Select")
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((800, 600))

    player_img_base = load_sprite(PLAYER_IMAGE_FILENAME, CELL_SIZE)
    enemy_img_base = load_sprite(ENEMY_IMAGE_FILENAME, CELL_SIZE)

    state = "MENU"
    current_level = None
    menu_error = ""

    maze = None
    rows = cols = 0
    start_cell = goal_cell = None
    start_px = goal_px = None
    wall_cells = []

    snake = [(0, 0)]
    direction = (0, 0)
    pending_dir = (0, 0)
    lives = STARTING_LIVES
    hit_flash = 0

    score = 0
    bonus_cells = []
    collected_bonus = set()
    bonus_popup_ticks = 0
    bonus_popup_pos_px = (0, 0)
    bonuses_active = False

    enemies = []
    enemy_spawns = []
    enemy_tick = 0
    enemies_active = False

    has_key = False
    key_cells = []
    collected_keys = set()
    key_popup_ticks = 0
    need_key_popup_ticks = 0

    # Portal variables
    portals_active = False
    portal_pairs = {}
    portal_popup_ticks = 0
    portal_popup_text = ""
    portal_popup_pos_px = (0, 0)

    def load_level(level_index: int):
        nonlocal screen, state, current_level, menu_error
        nonlocal maze, rows, cols, start_cell, goal_cell, start_px, goal_px, wall_cells
        nonlocal snake, direction, pending_dir, lives, hit_flash
        nonlocal enemies, enemy_spawns, enemy_tick, enemies_active
        nonlocal score, bonus_cells, collected_bonus, bonus_popup_ticks, bonus_popup_pos_px, bonuses_active
        nonlocal has_key, key_cells, collected_keys, key_popup_ticks, need_key_popup_ticks
        nonlocal portals_active, portal_pairs, portal_popup_ticks, portal_popup_text, portal_popup_pos_px

        menu_error = ""
        current_level = level_index
        maze = LEVELS[level_index]["maze"]
        validate_maze(maze)

        rows = len(maze)
        cols = len(maze[0])
        screen = pygame.display.set_mode((cols * CELL_SIZE, rows * CELL_SIZE + HUD_HEIGHT))

        start_cell = find_cell(maze, "S")
        goal_cell = find_cell(maze, "G")
        start_px = cell_to_px(start_cell)
        goal_px = cell_to_px(goal_cell)

        wall_cells = [(c, r) for r in range(rows) for c in range(cols) if maze[r][c] == "#"]

        snake = [start_px]
        direction = (0, 0)
        pending_dir = (0, 0)
        lives = STARTING_LIVES
        hit_flash = 0
        state = "WAITING"

        score = 0
        bonus_cells = find_all_cells(maze, "B")
        collected_bonus = set()
        bonus_popup_ticks = 0
        bonus_popup_pos_px = (0, 0)
        bonuses_active = len(bonus_cells) > 0

        enemies = []
        enemy_spawns = find_all_cells(maze, "E")
        enemy_tick = 0
        enemies_active = len(enemy_spawns) > 0
        if enemies_active:
            for spawn in enemy_spawns:
                enemies.append({
                    "pos": spawn,
                    "dir": choose_enemy_initial_dir(maze, spawn, rows, cols),
                })

        has_key = False
        key_cells = []
        collected_keys = set()
        key_popup_ticks = 0
        need_key_popup_ticks = 0
        if current_level == KEY_LEVEL_INDEX:
            key_cells = find_all_cells(maze, "K")

        # Portals
        portal_pairs = {}
        p1a = find_all_cells(maze, "P")
        p1b = find_all_cells(maze, "Q")
        p2a = find_all_cells(maze, "R")
        p2b = find_all_cells(maze, "T")

        if len(p1a) == 1 and len(p1b) == 1:
            portal_pairs[p1a[0]] = p1b[0]
            portal_pairs[p1b[0]] = p1a[0]
        if len(p2a) == 1 and len(p2b) == 1:
            portal_pairs[p2a[0]] = p2b[0]
            portal_pairs[p2b[0]] = p2a[0]

        portals_active = len(portal_pairs) > 0
        portal_popup_ticks = 0
        portal_popup_text = ""
        portal_popup_pos_px = (0, 0)

    def reset_current_level():
        if current_level is not None:
            load_level(current_level)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if state == "MENU":
                    try:
                        if event.key == pygame.K_1:
                            load_level(0)
                        elif event.key == pygame.K_2:
                            load_level(1)
                        elif event.key == pygame.K_3:
                            load_level(2)
                        elif event.key == pygame.K_4:
                            load_level(3)
                        elif event.key == pygame.K_5:
                            load_level(4)
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                    except Exception as e:
                        menu_error = str(e)
                    continue

                if event.key in (pygame.K_w, pygame.K_UP):
                    pending_dir = (0, -1)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    pending_dir = (0, 1)
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    pending_dir = (-1, 0)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    pending_dir = (1, 0)

                if state == "WAITING" and pending_dir != (0, 0):
                    direction = pending_dir
                    state = "PLAYING"

                if event.key == pygame.K_r and state in ("WAITING", "PLAYING", "WIN"):
                    reset_current_level()

                if event.key == pygame.K_m:
                    state = "MENU"
                    screen = pygame.display.set_mode((800, 600))

        if hit_flash > 0:
            hit_flash -= 1
        if bonus_popup_ticks > 0:
            bonus_popup_ticks -= 1
        if key_popup_ticks > 0:
            key_popup_ticks -= 1
        if need_key_popup_ticks > 0:
            need_key_popup_ticks -= 1
        if portal_popup_ticks > 0:
            portal_popup_ticks -= 1

        if state == "PLAYING":
            direction = allow_backtrack_direction(direction, pending_dir)

            head_x, head_y = snake[0]
            dx, dy = direction
            new_head = (head_x + dx * CELL_SIZE, head_y + dy * CELL_SIZE)
            new_cell = px_to_cell(new_head)

            blocked = False
            bump_locked_gate = False

            if not in_bounds(new_cell, rows, cols):
                blocked = True
            else:
                t = tile_at(maze, new_cell)
                if t == "#":
                    blocked = True
                elif current_level == KEY_LEVEL_INDEX and t == "G" and not has_key:
                    blocked = True
                    bump_locked_gate = True

            if blocked:
                lives -= 1
                hit_flash = 8
                if bump_locked_gate:
                    need_key_popup_ticks = 14
                if lives <= 0:
                    reset_current_level()

            elif new_head in snake:
                lives -= 1
                hit_flash = 8
                if lives <= 0:
                    reset_current_level()

            else:
                # Move player
                snake.insert(0, new_head)
                snake.pop()

                # Portal check
                head_cell = px_to_cell(snake[0])
                if portals_active and head_cell in portal_pairs:
                    exit_cell = portal_pairs[head_cell]
                    snake[0] = cell_to_px(exit_cell)
                    head_cell = exit_cell
                    portal_popup_ticks = PORTAL_POPUP_TICKS
                    portal_popup_pos_px = snake[0]
                    tile = tile_at(maze, head_cell)
                    if tile in ("Q", "P"):
                        portal_popup_text = "CYAN PORTAL"
                    else:
                        portal_popup_text = "MAGENTA PORTAL"

                # Bonus pickup
                if bonuses_active:
                    head_cell = px_to_cell(snake[0])
                    if head_cell in bonus_cells and head_cell not in collected_bonus:
                        collected_bonus.add(head_cell)
                        score += BONUS_POINTS
                        bonus_popup_ticks = BONUS_POPUP_TICKS
                        bonus_popup_pos_px = snake[0]

                # Key pickup
                if current_level == KEY_LEVEL_INDEX:
                    head_cell = px_to_cell(snake[0])
                    if head_cell in key_cells and head_cell not in collected_keys:
                        collected_keys.add(head_cell)
                        has_key = True
                        key_popup_ticks = KEY_POPUP_TICKS

                # Win
                if snake[0] == goal_px:
                    if current_level != KEY_LEVEL_INDEX or has_key:
                        state = "WIN"
                    else:
                        need_key_popup_ticks = 14

            if enemies_active and enemies:
                enemy_tick += 1
                if enemy_tick % ENEMY_MOVE_EVERY_TICKS == 0:
                    for e in enemies:
                        e["pos"], e["dir"] = move_enemy_bounce(maze, e["pos"], e["dir"], rows, cols)

                head_cell = px_to_cell(snake[0])
                if any(e["pos"] == head_cell for e in enemies):
                    lives -= 1
                    hit_flash = 8
                    if lives <= 0:
                        reset_current_level()

        if state == "MENU":
            draw_menu_background(screen)
            w, h = screen.get_size()

            draw_glow_text(screen, "METHOD MAN", 44, GOLD, MAGENTA_NEON, (w // 2, h // 2 - 200))
            draw_glow_text(screen, "MAZE MADNESS", 44, CYAN_NEON, PURPLE_NEON, (w // 2, h // 2 - 155))

            draw_text(screen, "SELECT A DUNGEON", 24, HUD_TEXT, (w // 2, h // 2 - 95))
            draw_text(screen, "1  -  LEVEL 1", 24, GOLD, (w // 2, h // 2 - 45))
            draw_text(screen, "2  -  LEVEL 2  (FOG OF WAR)", 24, CYAN_NEON, (w // 2, h // 2 - 5))
            draw_text(screen, "3  -  LEVEL 3  (ENEMIES)", 24, MAGENTA_NEON, (w // 2, h // 2 + 35))
            draw_text(screen, "4  -  LEVEL 4  (KEY + EXIT)", 24, LIME, (w // 2, h // 2 + 75))
            draw_text(screen, "5  -  LEVEL 5  (PORTALS)", 24, WHITE, (w // 2, h // 2 + 115))
            draw_text(screen, "ESC  -  QUIT", 18, HUD_TEXT, (w // 2, h // 2 + 165))

            if menu_error:
                draw_glow_text(screen, "LEVEL ERROR", 22, RED_NEON, MAGENTA_NEON, (w // 2, h // 2 + 220))
                draw_text(screen, menu_error, 16, RED_NEON, (w // 2, h // 2 + 250))

            pygame.display.flip()
            clock.tick(30)
            continue

        draw_dungeon_floor(screen, screen.get_width(), screen.get_height())

        for c, r in wall_cells:
            x, y = cell_to_px((c, r))
            draw_wall_tile(screen, x, y, CELL_SIZE)

        if current_level == KEY_LEVEL_INDEX:
            for cell in key_cells:
                if cell not in collected_keys:
                    kx, ky = cell_to_px(cell)
                    draw_key_orb(screen, (kx + CELL_SIZE // 2, ky + CELL_SIZE // 2), max(3, CELL_SIZE // 4))

        if bonuses_active:
            for cell in bonus_cells:
                if cell not in collected_bonus:
                    bx, by = cell_to_px(cell)
                    draw_bonus_orb(screen, (bx + CELL_SIZE // 2, by + CELL_SIZE // 2), max(3, CELL_SIZE // 4))

        # Portals
        if portals_active:
            for cell in portal_pairs.keys():
                x, y = cell_to_px(cell)
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                tile = tile_at(maze, cell)
                if tile in ("P", "Q"):
                    draw_portal(screen, rect, PORTAL1_COLOR, "1")
                elif tile in ("R", "T"):
                    draw_portal(screen, rect, PORTAL2_COLOR, "2")

        goal_rect = pygame.Rect(goal_px[0], goal_px[1], CELL_SIZE, CELL_SIZE)
        if current_level == KEY_LEVEL_INDEX and not has_key:
            draw_exit_tile(screen, goal_rect, locked=True)
        else:
            draw_exit_tile(screen, goal_rect, locked=False)

        start_rect = pygame.Rect(start_px[0], start_px[1], CELL_SIZE, CELL_SIZE)
        draw_start_tile(screen, start_rect)

        if enemies_active:
            for e in enemies:
                ex, ey = cell_to_px(e["pos"])
                enemy_img = rotated_sprite(enemy_img_base, e["dir"])
                screen.blit(enemy_img, (ex, ey))

        # Method Man stays in original orientation
        head_px = snake[0]
        screen.blit(player_img_base, head_px)

        if bonus_popup_ticks > 0:
            draw_glow_text(
                screen,
                f"+{BONUS_POINTS}",
                20,
                CYAN_NEON,
                PURPLE_NEON,
                (bonus_popup_pos_px[0] + CELL_SIZE // 2, bonus_popup_pos_px[1] - 8),
            )

        if key_popup_ticks > 0:
            draw_glow_text(
                screen,
                "KEY FOUND!",
                20,
                GOLD,
                MAGENTA_NEON,
                (snake[0][0] + CELL_SIZE // 2, snake[0][1] - 8),
            )

        if need_key_popup_ticks > 0:
            draw_glow_text(
                screen,
                "NEED KEY",
                20,
                RED_NEON,
                MAGENTA_NEON,
                (snake[0][0] + CELL_SIZE // 2, snake[0][1] - 8),
            )

        if portal_popup_ticks > 0:
            draw_glow_text(
                screen,
                portal_popup_text,
                18,
                WHITE,
                CYAN_NEON if "CYAN" in portal_popup_text else MAGENTA_NEON,
                (portal_popup_pos_px[0] + CELL_SIZE // 2, portal_popup_pos_px[1] - 8),
            )

        if current_level == FOG_LEVEL_INDEX:
            head_cell = px_to_cell(snake[0])
            apply_fog_of_war(screen, rows, cols, head_cell, FOG_RADIUS)

        # HUD
        hud_rect = pygame.Rect(6, 6, screen.get_width() - 12, HUD_HEIGHT - 12)
        pygame.draw.rect(screen, (14, 10, 26), hud_rect)
        pygame.draw.rect(screen, PURPLE_NEON, hud_rect, 2)

        w, _ = screen.get_size()
        draw_text(screen, f"LIVES: {lives}", 22, GOLD, (110, 28))

        if bonuses_active:
            draw_text(screen, f"SCORE: {score}", 20, CYAN_NEON, (w // 2, 28))

        if current_level == KEY_LEVEL_INDEX:
            draw_text(screen, f"KEY: {'YES' if has_key else 'NO'}", 20, KEY_COLOR, (w - 120, 28))
        elif current_level == PORTAL_LEVEL_INDEX:
            draw_text(screen, "PORTALS: 2 SETS", 18, WHITE, (w - 120, 28))

        draw_text(screen, "M: MENU", 18, HUD_TEXT, (w - 60, 28))

        if state == "WAITING":
            draw_glow_text(screen, "PRESS WASD / ARROWS TO BEGIN", 24, WHITE, PURPLE_NEON,
                           (w // 2, HUD_HEIGHT + (rows * CELL_SIZE) // 2))
            draw_text(screen, "R: RESTART LEVEL    M: MENU", 18, HUD_TEXT,
                      (w // 2, HUD_HEIGHT + (rows * CELL_SIZE) // 2 + 35))
        elif state == "WIN":
            draw_glow_text(screen, "YOU ESCAPED THE DUNGEON!", 34, GOLD, MAGENTA_NEON,
                           (w // 2, HUD_HEIGHT + (rows * CELL_SIZE) // 2 - 10))
            draw_text(screen, "R: REPLAY LEVEL    M: MENU", 24, CYAN_NEON,
                      (w // 2, HUD_HEIGHT + (rows * CELL_SIZE) // 2 + 35))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()