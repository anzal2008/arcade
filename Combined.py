import pygame
import os
import sys
import random
import time
from os.path import join

pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 900, 500
FPS = 60
VEL = 5
BULLET_VEL = 7
MAX_BULLET = 3
SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 55, 40
BORDER = pygame.Rect(WIDTH // 2 - 5, 0, 10, HEIGHT)
# add platformer here?
PLAYER_WIDTH, PLAYER_HEIGHT = int(WIDTH * 0.05), int(HEIGHT * 0.12)
PLAYER_VEL = 5
STAR_WIDTH, STAR_HEIGHT = int(WIDTH * 0.035), int(HEIGHT * 0.08)
STAR_VEL = 3

pygame.display.set_caption("Pygame Arcade Launcher")
WIN = pygame.display.set_mode((WIDTH, HEIGHT))

def load_font(size):
    return pygame.font.Font(join("assets", "Menu", "text", "Platform.TTF"), size)

HEALTH_FONT = load_font(40)
WINNER_FONT = load_font(100)
MENU_FONT = load_font(60)
LAUNCHER_TITLE_FONT = load_font(70)
LAUNCHER_LABEL_FONT = load_font(25)

#Shootet game
def draw_window_shooter(red, yellow, red_bullets, yellow_bullets, red_health, yellow_health, bg, red_ship, yellow_ship):
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

def handle_bullets(yellow_bullets, red_bullets, yellow, red):
    for bullet in yellow_bullets:
        bullet.x += BULLET_VEL
        if red.colliderect(bullet):
            pygame.event.post(pygame.event.Event(pygame.USEREVENT + 2))  # RED_HIT
            yellow_bullets.remove(bullet)
        elif bullet.x > WIDTH:
            yellow_bullets.remove(bullet)

    for bullet in red_bullets:
        bullet.x -= BULLET_VEL
        if yellow.colliderect(bullet):
            pygame.event.post(pygame.event.Event(pygame.USEREVENT + 1))  # YELLOW_HIT
            red_bullets.remove(bullet)
        elif bullet.x < 0:
            red_bullets.remove(bullet)

def handle_movement(keys_pressed, yellow, red):
    # Yellow controls
    if keys_pressed[pygame.K_a] and yellow.x - VEL > 0:
        yellow.x -= VEL
    if keys_pressed[pygame.K_d] and yellow.x + SPACESHIP_WIDTH + VEL < BORDER.x:
        yellow.x += VEL
    if keys_pressed[pygame.K_w] and yellow.y - VEL > 0:
        yellow.y -= VEL
    if keys_pressed[pygame.K_s] and yellow.y + SPACESHIP_HEIGHT + VEL < HEIGHT - 15:
        yellow.y += VEL
    # Red controls
    if keys_pressed[pygame.K_LEFT] and red.x - VEL > BORDER.x + 10:
        red.x -= VEL
    if keys_pressed[pygame.K_RIGHT] and red.x + SPACESHIP_WIDTH + VEL < WIDTH:
        red.x += VEL
    if keys_pressed[pygame.K_UP] and red.y - VEL > 0:
        red.y -= VEL
    if keys_pressed[pygame.K_DOWN] and red.y + SPACESHIP_HEIGHT + VEL < HEIGHT:
        red.y += VEL

def draw_winner(text):
    draw_text = WINNER_FONT.render(text, 1, "white")
    WIN.blit(draw_text, (WIDTH / 2 - draw_text.get_width() / 2, HEIGHT / 2 - draw_text.get_height() / 2))
    pygame.display.update()
    pygame.time.delay(4000)

def main_shooter():
    ASSETS_FOLDER = os.path.join(os.path.dirname(__file__), 'assets', 'Dual_game')
    bg = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, '1v1.png')), (WIDTH, HEIGHT))
    red_ship = pygame.transform.rotate(pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'spaceship_red.png')), (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), 270)
    yellow_ship = pygame.transform.rotate(pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'spaceship_yellow.png')), (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), 90)
    bullet_hit_sound = pygame.mixer.Sound(join(ASSETS_FOLDER, 'Grenade+1.mp3'))
    bullet_fire_sound = pygame.mixer.Sound(join(ASSETS_FOLDER, 'Gun+Silencer.mp3'))

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
            if event.type == pygame.USEREVENT + 2:  # RED_HIT
                red_health -= 1
                bullet_hit_sound.play()
            if event.type == pygame.USEREVENT + 1:  # YELLOW_HIT
                yellow_health -= 1
                bullet_hit_sound.play()

        winner_text = ""
        if red_health <= 0: winner_text = "Yellow Wins!"
        if yellow_health <= 0: winner_text = "Red Wins!"
        if winner_text != "":
            draw_winner(winner_text)
            return

        keys_pressed = pygame.key.get_pressed()
        handle_movement(keys_pressed, yellow, red)
        handle_bullets(yellow_bullets, red_bullets, yellow, red)
        draw_window_shooter(red, yellow, red_bullets, yellow_bullets, red_health, yellow_health, bg, red_ship, yellow_ship)
#Space dodger game
def draw_dodger(player, elapsed_time, stars, bg, player_img, star_img):
    WIN.blit(bg, (0, 0))
    time_text = MENU_FONT.render(f"Time: {round(elapsed_time)}s", 1, "white")
    WIN.blit(time_text, (10, 10))
    WIN.blit(player_img, (player.x, player.y))
    for star in stars:
        WIN.blit(star_img, (star.x, star.y))
    pygame.display.update()

