import sys
import pygame

# ---------- Settings ----------
CELL_SIZE = 24
FPS = 5
STARTING_LIVES = 3

# Fog of war settings (Level 2 only)
FOG_LEVEL_INDEX = 1   # 0=Level 1, 1=Level 2, 2=Level 3, 3=Level 4
FOG_RADIUS = 5        # tiles visible using Manhattan distance

# Enemy settings (Level 3 only)
ENEMY_LEVEL_INDEX = 2
ENEMY_MOVE_EVERY_TICKS = 1  # 1 = move every game tick, 2 = every other tick (slower enemies)

# Bonus settings (Level 3 only)
BONUS_LEVEL_INDEX = 2
BONUS_POINTS = 200
BONUS_POPUP_TICKS = 30  # how long "+200" shows

# Key + Locked Exit settings (Level 4 only)
KEY_LEVEL_INDEX = 3
KEY_POPUP_TICKS = 40

# Characters:
# # = wall, S = start, G = exit/goal, . = empty, E = enemy spawn, B = bonus, K = key

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
            "#S.........#.............#",
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
            "#S#..............#.......#",
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
]

# ---------- Colors ----------
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GRAY = (35, 35, 35)
BLUE = (80, 170, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 140, 0)
RED = (220, 60, 60)
WALL = (120, 120, 120)
YELLOW = (240, 220, 80)
ENEMY_COLOR = (255, 120, 60)
BONUS_COLOR = BLUE
KEY_COLOR = (255, 215, 0)  # gold-ish

