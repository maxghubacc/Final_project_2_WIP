import sys
import pygame

# ---------- Settings ----------
CELL_SIZE = 24
FPS = 6  # slower movement for maze mode

# # = wall, S = start, G = goal, . = empty
MAZE = [
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
]

ROWS = len(MAZE)
COLS = len(MAZE[0])
WINDOW_WIDTH = COLS * CELL_SIZE
WINDOW_HEIGHT = ROWS * CELL_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GRAY = (35, 35, 35)
BLUE = (80, 170, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 140, 0)
RED = (220, 60, 60)
WALL = (120, 120, 120)
YELLOW = (240, 220, 80)

STARTING_LIVES = 3

# ---------- Helpers ----------
def draw_text(surface, text, size, color, center):
    font = pygame.font.SysFont("consolas", size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    surface.blit(surf, rect)

def find_cell(ch: str):
    for r in range(ROWS):
        for c in range(COLS):
            if MAZE[r][c] == ch:
                return (c, r)  # (col, row)
    raise ValueError(f"Character {ch} not found in maze")

def cell_to_px(cell):
    return (cell[0] * CELL_SIZE, cell[1] * CELL_SIZE)

def in_bounds(cell):
    c, r = cell
    return 0 <= c < COLS and 0 <= r < ROWS

def is_wall(cell):
    c, r = cell
    return MAZE[r][c] == "#"

def clamp_direction(current_dir, new_dir):
    """Prevent reversing into yourself (mostly irrelevant with length 1, but safe)."""
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
    pygame.display.set_caption("Snake Maze (3 Lives)")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    start_cell = find_cell("S")
    goal_cell = find_cell("G")
    goal_px = cell_to_px(goal_cell)

    wall_cells = [(c, r) for r in range(ROWS) for c in range(COLS) if MAZE[r][c] == "#"]

    def reset_game():
        snake = [cell_to_px(start_cell)]  # length 1
        direction = (0, 0)               # not moving yet
        pending_dir = (0, 0)
        state = "WAITING"                # WAITING, PLAYING, WIN
        moves = 0
        lives = STARTING_LIVES
        hit_flash = 0  # frames to flash when hit wall
        return snake, direction, pending_dir, state, moves, lives, hit_flash

    snake, direction, pending_dir, state, moves, lives, hit_flash = reset_game()

    while True:
        # ---- Events ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_w, pygame.K_UP):
                    pending_dir = (0, -1)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    pending_dir = (0, 1)
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    pending_dir = (-1, 0)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    pending_dir = (1, 0)

                # Start moving on first direction press
                if state == "WAITING" and pending_dir != (0, 0):
                    direction = pending_dir
                    state = "PLAYING"

                # Manual restart
                if event.key == pygame.K_r:
                    snake, direction, pending_dir, state, moves, lives, hit_flash = reset_game()

        # ---- Update ----
        if hit_flash > 0:
            hit_flash -= 1

        if state == "PLAYING":
            direction = clamp_direction(direction, pending_dir)

            head_x, head_y = snake[0]
            dx, dy = direction
            new_head = (head_x + dx * CELL_SIZE, head_y + dy * CELL_SIZE)
            new_cell = (new_head[0] // CELL_SIZE, new_head[1] // CELL_SIZE)

            # Collision with boundary or wall: lose a life, DON'T move
            if (not in_bounds(new_cell)) or is_wall(new_cell):
                lives -= 1
                hit_flash = 8  # quick visual feedback

                # If out of lives, restart from beginning automatically
                if lives <= 0:
                    snake, direction, pending_dir, state, moves, lives, hit_flash = reset_game()

            # (Optional) Self collision handling if you later make the snake longer:
            elif new_head in snake:
                lives -= 1
                hit_flash = 8
                if lives <= 0:
                    snake, direction, pending_dir, state, moves, lives, hit_flash = reset_game()

            else:
                # Valid move: move forward (constant length)
                snake.insert(0, new_head)
                snake.pop()
                moves += 1

                # Win condition
                if new_head == goal_px:
                    state = "WIN"

        # ---- Draw ----
        screen.fill(BLACK)

        # Walls
        for c, r in wall_cells:
            x, y = cell_to_px((c, r))
            pygame.draw.rect(screen, WALL, (x, y, CELL_SIZE, CELL_SIZE))

        # Goal B
        pygame.draw.rect(screen, BLUE, (*goal_px, CELL_SIZE, CELL_SIZE))
        draw_text(screen, "B", 18, WHITE, (goal_px[0] + CELL_SIZE // 2, goal_px[1] + CELL_SIZE // 2))

        # Start A
        start_px = cell_to_px(start_cell)
        pygame.draw.rect(screen, GRAY, (*start_px, CELL_SIZE, CELL_SIZE), 2)
        draw_text(screen, "A", 18, WHITE, (start_px[0] + CELL_SIZE // 2, start_px[1] + CELL_SIZE // 2))

        # Snake (flash red when you hit a wall)
        for i, (x, y) in enumerate(snake):
            if hit_flash > 0:
                color = RED
            else:
                color = DARK_GREEN if i == 0 else GREEN
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)

        # HUD
        draw_text(screen, f"Moves: {moves}", 22, WHITE, (70, 16))
        draw_text(screen, f"Lives: {lives}", 22, YELLOW, (WINDOW_WIDTH // 2, 16))
        draw_text(screen, "Reach B", 22, WHITE, (WINDOW_WIDTH - 70, 16))

        if state == "WAITING":
            draw_text(screen, "Press WASD / Arrow Keys to Start", 24, WHITE,
                      (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        elif state == "WIN":
            draw_text(screen, "YOU WIN!", 48, WHITE, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 10))
            draw_text(screen, "Press R to Play Again", 28, WHITE, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 35))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()