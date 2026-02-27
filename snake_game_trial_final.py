import random
import sys
import pygame

# ---------- Settings ----------
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
CELL_SIZE = 20  # size of each grid cell (snake + food)
FPS = 12        # game speed

# Colors (R, G, B)
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 140, 0)
RED = (220, 50, 50)
GRAY = (40, 40, 40)

# ---------- Helper functions ----------
def draw_text(surface, text, size, color, center):
    font = pygame.font.SysFont("consolas", size, bold=True)
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=center)
    surface.blit(text_surf, text_rect)

def random_grid_position():
    cols = WINDOW_WIDTH // CELL_SIZE
    rows = WINDOW_HEIGHT // CELL_SIZE
    return (random.randint(0, cols - 1) * CELL_SIZE,
            random.randint(0, rows - 1) * CELL_SIZE)

def clamp_direction(current_dir, new_dir):
    """Prevent reversing into yourself (e.g., going RIGHT then LEFT)."""
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
    pygame.display.set_caption("Snake (PyCharm + pygame)")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    def reset_game():
        start_x = (WINDOW_WIDTH // 2) // CELL_SIZE * CELL_SIZE
        start_y = (WINDOW_HEIGHT // 2) // CELL_SIZE * CELL_SIZE

        snake = [(start_x, start_y),
                 (start_x - CELL_SIZE, start_y),
                 (start_x - 2 * CELL_SIZE, start_y)]
        direction = (1, 0)  # moving right
        pending_dir = direction

        food = random_grid_position()
        while food in snake:
            food = random_grid_position()

        score = 0
        game_over = False
        return snake, direction, pending_dir, food, score, game_over

    snake, direction, pending_dir, food, score, game_over = reset_game()

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

                if game_over and event.key == pygame.K_r:
                    snake, direction, pending_dir, food, score, game_over = reset_game()

        if not game_over:
            # Apply direction change (with reverse-protection)
            direction = clamp_direction(direction, pending_dir)

            # ---- Move snake ----
            head_x, head_y = snake[0]
            dx, dy = direction
            new_head = (head_x + dx * CELL_SIZE, head_y + dy * CELL_SIZE)

            # Wall collision
            if (new_head[0] < 0 or new_head[0] >= WINDOW_WIDTH or
                new_head[1] < 0 or new_head[1] >= WINDOW_HEIGHT):
                game_over = True
            # Self collision
            elif new_head in snake:
                game_over = True
            else:
                snake.insert(0, new_head)

                # Eat food
                if new_head == food:
                    score += 1
                    food = random_grid_position()
                    while food in snake:
                        food = random_grid_position()
                else:
                    snake.pop()

        # ---- Draw ----
        screen.fill(BLACK)

        # Optional grid (subtle)
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (0, y), (WINDOW_WIDTH, y), 1)

        # Draw food
        pygame.draw.rect(screen, RED, (*food, CELL_SIZE, CELL_SIZE))

        # Draw snake (head darker)
        for i, (x, y) in enumerate(snake):
            color = DARK_GREEN if i == 0 else GREEN
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)

        # Score
        draw_text(screen, f"Score: {score}", 24, WHITE, (70, 18))

        if game_over:
            draw_text(screen, "GAME OVER", 48, WHITE, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
            draw_text(screen, "Press R to Restart", 28, WHITE, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
            draw_text(screen, "Press X (window close) to Quit", 18, WHITE, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 55))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()