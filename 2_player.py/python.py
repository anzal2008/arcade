import pygame
import random
import time
pygame.font.init()

WIDTH, HEIGHT = 1000,800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SPACE DODGER")

BG = pygame.transform.scale(pygame.image.load("bg.jpeg"), (WIDTH, HEIGHT))

PLAYER_WIDTH = 40
PLAYER_HEIGHT = 60
PLAYER_VEL = 5

STAR_WIDTH = 30 
STAR_HEIGHT = 40
STAR_VEL = 3

FONT = pygame.font.SysFont("comicsans", 30)
MENU_FONT = pygame.font.SysFont("comicsans", 60)

PLAYER_IMAGE = pygame.image.load("spaceship.png")
PLAYER_IMAGE = pygame.transform.scale(PLAYER_IMAGE, (PLAYER_WIDTH, PLAYER_HEIGHT))
PLAYER_MASK = pygame.mask.from_surface(PLAYER_IMAGE)
                                    
STAR_IMAGE = pygame.image.load("asteroid.png")
STAR_IMAGE = pygame.transform.scale(STAR_IMAGE, (STAR_WIDTH, STAR_HEIGHT))
STAR_MASK = pygame.mask.from_surface(STAR_IMAGE)


def draw(player, elapsed_time, stars):
    WIN.blit(BG, (0,0))

    time_text = FONT.render(f"Time: {round(elapsed_time)}s", 1, "white")
    WIN.blit(time_text, (10,10))

    WIN.blit(PLAYER_IMAGE, (player.x, player.y))

    for star in stars:
        WIN.blit(STAR_IMAGE, (star.x, star.y))

    pygame.display.update()

    
def main():
    run = True
    
    player = PLAYER_IMAGE.get_rect()
    player.bottom = HEIGHT
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
                star_rect.x = random.randint(0, WIDTH - star_rect.width)
                star_rect.y = -star_rect.height
                stars.append(star_rect)

            star_add_increment = max(200, star_add_increment - 50)
            star_count = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT] and player.x + PLAYER_WIDTH + PLAYER_VEL <= WIDTH:
            player.x += PLAYER_VEL
        if keys[pygame.K_LEFT] and player.x - PLAYER_VEL >=0:
            player.x -= PLAYER_VEL
        if keys[pygame.K_UP] and player.y - PLAYER_VEL >=0:
            player.y -= PLAYER_VEL
        if keys[pygame.K_DOWN] and player.y + PLAYER_HEIGHT + PLAYER_VEL <= HEIGHT:
            player.y += PLAYER_VEL


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
            lost_text = FONT.render("You Lost!", 1, "white")
            WIN.blit(lost_text, (WIDTH/2 - lost_text.get_width()/2, HEIGHT/2 - lost_text.get_height()/2))
            pygame.display.update()
            pygame.time.delay(4000)
            break

        draw(player, elapsed_time, stars)
   
    last_screen(elapsed_time)
    
    pygame.quit()

def last_screen(final_time):
    run = True

    button_text = MENU_FONT.render("Play Again", 1, "black")
    button_rect = button_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 150))

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    main()
                    return
        
        WIN.blit(BG, (0, 0))

        score_text = MENU_FONT.render(f"Time: {round(final_time)}s", 1, "white")
        WIN.blit(score_text, (WIDTH / 2 - score_text.get_width() / 2, HEIGHT / 2 - 100))

        pygame.draw.rect(WIN, "red", button_rect, border_radius=10)

        WIN.blit(button_text, button_rect)

        pygame.display.update()

def start_screen():
    run = True

    start_text = MENU_FONT.render("START GAME!", 1, "black")
    start_rect = start_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 100))

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    main()
                    return
        
        WIN.blit(BG, (0, 0))

        title_text = MENU_FONT.render("SPACE DODGER", 1, "white")
        WIN.blit(title_text, (WIDTH / 2 - title_text.get_width() / 2, HEIGHT / 2 - 50))

        pygame.draw.rect(WIN, "green", start_rect, border_radius=10)
        WIN.blit(start_text, start_rect)

        pygame.display.update()

if __name__ == "__main__":
    import sys
    start_screen()