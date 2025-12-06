import pygame
import os
import sys
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
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return join(base_path, relative_path)

def load_font(size):
    return pygame.font.Font(resource_path(join("assets", "Menu", "text", "Platform.TTF")), size)

HEALTH_FONT = load_font(40)
WINNER_FONT = load_font(100)

# -------------------- Shooter Game Functions --------------------
def draw_window_shooter(WIN, WIDTH, HEIGHT, BORDER, red, yellow, red_bullets, yellow_bullets, red_health, yellow_health, bg, red_ship, yellow_ship, HEALTH_FONT):
    WIN.blit(bg, (0, 0))
    pygame.draw.rect(WIN, "black", BORDER)

    red_health_text = HEALTH_FONT.render(f"Health: {red_health}", 1, "white")
    yellow_health_text = HEALTH_FONT.render(f"Health: {yellow_health}", 1, "white")
    WIN.blit(red_health_text, (WIDTH - red_health_text.get_width() - 10, 10))
    WIN.blit(yellow_health_text, (10, 10))

    WIN.blit(red_ship, (red.x, red.y))
    WIN.blit(yellow_ship, (yellow.x, yellow.y))

    for bullet in red_bullets:
        pygame.draw.rect(WIN, "red", bullet)
    for bullet in yellow_bullets:
        pygame.draw.rect(WIN, "yellow", bullet)

    pygame.display.update()

def handle_bullets(yellow_bullets, red_bullets, yellow, red, BULLET_VEL, WIDTH, bullet_hit_sound):
    red_hit = 0
    yellow_hit = 0

    for bullet in yellow_bullets[:]:
        bullet.x += BULLET_VEL
        if bullet.colliderect(red):
            red_hit += 1
            bullet_hit_sound.play()
            yellow_bullets.remove(bullet)
        elif bullet.x > WIDTH:
            yellow_bullets.remove(bullet)

    for bullet in red_bullets[:]:
        bullet.x -= BULLET_VEL
        if bullet.colliderect(yellow):
            yellow_hit += 1
            bullet_hit_sound.play()
            red_bullets.remove(bullet)
        elif bullet.x < 0:
            red_bullets.remove(bullet)

    return red_hit, yellow_hit

def handle_movement(keys, yellow, red, VEL, WIDTH, HEIGHT, BORDER, SPACESHIP_WIDTH, SPACESHIP_HEIGHT):
    # Yellow controls
    if keys[pygame.K_a] and yellow.x - VEL > 0:
        yellow.x -= VEL
    if keys[pygame.K_d] and yellow.x + SPACESHIP_WIDTH + VEL < BORDER.x:
        yellow.x += VEL
    if keys[pygame.K_w] and yellow.y - VEL > 0:
        yellow.y -= VEL
    if keys[pygame.K_s] and yellow.y + SPACESHIP_HEIGHT + VEL < HEIGHT:
        yellow.y += VEL

    # Red controls (arrow keys)
    if keys[pygame.K_LEFT] and red.x - VEL > BORDER.x + 10:
        red.x -= VEL
    if keys[pygame.K_RIGHT] and red.x + SPACESHIP_WIDTH + VEL < WIDTH:
        red.x += VEL
    if keys[pygame.K_UP] and red.y - VEL > 0:
        red.y -= VEL
    if keys[pygame.K_DOWN] and red.y + SPACESHIP_HEIGHT + VEL < HEIGHT:
        red.y += VEL

def draw_winner(text):
    draw_text = WINNER_FONT.render(text, 1, "white")
    WIN.blit(draw_text, (WIDTH / 2 - draw_text.get_width() / 2, HEIGHT / 2 - draw_text.get_height() / 2))
    pygame.display.update()
    pygame.time.delay(4000)

# -------------------- Main Shooter Loop --------------------
def main_shooter():
    ASSETS_FOLDER = resource_path(join("assets", "Dual_game"))

    FPS = 60
    VEL = 5
    BULLET_VEL = 7
    MAX_BULLET = 5
    SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 55, 40
    BORDER = pygame.Rect(WIDTH//2 - 5, 0, 10, HEIGHT)
    
    # Load assets
    bg = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, '1v1.png')), (WIDTH, HEIGHT))
    red_ship = pygame.transform.rotate(
        pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'spaceship_red.png')), (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), 270
    )
    yellow_ship = pygame.transform.rotate(
        pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'spaceship_yellow.png')), (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), 90
    )
    bullet_hit_sound = pygame.mixer.Sound(join(ASSETS_FOLDER, 'Grenade+1.mp3'))
    bullet_fire_sound = pygame.mixer.Sound(join(ASSETS_FOLDER, 'Gun+Silencer.mp3'))

    # Initialize players
    red = pygame.Rect(700, 300, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)
    yellow = pygame.Rect(100, 300, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)
    red_bullets = []
    yellow_bullets = []
    red_health = 10
    yellow_health = 10

    clock = pygame.time.Clock()
    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LCTRL and len(yellow_bullets) < MAX_BULLET:
                    yellow_bullets.append(pygame.Rect(yellow.x + yellow.width, yellow.y + yellow.height // 2 - 2, 10, 5))
                    bullet_fire_sound.play()
                if event.key == pygame.K_RCTRL and len(red_bullets) < MAX_BULLET:
                    red_bullets.append(pygame.Rect(red.x, red.y + red.height // 2 - 2, 10, 5))
                    bullet_fire_sound.play()

        keys = pygame.key.get_pressed()
        handle_movement(keys, yellow, red, VEL, WIDTH, HEIGHT, BORDER, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)

        red_hits, yellow_hits = handle_bullets(yellow_bullets, red_bullets, yellow, red, BULLET_VEL, WIDTH, bullet_hit_sound)
        red_health -= red_hits
        yellow_health -= yellow_hits

        if red_health <= 0: 
            draw_winner("Yellow Wins!")
            return
        if yellow_health <= 0: 
            draw_winner("Red Wins!")
            return
       
        draw_window_shooter(WIN, WIDTH, HEIGHT, BORDER, red, yellow, red_bullets, yellow_bullets, red_health, yellow_health, bg, red_ship, yellow_ship, HEALTH_FONT)

# -------------------- Run --------------------
if __name__ == "__main__":
    main_shooter()
    pygame.quit()
