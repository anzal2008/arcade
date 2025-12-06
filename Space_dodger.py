import pygame
import os
import sys
import random
from os.path import join

# -------------------- Initialization --------------------
pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 900, 500
WIN = pygame.display.set_mode((WIDTH, HEIGHT))

# -------------------- Helper Functions --------------------
def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return join(base_path, relative_path)

def load_font(size):
    return pygame.font.Font(resource_path(join("assets", "Menu", "text", "Platform.TTF")), size)

DODGER_FONT = load_font(40)

# -------------------- Drawing --------------------
def draw_window_dodger(WIN, bg, player, obstacles, score, font):
    WIN.blit(bg, (0, 0))
    WIN.blit(player['img'], (player['rect'].x, player['rect'].y))

    for obs in obstacles:
        pygame.draw.rect(WIN, "red", obs)

    score_text = font.render(f"Score: {int(score)}", True, "white")
    WIN.blit(score_text, (10, 10))
    pygame.display.update()

# -------------------- Main Dodger Game --------------------
def main_dodger():
    ASSETS_FOLDER = resource_path(join("assets", "Dual_game"))

    FPS = 60
    PLAYER_VEL = 5
    OBSTACLE_VEL = 6
    OBSTACLE_WIDTH = 40
    OBSTACLE_HEIGHT = 40
    SPAWN_RATE = 30

    # Load assets
    bg = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, "space.png")), (WIDTH, HEIGHT))
    player_img = pygame.transform.scale(
        pygame.image.load(join(ASSETS_FOLDER, "spaceship_yellow.png")),
        (50, 35)
    )

    player = {"img": player_img, "rect": pygame.Rect(WIDTH // 2, HEIGHT - 80, 50, 35)}

    obstacles = []
    frame = 0
    score = 0
    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(FPS)
        frame += 1
        score += 0.05

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        # Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player['rect'].x - PLAYER_VEL > 0:
            player['rect'].x -= PLAYER_VEL
        if keys[pygame.K_d] and player['rect'].x + player['rect'].width + PLAYER_VEL < WIDTH:
            player['rect'].x += PLAYER_VEL
        if keys[pygame.K_w] and player['rect'].y - PLAYER_VEL > 0:
            player['rect'].y -= PLAYER_VEL
        if keys[pygame.K_s] and player['rect'].y + player['rect'].height + PLAYER_VEL < HEIGHT:
            player['rect'].y += PLAYER_VEL

        # Spawn obstacles
        if frame % SPAWN_RATE == 0:
            x_pos = random.randint(0, WIDTH - OBSTACLE_WIDTH)
            obstacles.append(pygame.Rect(x_pos, -OBSTACLE_HEIGHT, OBSTACLE_WIDTH, OBSTACLE_HEIGHT))

        # Move obstacles and check collisions
        for obs in obstacles[:]:
            obs.y += OBSTACLE_VEL
            if obs.y > HEIGHT:
                obstacles.remove(obs)

            if obs.colliderect(player['rect']):
                pygame.time.delay(1000)
                return

        draw_window_dodger(WIN, bg, player, obstacles, score, DODGER_FONT)

# -------------------- Run --------------------
if __name__ == "__main__":
    main_dodger()
    pygame.quit()