def lost_screen_dodger(final_time, bg, player_img, star_img):
    run = True
    button_text = MENU_FONT.render("Play Again", 1, "black")
    button_rect = button_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 150))
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos): main_dodger(); return
        WIN.blit(bg, (0, 0))
        score_text = MENU_FONT.render(f"Time: {round(final_time)}s", 1, "white")
        WIN.blit(score_text, (WIDTH / 2 - score_text.get_width() / 2, HEIGHT / 2 - 100))
        pygame.draw.rect(WIN, "red", button_rect, border_radius=10)
        WIN.blit(button_text, button_rect)
        pygame.display.update()

def main_dodger():
    ASSETS_FOLDER = os.path.join(os.path.dirname(__file__), 'assets', 'Dual_game')
    bg = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'bg.jpeg')), (WIDTH, HEIGHT))
    player_img = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'spaceship.png')), (PLAYER_WIDTH, PLAYER_HEIGHT))
    star_img = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'asteroid.png')), (STAR_WIDTH, STAR_HEIGHT))
    player_mask = pygame.mask.from_surface(player_img)
    star_mask = pygame.mask.from_surface(star_img)

    player = player_img.get_rect(midbottom=(200, HEIGHT - 150))
    stars = []
    elapsed_time = 0
    clock = pygame.time.Clock()
    start_time = time.time()
    star_timer = 0
    run = True
    while run:
        dt = clock.tick(FPS)
        star_timer += dt
        elapsed_time = time.time() - start_time
        if star_timer > 2000:
            for _ in range(3):
                star_rect = star_img.get_rect(x=random.randint(0, WIDTH - STAR_WIDTH), y=-STAR_HEIGHT)
                stars.append(star_rect)
            star_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT] and player.x + PLAYER_WIDTH + PLAYER_VEL <= WIDTH: player.x += PLAYER_VEL
        if keys[pygame.K_LEFT] and player.x - PLAYER_VEL >= 0: player.x -= PLAYER_VEL
        if keys[pygame.K_UP] and player.y - PLAYER_VEL >= 0: player.y -= PLAYER_VEL
        if keys[pygame.K_DOWN]:
            if player.bottom + PLAYER_VEL <= HEIGHT: player.y += PLAYER_VEL
            else: player.bottom = HEIGHT

        hit = False
        for star in stars[:]:
            star.y += STAR_VEL
            if star.y > HEIGHT: stars.remove(star)
            elif player.colliderect(star):
                x_offset, y_offset = star.x - player.x, star.y - player.y
                if player_mask.overlap(star_mask, (x_offset, y_offset)):
                    hit = True
                    break
        if hit: lost_screen_dodger(elapsed_time, bg, player_img, star_img); return
        draw_dodger(player, elapsed_time, stars, bg, player_img, star_img)

# Launcher
def launcher_screen():
    ASSETS_FOLDER = os.path.join(os.path.dirname(__file__), 'assets', 'Dual_game')
    launcher_bg = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'Arcade_BG.png')), (WIDTH, HEIGHT))
    arcade_img = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'arcade.png')), (250, 350))

    arcade1_rect = arcade_img.get_rect(center=(WIDTH//2 - 250, HEIGHT//2 + 75))
    arcade2_rect = arcade_img.get_rect(center=(WIDTH//2, HEIGHT//2 + 75))
    arcade3_rect = arcade_img.get_rect(center=(WIDTH//2 + 250, HEIGHT//2 + 75))

    label_shooter = LAUNCHER_LABEL_FONT.render("1v1 Shooter", True, "white")
    label_dodger = LAUNCHER_LABEL_FONT.render("Space Dodger", True, "white")
    label_platformer = LAUNCHER_LABEL_FONT.render("Platformer", True, "white")

    label_shooter_rect = label_shooter.get_rect(center=(arcade1_rect.centerx, arcade1_rect.bottom - 30))
    label_dodger_rect = label_dodger.get_rect(center=(arcade2_rect.centerx, arcade2_rect.bottom - 30))
    label_platformer_rect = label_platformer.get_rect(center=(arcade3_rect.centerx, arcade3_rect.bottom - 30))

    title_text = LAUNCHER_TITLE_FONT.render("PYGAME ARCADE", 1, "white")
    title_rect = title_text.get_rect(center=(WIDTH // 2, 50))

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if arcade1_rect.collidepoint(event.pos): main_shooter()
                if arcade2_rect.collidepoint(event.pos): main_dodger()
                if arcade3_rect.collidepoint(event.pos): print("Platformer tbd")

        WIN.blit(launcher_bg, (0, 0))
        WIN.blit(arcade_img, arcade1_rect)
        WIN.blit(arcade_img, arcade2_rect)
        WIN.blit(arcade_img, arcade3_rect)
        WIN.blit(title_text, title_rect)
        WIN.blit(label_shooter, label_shooter_rect)
        WIN.blit(label_dodger, label_dodger_rect)
        WIN.blit(label_platformer, label_platformer_rect)
        pygame.display.update()

if __name__ == "__main__":
    launcher_screen()
    pygame.quit()
    #FINAL TOUCHES
    # add a few more simple improvment to all the games 
    # make so buyttons wrokm everywhere and is seamless
    # eventall;y add transtion ot each game
    # have a goal of achievenmtn top done "finish" the game
    # imporvwe fonts and than submit game 1 week lets go
    # Combine code to see how it works than add setting all that good stf eheh