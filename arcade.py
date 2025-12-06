import pygame
import os
import sys
from os.path import join

from one_v_one import main_shooter
from Space_dodger import main_dodger
from game import main_menu, main as platformer_main   # <-- IMPORTANT FIX

pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 900, 500
pygame.display.set_caption("Pygame Arcade Launcher")
WIN = pygame.display.set_mode((WIDTH, HEIGHT))

# --------------------------
# Resource path function
# --------------------------
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --------------------------
# Load font via resource_path
# --------------------------
def load_font(size):
    return pygame.font.Font(resource_path(join("assets", "Menu", "text", "Platform.TTF")), size)

LAUNCHER_TITLE_FONT = load_font(70)
LAUNCHER_LABEL_FONT = load_font(25)

# --------------------------
# Launcher screen
# --------------------------
def launcher_screen():
    ASSETS_FOLDER = join("assets", "Dual_game")
    
    # Load background and arcade images using resource_path
    launcher_bg = pygame.transform.scale(
        pygame.image.load(resource_path(join(ASSETS_FOLDER, 'Arcade_BG.png'))),
        (WIDTH, HEIGHT)
    )
    arcade_img = pygame.transform.scale(
        pygame.image.load(resource_path(join(ASSETS_FOLDER, 'arcade.png'))),
        (250, 350)
    )

    # Arcade positions
    arcade1 = arcade_img.get_rect(center=(WIDTH//2 - 250, HEIGHT//2 + 75))
    arcade2 = arcade_img.get_rect(center=(WIDTH//2, HEIGHT//2 + 75))
    arcade3 = arcade_img.get_rect(center=(WIDTH//2 + 250, HEIGHT//2 + 75))

    # Labels
    label1 = LAUNCHER_LABEL_FONT.render("1v1 Shooter", True, "white")
    label2 = LAUNCHER_LABEL_FONT.render("Space Dodger", True, "black")
    label3 = LAUNCHER_LABEL_FONT.render("Platformer", True, "white")

    label1_rect = label1.get_rect(center=(arcade1.centerx, arcade1.bottom - 30))
    label2_rect = label2.get_rect(center=(arcade2.centerx, arcade2.bottom - 30))
    label3_rect = label3.get_rect(center=(arcade3.centerx, arcade3.bottom - 30))

    # Title
    title_text = LAUNCHER_TITLE_FONT.render("PYGAME ARCADE", True, "white")
    title_rect = title_text.get_rect(center=(WIDTH // 2, 50))

    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # 1v1 Shooter
                if arcade1.collidepoint(pos):
                    main_shooter()

                # Space Dodger
                elif arcade2.collidepoint(pos):
                    main_dodger()

                # Platformer
                elif arcade3.collidepoint(pos):
                    selected_map = main_menu(WIN)
                    if selected_map not in [None, "quit"]:
                        platformer_main(WIN, selected_map)

        # Draw everything
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