# ---------- Helpers ----------
def draw_text(surface, text, size, color, center):
    font = pygame.font.SysFont("consolas", size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    surface.blit(surf, rect)

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
    return (cell[0] * CELL_SIZE, cell[1] * CELL_SIZE)

def px_to_cell(px):
    return (px[0] // CELL_SIZE, px[1] // CELL_SIZE)

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
    """
    Allows reversing direction (backtracking).
    If the player hasn't chosen a direction yet (0,0), keep it until a real direction arrives.
    """
    if new_dir == (0, 0):
        return current_dir
    return new_dir

def apply_fog_of_war(surface, rows, cols, head_cell, radius):
    hx, hy = head_cell
    for r in range(rows):
        for c in range(cols):
            dist = abs(c - hx) + abs(r - hy)  # Manhattan distance
            if dist > radius:
                x, y = cell_to_px((c, r))
                pygame.draw.rect(surface, BLACK, (x, y, CELL_SIZE, CELL_SIZE))

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

# ---------- Game ----------
def main():
    pygame.init()
    pygame.display.set_caption("Snake Maze - Level Select")
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((800, 600))

    state = "MENU"  # MENU, WAITING, PLAYING, WIN
    current_level = None
    menu_error = ""

    # Level-specific variables
    maze = None
    rows = cols = 0
    start_cell = goal_cell = None
    start_px = goal_px = None
    wall_cells = []

    # Game variables
    snake = [(0, 0)]
    direction = (0, 0)
    pending_dir = (0, 0)
    moves = 0
    lives = STARTING_LIVES
    hit_flash = 0

    # Score / bonus variables (Level 3 uses B bonus tiles)
    score = 0
    bonus_cells = []
    collected_bonus = set()
    bonus_popup_ticks = 0
    bonus_popup_pos_px = (0, 0)

    # Enemy variables (Level 3 only)
    enemies = []
    enemy_spawns = []
    enemy_tick = 0

    # Key variables (Level 4 only)
    has_key = False
    key_cells = []
    collected_keys = set()
    key_popup_ticks = 0
    need_key_popup_ticks = 0

    def load_level(level_index: int):
        nonlocal screen, state, current_level, menu_error
        nonlocal maze, rows, cols, start_cell, goal_cell, start_px, goal_px, wall_cells
        nonlocal snake, direction, pending_dir, moves, lives, hit_flash
        nonlocal enemies, enemy_spawns, enemy_tick
        nonlocal score, bonus_cells, collected_bonus, bonus_popup_ticks, bonus_popup_pos_px
        nonlocal has_key, key_cells, collected_keys, key_popup_ticks, need_key_popup_ticks

        menu_error = ""
        current_level = level_index
        maze = LEVELS[level_index]["maze"]
        validate_maze(maze)

        rows = len(maze)
        cols = len(maze[0])
        screen = pygame.display.set_mode((cols * CELL_SIZE, rows * CELL_SIZE))

        start_cell = find_cell(maze, "S")
        goal_cell = find_cell(maze, "G")
        start_px = cell_to_px(start_cell)
        goal_px = cell_to_px(goal_cell)

        wall_cells = [(c, r) for r in range(rows) for c in range(cols) if maze[r][c] == "#"]

        # Reset player
        snake = [start_px]
        direction = (0, 0)
        pending_dir = (0, 0)
        moves = 0
        lives = STARTING_LIVES
        hit_flash = 0
        state = "WAITING"

        # Reset bonus/score
        score = 0
        bonus_cells = []
        collected_bonus = set()
        bonus_popup_ticks = 0
        bonus_popup_pos_px = (0, 0)
        if current_level == BONUS_LEVEL_INDEX:
            bonus_cells = find_all_cells(maze, "B")

        # Reset enemies
        enemies = []
        enemy_spawns = find_all_cells(maze, "E")
        enemy_tick = 0
        if current_level == ENEMY_LEVEL_INDEX:
            for spawn in enemy_spawns:
                enemies.append({
                    "pos": spawn,
                    "dir": choose_enemy_initial_dir(maze, spawn, rows, cols),
                })

        # Reset key/lock system
        has_key = False
        key_cells = []
        collected_keys = set()
        key_popup_ticks = 0
        need_key_popup_ticks = 0
        if current_level == KEY_LEVEL_INDEX:
            key_cells = find_all_cells(maze, "K")

    def reset_current_level():
        if current_level is not None:
            load_level(current_level)

    while True:
        # ---- Events ----
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

        # ---- Update ----
        if hit_flash > 0:
            hit_flash -= 1
        if bonus_popup_ticks > 0:
            bonus_popup_ticks -= 1
        if key_popup_ticks > 0:
            key_popup_ticks -= 1
        if need_key_popup_ticks > 0:
            need_key_popup_ticks -= 1

        if state == "PLAYING":
            # ✅ Backtracking enabled here:
            direction = allow_backtrack_direction(direction, pending_dir)

            # ---- Move player ----
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
                    need_key_popup_ticks = 30
                if lives <= 0:
                    reset_current_level()

            elif new_head in snake:
                lives -= 1
                hit_flash = 8
                if lives <= 0:
                    reset_current_level()

            else:
                snake.insert(0, new_head)
                snake.pop()
                moves += 1

                # Bonus pickup (Level 3 only)
                if current_level == BONUS_LEVEL_INDEX:
                    head_cell = px_to_cell(snake[0])
                    if head_cell in bonus_cells and head_cell not in collected_bonus:
                        collected_bonus.add(head_cell)
                        score += BONUS_POINTS
                        bonus_popup_ticks = BONUS_POPUP_TICKS
                        bonus_popup_pos_px = snake[0]

                # Key pickup (Level 4 only)
                if current_level == KEY_LEVEL_INDEX:
                    head_cell = px_to_cell(snake[0])
                    if head_cell in key_cells and head_cell not in collected_keys:
                        collected_keys.add(head_cell)
                        has_key = True
                        key_popup_ticks = KEY_POPUP_TICKS

                if new_head == goal_px:
                    if current_level != KEY_LEVEL_INDEX or has_key:
                        state = "WIN"
                    else:
                        need_key_popup_ticks = 30

            # ---- Move enemies (Level 3 only) ----
            if current_level == ENEMY_LEVEL_INDEX and enemies:
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

        # ---- Draw ----
        screen.fill(BLACK)

        if state == "MENU":
            w, h = screen.get_size()
            draw_text(screen, "SNAKE MAZE", 54, WHITE, (w // 2, h // 2 - 170))
            draw_text(screen, "Select a Level:", 28, WHITE, (w // 2, h // 2 - 95))
            draw_text(screen, "1 - Level 1", 26, WHITE, (w // 2, h // 2 - 45))
            draw_text(screen, "2 - Level 2 (Fog of War)", 26, WHITE, (w // 2, h // 2 - 10))
            draw_text(screen, "3 - Level 3 (Enemies + Bonus)", 26, WHITE, (w // 2, h // 2 + 25))
            draw_text(screen, "4 - Level 4 (Key + Locked Exit)", 26, WHITE, (w // 2, h // 2 + 60))
            draw_text(screen, "ESC - Quit", 20, WHITE, (w // 2, h // 2 + 140))

            if menu_error:
                draw_text(screen, "Level error:", 22, RED, (w // 2, h // 2 + 200))
                draw_text(screen, menu_error, 18, RED, (w // 2, h // 2 + 230))

            pygame.display.flip()
            clock.tick(30)
            continue

        # Walls
        for c, r in wall_cells:
            x, y = cell_to_px((c, r))
            pygame.draw.rect(screen, WALL, (x, y, CELL_SIZE, CELL_SIZE))

        # Key (Level 4 only)
        if current_level == KEY_LEVEL_INDEX:
            for cell in key_cells:
                if cell not in collected_keys:
                    kx, ky = cell_to_px(cell)
                    pygame.draw.circle(
                        screen,
                        KEY_COLOR,
                        (kx + CELL_SIZE // 2, ky + CELL_SIZE // 2),
                        max(2, CELL_SIZE // 4),
                    )

        # Bonus dots (Level 3 only)
        if current_level == BONUS_LEVEL_INDEX:
            for cell in bonus_cells:
                if cell not in collected_bonus:
                    bx, by = cell_to_px(cell)
                    pygame.draw.circle(
                        screen,
                        BONUS_COLOR,
                        (bx + CELL_SIZE // 2, by + CELL_SIZE // 2),
                        max(2, CELL_SIZE // 4),
                    )

        # Goal (Exit)
        if current_level == KEY_LEVEL_INDEX and not has_key:
            pygame.draw.rect(screen, (60, 90, 130), (*goal_px, CELL_SIZE, CELL_SIZE))
            draw_text(screen, "🔒", 18, WHITE, (goal_px[0] + CELL_SIZE // 2, goal_px[1] + CELL_SIZE // 2))
        else:
            pygame.draw.rect(screen, BLUE, (*goal_px, CELL_SIZE, CELL_SIZE))
            draw_text(screen, "B", 18, WHITE, (goal_px[0] + CELL_SIZE // 2, goal_px[1] + CELL_SIZE // 2))

        # Start
        pygame.draw.rect(screen, GRAY, (*start_px, CELL_SIZE, CELL_SIZE), 2)
        draw_text(screen, "A", 18, WHITE, (start_px[0] + CELL_SIZE // 2, start_px[1] + CELL_SIZE // 2))

        # Enemies (Level 3 only)
        if current_level == ENEMY_LEVEL_INDEX:
            for e in enemies:
                ex, ey = cell_to_px(e["pos"])
                pygame.draw.rect(screen, ENEMY_COLOR, (ex, ey, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, BLACK, (ex, ey, CELL_SIZE, CELL_SIZE), 2)

        # Snake
        for i, (x, y) in enumerate(snake):
            color = RED if hit_flash > 0 else (DARK_GREEN if i == 0 else GREEN)
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)

        # Popups
        if bonus_popup_ticks > 0:
            draw_text(
                screen,
                f"+{BONUS_POINTS}",
                24,
                BONUS_COLOR,
                (bonus_popup_pos_px[0] + CELL_SIZE // 2, bonus_popup_pos_px[1] - 10),
            )

        if key_popup_ticks > 0:
            draw_text(
                screen,
                "KEY FOUND!",
                24,
                KEY_COLOR,
                (snake[0][0] + CELL_SIZE // 2, snake[0][1] - 10),
            )

        if need_key_popup_ticks > 0:
            draw_text(
                screen,
                "NEED KEY",
                24,
                KEY_COLOR,
                (snake[0][0] + CELL_SIZE // 2, snake[0][1] - 10),
            )

        # Fog of War (ONLY Level 2)
        if current_level == FOG_LEVEL_INDEX:
            head_cell = px_to_cell(snake[0])
            apply_fog_of_war(screen, rows, cols, head_cell, FOG_RADIUS)

        # HUD (draw after fog so it's always visible)
        w, _ = screen.get_size()
        draw_text(screen, f"Moves: {moves}", 22, WHITE, (70, 16))
        draw_text(screen, f"Lives: {lives}", 22, YELLOW, (w // 2, 16))
        if current_level == BONUS_LEVEL_INDEX:
            draw_text(screen, f"Score: {score}", 22, BONUS_COLOR, (w - 110, 16))
        if current_level == KEY_LEVEL_INDEX:
            draw_text(screen, f"Key: {'YES' if has_key else 'NO'}", 22, KEY_COLOR, (w - 110, 16))
        draw_text(screen, "M: Menu", 22, WHITE, (w - 70, 16))

        if state == "WAITING":
            draw_text(screen, "Press WASD / Arrow Keys to Start", 24, WHITE,
                      (w // 2, (rows * CELL_SIZE) // 2))
            draw_text(screen, "R: Restart level   M: Menu", 18, WHITE,
                      (w // 2, (rows * CELL_SIZE) // 2 + 35))
        elif state == "WIN":
            draw_text(screen, "YOU WIN!", 48, WHITE, (w // 2, (rows * CELL_SIZE) // 2 - 10))
            draw_text(screen, "R: Replay level   M: Menu", 28, WHITE,
                      (w // 2, (rows * CELL_SIZE) // 2 + 35))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()