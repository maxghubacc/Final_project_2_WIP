import sys
import pygame

# ---------- Settings ----------
CELL_SIZE = 24
FPS = 5
STARTING_LIVES = 3

# Characters:
# # = wall, S = start, G = goal, . = empty

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
        "name": "Level 2 (fixed)",
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
        "name": "Level 3 (fixed)",
        "maze": [
            "##########################",
            "#S#..............#.......#",
            "#.#.###########..#.#####.#",
            "#.#.....#........#.....#.#",
            "#.#####.#.###########.#.#.",
            "#.....#.#.....#.......#..#",
            "#####.#.#####.#.########.#",
            "#.....#.....#.#........#.#",
            "#.#########.#.########.#.#",
            "#.....#.....#.....#....#.#",
            "###.#.#.#########.#.####.#",
            "#...#.#.....#.....#......#",
            "#.###.#####.#.##########.#",
            "#...........#...........G#",
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
        raise ValueError("Maze missing goal 'G'.")

def find_cell(maze, ch: str):
    rows = len(maze)
    cols = len(maze[0])
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == ch:
                return (c, r)
    raise ValueError(f"Character {ch} not found in maze")

def cell_to_px(cell):
    return (cell[0] * CELL_SIZE, cell[1] * CELL_SIZE)

def in_bounds(cell, rows, cols):
    c, r = cell
    return 0 <= c < cols and 0 <= r < rows

def is_wall(maze, cell):
    c, r = cell
    return maze[r][c] == "#"

def clamp_direction(current_dir, new_dir):
    opposites = {
        (1, 0): (-1, 0),
        (-1, 0): (1, 0),
        (0, 1): (0, -1),
        (0, -1): (0, 1),
    }
    if new_dir == opposites.get(current_dir):
        return current_dir
    return new_dir

# ---------- Game ----------
def main():
    pygame.init()
    pygame.display.set_caption("Snake Maze - Level Select")
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((800, 600))

    state = "MENU"  # MENU, WAITING, PLAYING, WIN
    current_level = None
    menu_error = ""  # show validation errors instead of crashing

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

    def load_level(level_index: int):
        nonlocal screen, state, current_level, menu_error
        nonlocal maze, rows, cols, start_cell, goal_cell, start_px, goal_px, wall_cells
        nonlocal snake, direction, pending_dir, moves, lives, hit_flash

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

        snake = [start_px]
        direction = (0, 0)
        pending_dir = (0, 0)
        moves = 0
        lives = STARTING_LIVES
        hit_flash = 0
        state = "WAITING"

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
        if state == "PLAYING":
            if hit_flash > 0:
                hit_flash -= 1

            direction = clamp_direction(direction, pending_dir)

            head_x, head_y = snake[0]
            dx, dy = direction
            new_head = (head_x + dx * CELL_SIZE, head_y + dy * CELL_SIZE)
            new_cell = (new_head[0] // CELL_SIZE, new_head[1] // CELL_SIZE)

            if (not in_bounds(new_cell, rows, cols)) or is_wall(maze, new_cell):
                lives -= 1
                hit_flash = 8
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
                if new_head == goal_px:
                    state = "WIN"
        else:
            if hit_flash > 0:
                hit_flash -= 1

        # ---- Draw ----
        screen.fill(BLACK)

        if state == "MENU":
            w, h = screen.get_size()
            draw_text(screen, "SNAKE MAZE", 54, WHITE, (w // 2, h // 2 - 160))
            draw_text(screen, "Select a Level:", 28, WHITE, (w // 2, h // 2 - 80))
            draw_text(screen, "1 - Level 1", 28, WHITE, (w // 2, h // 2 - 25))
            draw_text(screen, "2 - Level 2", 28, WHITE, (w // 2, h // 2 + 20))
            draw_text(screen, "3 - Level 3", 28, WHITE, (w // 2, h // 2 + 65))
            draw_text(screen, "ESC - Quit", 20, WHITE, (w // 2, h // 2 + 140))

            if menu_error:
                draw_text(screen, "Level error:", 22, RED, (w // 2, h // 2 + 200))
                draw_text(screen, menu_error, 18, RED, (w // 2, h // 2 + 230))

            pygame.display.flip()
            clock.tick(30)
            continue

        # walls
        for c, r in wall_cells:
            x, y = cell_to_px((c, r))
            pygame.draw.rect(screen, WALL, (x, y, CELL_SIZE, CELL_SIZE))

        # goal
        pygame.draw.rect(screen, BLUE, (*goal_px, CELL_SIZE, CELL_SIZE))
        draw_text(screen, "B", 18, WHITE, (goal_px[0] + CELL_SIZE // 2, goal_px[1] + CELL_SIZE // 2))

        # start
        pygame.draw.rect(screen, GRAY, (*start_px, CELL_SIZE, CELL_SIZE), 2)
        draw_text(screen, "A", 18, WHITE, (start_px[0] + CELL_SIZE // 2, start_px[1] + CELL_SIZE // 2))

        # snake
        for i, (x, y) in enumerate(snake):
            color = RED if hit_flash > 0 else (DARK_GREEN if i == 0 else GREEN)
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)

        # HUD
        w, _ = screen.get_size()
        draw_text(screen, f"Moves: {moves}", 22, WHITE, (70, 16))
        draw_text(screen, f"Lives: {lives}", 22, YELLOW, (w // 2, 16))
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