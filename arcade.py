import pygame
import os
import sys
import traceback
from os.path import join

from one_v_one import main_shooter
from Space_dodger import main_dodger
from game import main_menu

pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 900, 500
pygame.display.set_caption("Pygame Arcade Launcher")
WIN = pygame.display.set_mode((WIDTH, HEIGHT))

def load_font(size):
    return pygame.font.Font(join("assets", "Menu", "text", "Platform.TTF"), size)

LAUNCHER_TITLE_FONT = load_font(70) 
LAUNCHER_LABEL_FONT = load_font(25)

def launcher_screen():
    ASSETS_FOLDER = os.path.join(os.path.dirname(__file__), 'assets', 'Dual_game')
    launcher_bg = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'Arcade_BG.png')), (WIDTH, HEIGHT))
    arcade_img = pygame.transform.scale(pygame.image.load(join(ASSETS_FOLDER, 'arcade.png')), (250, 350))

    arcade1 = arcade_img.get_rect(center=(WIDTH//2 - 250, HEIGHT//2 + 75))
    arcade2 = arcade_img.get_rect(center=(WIDTH//2, HEIGHT//2 + 75))
    arcade3 = arcade_img.get_rect(center=(WIDTH//2 + 250, HEIGHT//2 + 75))

    label1 = LAUNCHER_LABEL_FONT.render("1v1 Shooter", True, "white")
    label2  = LAUNCHER_LABEL_FONT.render("Space Dodger", True, "black")
    label3 = LAUNCHER_LABEL_FONT.render("Platformer", True, "white")

    label1_rect = label1.get_rect(center=(arcade1.centerx, arcade1.bottom - 30))
    label2_rect = label2.get_rect(center=(arcade2.centerx, arcade2.bottom - 30))
    label3_rect = label3.get_rect(center=(arcade3.centerx, arcade3.bottom - 30))

    title_text = LAUNCHER_TITLE_FONT.render("PYGAME ARCADE", 1, "white")
    title_rect = title_text.get_rect(center=(WIDTH // 2, 50))

    clock = pygame.time.Clock()
    run = True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
                pos = event.pos
                if arcade1.collidepoint(event.pos): 
                    main_shooter()
                elif arcade2.collidepoint(pos):
                    main_dodger()       
                elif arcade3.collidepoint(pos):              
                    main_menu(WIN)

        WIN.blit(launcher_bg, (0, 0))
        WIN.blit(arcade_img, arcade1)
        WIN.blit(arcade_img, arcade2)
        WIN.blit(arcade_img, arcade3)

        WIN.blit(title_text, title_rect)
        WIN.blit(label1, label1_rect)
        WIN.blit(label2, label2_rect)
        WIN.blit(label3, label3_rect)
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
    # Bebugg imporitng as glitchy for 