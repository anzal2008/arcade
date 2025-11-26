import pygame
import os
import sys 
import random
import time

pygame.font.init()
pygame.mixer.init()

# Shooter 2 player constants
WIDTH, HEIGHT = 900, 500
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Arcade Launcher")

GAME_FOLDER = os.path.dirname(__file__)
ASSETS_FOLDER = os.path.join(GAME_FOLDER, 'Assets')

#ALL FONTS
HEALTH_FONT = pygame.font.SysFont('comicsans', 40)
WINNER_FONT = pygame.font.SysFont('comicsans', 100)
MENU_FONT = pygame.font.SysFont("comicsans", 60)
LAUNCHER_FONT = pygame.font.SysFont('comicsans', 70) 

#Shooter 2 player game param
FPS = 60
VEL = 5
BULLET_VEL = 7
MAX_BULLET = 3
YELLOW_HIT = pygame.USEREVENT + 1
RED_HIT = pygame.USEREVENT + 2
BORDER = pygame.Rect(WIDTH//2 - 5, 0, 10, HEIGHT)
SPACESHIP_WIDTH, SPACESHIP_HEIGTH = 55, 40

#Space Dodger Param
DODGER_WIDTH, DODGER_HEIGHT = 1000, 800
PLAYER_WIDTH = 40 
PLAYER_HEIGHT = 60 
PLAYER_VEL = 5
STAR_WIDTH = 30 
STAR_HEIGHT = 40
STAR_VEL = 3
DODGER_FONT = pygame.font.SysFont("comicsans", 30)

#Shooter assets
BULLET_HIT_SOUND = pygame.mixer.Sound(os.path.join(ASSETS_FOLDER, 'Grenade+1.mp3'))
BULLET_FIRE_SOUND = pygame.mixer.Sound(os.path.join(ASSETS_FOLDER, 'Gun+Silencer.mp3'))
YELLOW_SPACESHIP_IMAGE = pygame.image.load(os.path.join(ASSETS_FOLDER, 'spaceship_yellow.png'))
YELLOW_SPACESHIP = pygame.transform.rotate(pygame.transform.scale(YELLOW_SPACESHIP_IMAGE, (SPACESHIP_WIDTH, SPACESHIP_HEIGTH)), 90)
RED_SPACESHIP_IMAGE = pygame.image.load(os.path.join(ASSETS_FOLDER, 'spaceship_red.png'))
RED_SPACESHIP = pygame.transform.rotate(pygame.transform.scale(RED_SPACESHIP_IMAGE, (SPACESHIP_WIDTH, SPACESHIP_HEIGTH)), 270)
SPACE_IMAGE = pygame.image.load(os.path.join(ASSETS_FOLDER, 'space.png')) 

# DODGER ASSETS 
DODGER_BG_IMAGE = pygame.image.load(os.path.join(ASSETS_FOLDER, 'bg.jpeg'))
DODGER_PLAYER_IMAGE = pygame.image.load(os.path.join(ASSETS_FOLDER, 'spaceship.png'))
DODGER_STAR_IMAGE = pygame.image.load(os.path.join(ASSETS_FOLDER, 'asteroid.png'))

# Shooter 2 player game functions
def draw_window_shooter(red, yellow, red_bullets, yellow_bullets, red_health, yellow_health, SPACE): #kept in screen
    WIN.blit(SPACE, (0, 0)) 
    pygame.draw.rect(WIN, "black", BORDER)

    red_health_text = HEALTH_FONT.render("Health: " + str(red_health), 1, 'white')
    yellow_health_text = HEALTH_FONT.render("Health: " + str(yellow_health), 1, 'white')
    WIN.blit(red_health_text, (WIDTH - red_health_text.get_width() - 10, 10))
    WIN.blit(yellow_health_text, (10, 10))

    WIN.blit(RED_SPACESHIP, (red.x, red.y))
    WIN.blit(YELLOW_SPACESHIP, (yellow.x, yellow.y))

    for bullet in red_bullets:
        pygame.draw.rect(WIN, "red", bullet)

    for bullet in yellow_bullets:
        pygame.draw.rect(WIN, "yellow", bullet)

    pygame.display.update()

#Shooter Movement
def yellow_handle_movement(keys_pressed, yellow):
    if keys_pressed[pygame.K_a] and yellow.x - VEL > 0: #left
        yellow.x -= VEL
    if keys_pressed[pygame.K_d] and yellow.x + SPACESHIP_WIDTH + VEL < BORDER.x: #right
        yellow.x += VEL
    if keys_pressed[pygame.K_w] and yellow.y - VEL > 0: #up
        yellow.y -= VEL
    if keys_pressed[pygame.K_s] and yellow.y + SPACESHIP_HEIGTH + VEL < HEIGHT - 15: #down
        yellow.y += VEL

def red_handle_movement(keys_pressed, red):
    if keys_pressed[pygame.K_LEFT] and red.x - VEL > BORDER.x + 10: #left
        red.x -= VEL
    if keys_pressed[pygame.K_RIGHT] and red.x + SPACESHIP_WIDTH + VEL < WIDTH: #right
        red.x += VEL
    if keys_pressed[pygame.K_UP] and red.y - VEL > 0: #up
        red.y -= VEL
    if keys_pressed[pygame.K_DOWN] and red.y + SPACESHIP_HEIGTH + VEL < HEIGHT: #down
        red.y += VEL

def handle_bullets_shooter(yellow_bullets, red_bullets, yellow, red):
    for bullet in yellow_bullets:
        bullet.x += BULLET_VEL
        if red.colliderect(bullet):
            pygame.event.post(pygame.event.Event(RED_HIT))
            yellow_bullets.remove(bullet)
        elif bullet.x > WIDTH:
            yellow_bullets.remove(bullet)

    for bullet in red_bullets:
        bullet.x -= BULLET_VEL
        if yellow.colliderect(bullet):
            pygame.event.post(pygame.event.Event(YELLOW_HIT))
            red_bullets.remove(bullet)
        elif bullet.x < 0:
            red_bullets.remove(bullet)
#Shooter
def draw_winner_shooter(text):
    draw_text = WINNER_FONT.render(text, 1, "white")
    WIN.blit(draw_text, (WIDTH/2 - draw_text.get_width()/2, HEIGHT/2 - draw_text.get_height()/2))
    
    pygame.display.update()
    pygame.time.delay(4000)
    
# Main Shooter game itself
def main_shooter(): 
    pygame.display.set_caption("2-Shooter") 
    
    # Scale background to the current size
    SHOOTER_BG = pygame.transform.scale(SPACE_IMAGE, (WIDTH, HEIGHT))
    
    red = pygame.Rect(700,300, SPACESHIP_WIDTH, SPACESHIP_HEIGTH)
    yellow = pygame.Rect(100,300, SPACESHIP_WIDTH, SPACESHIP_HEIGTH)

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
                run = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LCTRL and len(yellow_bullets) < MAX_BULLET:
                    bullet = pygame.Rect(yellow.x + yellow.width, yellow.y + yellow.height//2 - 2, 10, 5)
                    yellow_bullets.append(bullet)
                    BULLET_FIRE_SOUND.play()
                
                if event.key == pygame.K_RCTRL and len(red_bullets) < MAX_BULLET:
                    bullet = pygame.Rect(red.x , red.y + red.height//2 - 2, 10, 5)
                    red_bullets.append(bullet)
                    BULLET_FIRE_SOUND.play()
                    
            if event.type == RED_HIT:
                red_health -= 1
                BULLET_HIT_SOUND.play()
            
            if event.type == YELLOW_HIT:
                yellow_health -= 1
                BULLET_HIT_SOUND.play()
                
        winner_text = ""
        if red_health <= 0:
            winner_text = "Yellow Wins!"

        if yellow_health <= 0:
            winner_text = "Red Wins!"

        if winner_text != "":
            draw_winner_shooter(winner_text)
            break
                
        keys_pressed = pygame.key.get_pressed()
        yellow_handle_movement(keys_pressed, yellow)
        red_handle_movement(keys_pressed, red)
        # Pass the scaled background image
        draw_window_shooter(red, yellow, red_bullets, yellow_bullets, red_health, yellow_health, SHOOTER_BG) 

        handle_bullets_shooter(yellow_bullets, red_bullets, yellow, red)

    return 

#Space dodger game functions

def draw_dodger(player, elapsed_time, stars, BG, PLAYER_IMAGE, STAR_IMAGE):
    WIN.blit(BG, (0,0))

    time_text = DODGER_FONT.render(f"Time: {round(elapsed_time)}s", 1, "white")
    WIN.blit(time_text, (10,10))

    WIN.blit(PLAYER_IMAGE, (player.x, player.y))
    
    for star in stars:
        WIN.blit(STAR_IMAGE, (star.x, star.y))

    pygame.display.update()

def lost_screen_dodger(final_time, BG):
  
    run = True

    button_text = MENU_FONT.render("Play Again", 1, "black")
    button_rect = button_text.get_rect(center=(DODGER_WIDTH / 2, DODGER_HEIGHT / 2 + 150))

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    main_dodger()
                    return 

        WIN.blit(BG, (0, 0))

        score_text = MENU_FONT.render(f"Time: {round(final_time)}s", 1, "white")
        WIN.blit(score_text, (DODGER_WIDTH / 2 - score_text.get_width() / 2, DODGER_HEIGHT / 2 - 100))

        pygame.draw.rect(WIN, "red", button_rect, border_radius=10)

        WIN.blit(button_text, button_rect)

        pygame.display.update()

def start_screen_dodger(BG):
   
    run = True

    start_text = MENU_FONT.render("START GAME!", 1, "black")
    start_rect = start_text.get_rect(center=(DODGER_WIDTH / 2, DODGER_HEIGHT / 2 + 100))

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    main_dodger()
                    return 

        WIN.blit(BG, (0, 0))

        title_text = MENU_FONT.render("SPACE DODGER", 1, "white")
        WIN.blit(title_text, (DODGER_WIDTH / 2 - title_text.get_width() / 2, DODGER_HEIGHT / 2 - 50))

        pygame.draw.rect(WIN, "green", start_rect, border_radius=10)
        WIN.blit(start_text, start_rect)

        pygame.display.update()

def main_dodger():
    global DODGER_WIDTH, DODGER_HEIGHT, DODGER_PLAYER_IMAGE, DODGER_STAR_IMAGE, PLAYER_WIDTH, PLAYER_HEIGHT, HEIGHT
    
    DODGER_BG = pygame.transform.scale(DODGER_BG_IMAGE, (DODGER_WIDTH, DODGER_HEIGHT))
    
    PLAYER_IMAGE = pygame.transform.scale(DODGER_PLAYER_IMAGE, (PLAYER_WIDTH, PLAYER_HEIGHT))
    PLAYER_MASK = pygame.mask.from_surface(PLAYER_IMAGE)
    
    STAR_IMAGE = pygame.transform.scale(DODGER_STAR_IMAGE, (STAR_WIDTH, STAR_HEIGHT))
    STAR_MASK = pygame.mask.from_surface(STAR_IMAGE)

    run = True
    
    player = PLAYER_IMAGE.get_rect()
    player.bottom = HEIGHT - 150
    player.x = 200
    
    clock = pygame.time.Clock()
    start_time = time.time()
    elapsed_time = 0

    star_add_increment = 2000
    star_count = 0

    stars = []
    hit = False

    while run:
        star_count += clock.tick(60)
        elapsed_time = time.time()- start_time

        if star_count > star_add_increment:
            for _ in range(3):
                star_rect = STAR_IMAGE.get_rect()
                star_rect.x = random.randint(0, DODGER_WIDTH - star_rect.width)
                star_rect.y = -star_rect.height
                stars.append(star_rect)

            star_add_increment = max(200, star_add_increment - 50)
            star_count = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        keys = pygame.key.get_pressed()
       
        if keys[pygame.K_RIGHT] and player.x + PLAYER_WIDTH + PLAYER_VEL <= DODGER_WIDTH:
            player.x += PLAYER_VEL
        if keys[pygame.K_LEFT] and player.x - PLAYER_VEL >=0:
            player.x -= PLAYER_VEL
        if keys[pygame.K_UP] and player.y - PLAYER_VEL >=0:
            player.y -= PLAYER_VEL
        if keys[pygame.K_DOWN]:
            new_bottom = player.bottom + PLAYER_VEL
            if new_bottom <= HEIGHT:
                player.y += PLAYER_VEL
            else:
                player.bottom = HEIGHT


        for star in stars[:]:
            star.y += STAR_VEL
            if star.y > HEIGHT:
                stars.remove(star)
            elif player.colliderect(star):
                x_offset = star.x - player.x
                y_offset = star.y - player.y
                
                if PLAYER_MASK.overlap(STAR_MASK, (x_offset, y_offset)):
                    hit = True
                    break

        if hit:
            break

        draw_dodger(player, elapsed_time, stars, DODGER_BG, PLAYER_IMAGE, STAR_IMAGE)
    
    
    if hit:
        lost_screen_dodger(elapsed_time, DODGER_BG) 
    
    return 

#Basic launch screen for my 3 games

def launcher_screen():
    global WIDTH, HEIGHT, WIN
    
    WIDTH, HEIGHT = 900, 500
    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pygame Arcade Launcher")
    
    SPACE_LAUNCHER = pygame.transform.scale(SPACE_IMAGE, (WIDTH, HEIGHT))

    run = True
    
    shooter_text = LAUNCHER_FONT.render("1. 2-PLAYER SHOOTER", 1, "yellow")
    shooter_rect = shooter_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    
    dodger_text = LAUNCHER_FONT.render("2. SPACE DODGER", 1, "red")
    dodger_rect = dodger_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    
    title_text = LAUNCHER_FONT.render("PYGAME ARCADE", 1, "white")
    title_rect = title_text.get_rect(center=(WIDTH // 2, 50))

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if shooter_rect.collidepoint(event.pos):
                    
                    main_shooter()
                  
                    
                if dodger_rect.collidepoint(event.pos):
                    
                   
                    WIDTH, HEIGHT = DODGER_WIDTH, DODGER_HEIGHT
                    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
                    pygame.display.set_caption("SPACE DODGER")
                    
                    main_dodger() 
                    
                   
                    WIDTH, HEIGHT = 900, 500
                    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
                    pygame.display.set_caption("Pygame Arcade Launcher")
                    
                   
                    SPACE_LAUNCHER = pygame.transform.scale(SPACE_IMAGE, (WIDTH, HEIGHT))
                    

        # Drawing the Launcher Screen
        WIN.blit(SPACE_LAUNCHER, (0, 0))
        WIN.blit(title_text, title_rect)
        WIN.blit(shooter_text, shooter_rect)
        WIN.blit(dodger_text, dodger_rect)
        
        pygame.display.update()

if __name__ == "__main__":
    launcher_screen()
    pygame.quit()