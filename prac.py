import pygame
import os
import math
import sys
import json
import random
from os import listdir
from os.path import isfile, join, exists

pygame.init()
pygame.mixer.init()
pygame.font.init()

WIDTH, HEIGHT = 1000, 800
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platformer")

FPS = 60
PLAYER_VEL = 8
BASE_TILE_SIZE = 32
EDITOR_BLOCK_SIZE = 96
LIVES_START = 3
DEATH_PLANE_HEIGHT = HEIGHT + 200
AIR_DRAG = 0.95

TIME_FOR_3_STARS = 60.0
TIME_FOR_2_STARS = 120.0
TIME_FOR_1_STARS = 180.0

LEVEL_COMPLETE_ASSETS = {
    3: join("assets", "other", "level_complete_3.png"),
    2: join("assets", "other", "level_complete_2.png"),
    1: join("assets", "other", "level_complete_1.png"),
    0: join("assets", "other", "level_complete_0.png"),
}

BACKGROUND_MAPPING = {
    "level_data_1.json": "Blue.png",
    "level_data_2.json": "Brown.png",
    "level_data_3.json": "Purple.png",
    "level_data_4.json": "Yellow.png",
    "level_data_5.json": "Green.png",
    "level_data_6.json": "Pink.png",
}


PARTICLE_MAPPING = {
    'ice': join("assets", "Traps", "Climate", "Iceparticle.png"),
    'mud': join("assets", "Traps", "Climate", "Mudparticle.png"),
    'regular': join("assets", "Traps", "Climate", "Sandparticle.png"),
}

MAP_FILES = {
    pygame.K_1: 'level_data_1.json',
    pygame.K_2: 'level_data_2.json',
    pygame.K_3: 'level_data_3.json',
    pygame.K_4: 'level_data_4.json',
    pygame.K_5: 'level_data_5.json',
    pygame.K_6: 'level_data_6.json',
}

def try_font(path, size):
    return pygame.font.Font(path, size)

FONT = try_font(join("assets", "Menu", "Text", "Platform.TTF"), 40)
MENU_FONT = try_font(join("assets", "Menu", "Text", "Platform.TTF"), 80)

# Utilities and definitions
def load_image(path, fallback_size=(32, 32)):
    return pygame.image.load(path).convert_alpha()

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    files = [f for f in listdir(path) if isfile(join(path, f))]
    all_sprites = {}

    for image in files:
        sheet = load_image(join(path, image), (width, height))
        sprites = []

        for i in range(sheet.get_width() // width):
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            rect = pygame.Rect(i * width, 0, width, height)
            surf.blit(sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surf))
        
        name = image.replace('.png', '')
        key = ('idle' if 'Idle' in name else 'run' if 'Run' in name else 'jump' if 'Jump' in name else 'fall' if 'Fall' in name else 'hit' if 'Hit' in name else name.lower())
        
        if direction:
            all_sprites[key + '_right'] = sprites
            all_sprites[key + '_left'] = [pygame.transform.flip(s, True, False) for s in sprites]
        else:
            all_sprites[key] = sprites
    return all_sprites

def cut_spritesheet(sheet, fw, fh, count=None):
    frames = []
    if sheet is None:
        return frames
    max_count = sheet.get_width() // fw if fw > 0 else 0
    total = count if count is not None else max_count
    for i in range(min(total, max_count)):
        rect = (i * fw, 0, fw, fh)
        frames.append(sheet.subsurface(rect).copy())
    return frames

def get_background(name):
    path = join("assets", "Background", name)
    img = load_image(path, (WIDTH, HEIGHT)).convert()
    return img, img.get_width(), img.get_height()

def get_block_variant(size, sx, sy):
    path = join("assets", "Terrain", "Terrain.png")
    img = load_image(path, (BASE_TILE_SIZE, BASE_TILE_SIZE))
    surf = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE), pygame.SRCALPHA)
    surf.blit(img, (0, 0), pygame.Rect(sx, sy, BASE_TILE_SIZE, BASE_TILE_SIZE))
    return pygame.transform.scale(surf, (size, size))

def get_special_block_variant(size, sx, sy):
    path = join("assets", "Traps", "Climate", "Special.png")
    TILE_SIZE = 48
    img = load_image(path, (TILE_SIZE, TILE_SIZE))
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    surf.blit(img, (0, 0), pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE))

    return pygame.transform.scale(surf, (size, size))

# Base object classes
class BaseObject(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.width = w
        self.height = h
        self.name = name
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, win, ox, oy):
        win.blit(self.image, (self.rect.x - ox, self.rect.y - oy))

    def loop(self):
        return

class Block(BaseObject):
    def __init__(self, x, y, size, vx=96, vy=0):
        super().__init__(x, y, size, size, name='block')
        self.variant_x = vx
        self.variant_y = vy
        self.image = get_block_variant(size, vx, vy)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        if size == 48:
            self.name = 'tiny_block'

class SpecialBlock(BaseObject):
    def __init__(self, x, y, name, size=EDITOR_BLOCK_SIZE, vx=0, vy=0):
        super().__init__(x, y, size, size, name)
        self.variant_x = vx
        self.variant_y = vy

        if name == "mud":
            vx = 0
        elif name == "grass":
            vx = 64
        elif name == "ice":
            vx = 128

        self.image = get_special_block_variant(size, vx, vy)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

class AnimatedObject(BaseObject):
    def __init__(self, x, y, w, h, name, sheet_path, frame_size, anim_delay=5):
        super().__init__(x, y, w, h, name=name)
        sheet = load_image(sheet_path, (frame_size[0], frame_size[1]))
        fw, fh = frame_size
        self.frames = []
        if sheet and fw > 0:
            for i in range(sheet.get_width() // fw):
                fr = pygame.Surface((fw, fh), pygame.SRCALPHA)
                fr.blit(sheet, (0, 0), (i * fw, 0, fw, fh))
                self.frames.append(pygame.transform.scale(fr, (w, h)))
        self.anim_delay = anim_delay
        self.anim_count = 0
        if self.frames:
            self.image = self.frames[0]
            self.mask = pygame.mask.from_surface(self.image)

    def loop(self):
        if not getattr(self, 'frames', None):
            return
        idx = (self.anim_count // self.anim_delay) % len(self.frames)
        self.image = self.frames[idx]
        self.mask = pygame.mask.from_surface(self.image)
        self.anim_count += 1

class SpikeHead(AnimatedObject):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, 'spike_head', join('assets', 'Traps', 'Spike Head', 'Blink.png'), (54, 52), anim_delay=6)

class Fire(AnimatedObject):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, 'fire', join('assets', 'Traps', 'Fire', 'on.png'), (16, 32), anim_delay=3)

class Saw(AnimatedObject):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, 'saw', join('assets', 'Traps', 'saw', 'on.png'), (38, 38), anim_delay=2)

class CheckPoint(AnimatedObject):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, 'check_point', join('assets', 'Items', 'Checkpoints', 'Checkpoint', 'Idle.png'), (64, 64), anim_delay=5)

class StartPoint(AnimatedObject):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, 'start_point', join('assets', 'Items', 'Checkpoints', 'Start', 'start.png'), (64, 64), anim_delay=6)

class EndPoint(AnimatedObject):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, 'end_point', join('assets', 'Items', 'Checkpoints', 'End', 'end.png'), (64, 64), anim_delay=6)

class Particle(BaseObject):
    def __init__(self, x, y, image_path, velocity=(0,0), lifetime = 20):
        super().__init__(x, y, 10, 19, name='particle')

        img = load_image(image_path, (5, 5))
        self.image = pygame.transform.scale(img, (10, 10))

        self.rect = self.image.get_rect(center=(x, y))
        self.x_vel, self.y_vel = velocity
        self.lifetime = lifetime
        self.current_age = 0
        
        angle = pygame.time.get_ticks() % 360
        self.image = pygame.transform.rotate(self.image, angle)

    def update(self):
        self.rect.x += self.x_vel
        self.rect.y += self.y_vel

        self.y_vel += 0.5

        self.current_age += 1
        alpha = 255 - int(255 * (self.current_age / self.lifetime))
        self.image.set_alpha(max(0, alpha))
        
        if self.current_age > self.lifetime:
            self.kill()

class Trampoline(BaseObject):
    WIDTH = EDITOR_BLOCK_SIZE
    HEIGHT = int(EDITOR_BLOCK_SIZE * 0.35)
    BOUNCE_VELOCITY = -44 #Trampoline jump height
    ANIM_DELAY = 4

    _idle = pygame.transform.scale(load_image("assets/Traps/Trampoline/Idle.png"), (WIDTH, HEIGHT))
    _jump_frames = [pygame.transform.scale(f, (WIDTH, HEIGHT)) for f in cut_spritesheet(load_image("assets/Traps/Trampoline/Jump.png"), 282, 28, count=8)]

    def __init__(self, x, y):
        super().__init__(x, y, Trampoline.WIDTH, Trampoline.HEIGHT, name='trampoline')
        self.idle = Trampoline._idle
        self.frames = Trampoline._jump_frames or [self.idle]
        self.image = self.idle
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.anim_idx = 0
        self.anim_count = 0
        self.animating = False

    def loop(self):
        if not self.animating:
            self.image = self.idle
            return
        self.anim_count += 1
        if self.anim_count % Trampoline.ANIM_DELAY == 0:
            self.anim_idx += 1
            if self.anim_idx >= len(self.frames):
                self.anim_idx = 0
                self.animating = False
                self.image = self.idle
            else:
                self.image = self.frames[self.anim_idx]
        self.mask = pygame.mask.from_surface(self.image)

    def bounce(self, player):
        player.y_vel = Trampoline.BOUNCE_VELOCITY
        self.animating = True
        self.anim_idx = 0
        self.anim_count = 0

# Player class
class Player(pygame.sprite.Sprite):
    GRAVITY = 1
    SPRITES = load_sprite_sheets('MainCharacters', 'MaskDude', 32, 32, True)
    ANIM_DELAY = 3

    def __init__(self, x, y, w, h):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.x_vel = 0
        self.y_vel = 0
        self.direction = 'right'
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.lives = LIVES_START
        self.lives_invincibility_timer = 0
        self.start_pos = (x, y)
        self.sprite = self.SPRITES.get('idle_right', [pygame.Surface((w, h), pygame.SRCALPHA)])[0]
        self.update()

        self.terrain_modifier = 1.0
        self.terrain_friction = 0.9

        self.jump_boost = False
        self.jump_boost_timer = 0
        self.jump_boost_duration = FPS * 5        

        self.melon_active = False
        self.current_terrain_effect = 'regular'
        self.terrain_decay_timer = 0

        self.heart_image = load_image(join('assets', 'Other', 'heart.png'))
        self.heart_image = pygame.transform.scale(self.heart_image, (48, 48))
        self.heart_size = self.heart_image.get_width()
        self.heart_padding = 10

    def jump(self):
        if self.current_terrain_effect == 'mud':
            jump_factor = 4
        else:
            jump_factor = 8

        if self.jump_boost:
            jump_factor *= 1.6     

        self.y_vel = -self.GRAVITY * jump_factor
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel * self.terrain_modifier
        if self.direction != 'left':
            self.direction = 'left'
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel * self.terrain_modifier
        if self.direction != 'right':
            self.direction = 'right'
            self.animation_count = 0

    def make_hit(self):
        if self.lives_invincibility_timer <= 0:
            self.hit = True

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        if self.jump_count > 0:
            self.x_vel *= AIR_DRAG
            if abs(self.x_vel) < 0.1:
                self.x_vel = 0
        self.move(self.x_vel, self.y_vel)
        if self.hit:
            pass
        self.fall_count += 1
        self.update_sprite()
        if self.lives_invincibility_timer > 0:
            self.lives_invincibility_timer -= 1

        if self.jump_boost_timer > 0:
            self.jump_boost_timer -= 1
            if self.jump_boost_timer <= 0:
                self.jump_boost = False

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.fall_count = 0
        self.y_vel = 0

    def update_sprite(self):
        sheet = 'idle'
        if self.hit:
            sheet = 'hit'
        elif self.y_vel < 0:
            sheet = 'jump'
        elif self.y_vel > self.GRAVITY * 2:
            sheet = 'fall'
        elif self.x_vel != 0:
            sheet = 'run'
        key = sheet + '_' + self.direction
        sprites = self.SPRITES.get(key, self.SPRITES.get('idle_' + self.direction, [pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)]))
        idx = (self.animation_count // self.ANIM_DELAY) % len(sprites)
        self.sprite = sprites[idx]
        self.animation_count += 1
        if self.lives_invincibility_timer > 0 and (self.lives_invincibility_timer // 6) % 2 == 0:
            self.sprite.set_alpha(100)
        else:
            self.sprite.set_alpha(255)
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, ox, oy, inv):
        win.blit(self.sprite, (self.rect.x - ox, self.rect.y - oy))

class Fruit(BaseObject):
    FRUIT_SIZE = 48
    ANIM_DELAY = 6
    FRAME_SIZE = 32

    MELON = load_image(join("assets", "Items", "Fruits", "Melon.png"))
    PINEAPPLE = load_image(join("assets", "Items", "Fruits", "Pineapple.png"))
    STRAWBERRY = load_image(join("assets", "Items", "Fruits", "Strawberry.png"))

    FRUIT_ASSETS = {
        "melon": (MELON, (FRAME_SIZE, FRAME_SIZE)),
        "pineapple": (PINEAPPLE, (FRAME_SIZE, FRAME_SIZE)),
        "strawberry": (STRAWBERRY, (FRAME_SIZE, FRAME_SIZE)),
    }

    def __init__(self, x, y, name):
        super().__init__(x, y, self.FRUIT_SIZE, self.FRUIT_SIZE, name)

        sheet, (fw, fh) = self.FRUIT_ASSETS[name]

        self.frames = []
        for i in range(sheet.get_width() // fw):
            frame = pygame.Surface((fw, fh), pygame.SRCALPHA)
            frame.blit(sheet, (0,0), (i * fw, 0, fw, fh))
            self.frames.append(pygame.transform.scale(frame, (self.FRUIT_SIZE, self.FRUIT_SIZE)))

        self.animation_count = 0
        self.mask = pygame.mask.from_surface(self.image)
        self.anim_delay = self.ANIM_DELAY
        self.image = self.frames[0]

    def loop(self):
        idx = (self.animation_count // self.anim_delay) % len(self.frames)
        self.image = self.frames[idx]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)

class Button:
    def __init__(self, x, y, image_path, map_file=None):
        self.map_file = map_file
        img = load_image(image_path, (96, 96))
        self.image = pygame.transform.scale(img, (96, 96))
        self.rect = self.image.get_rect(topleft=(x, y))
    def draw(self, surf):
        surf.blit(self.image, self.rect.topleft)
    def check_click(self, pos):
        return self.rect.collidepoint(pos)

class GameButton(Button):
    def __init__(self, x, y, image_path, size, map_file=None):
        img = load_image(image_path, size)
        self.image = pygame.transform.scale(img, size)
        self.rect = self.image.get_rect(topleft=(x, y))
    def check_click(self, pos):
        return self.rect.collidepoint(pos)
    
# Save / Load level
def save_map(objects, key):
    fname = MAP_FILES[key]
    FULL_PATH = join("assets", "Maps", fname)
    data = []
    for o in objects:
        item = {'name': o.name, 'x': o.rect.x, 'y': o.rect.y, 'width': o.width, 'height': o.height}
        if getattr(o, 'variant_x', None) is not None:
            item['variant_x'] = o.variant_x
            item['variant_y'] = getattr(o, 'variant_y', 0)
        data.append(item)
    with open(FULL_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def load_map(filename='level_data_1.json', block_size=EDITOR_BLOCK_SIZE):
    FULL_PATH = join("assets", "Maps", filename)
    if not exists(FULL_PATH):
        return [], None
    with open(FULL_PATH, 'r') as f:
        data = json.load(f)
    return load_level(data, block_size)

def load_level(data, block_size):
    objects = []
    start_pos = None 
    for item in data:
        name = item.get('name')
        x = item.get('x', 0)
        y = item.get('y', 0)
        if name == 'block':
            objects.append(Block(x, y, block_size, item.get('variant_x', 96), item.get('variant_y', 0)))
        elif name == 'tiny_block':
            objects.append(Block(x, y, 48, item.get('variant_x', 144), item.get('variant_y', 0)))
        elif name in ('mud', 'grass', 'ice'):
                      objects.append(SpecialBlock(x, y, name, block_size, item.get('variant_x', 0),item.get('varaint_y', 0)))
        elif name == 'fire':
            fire_w, fire_h = BASE_TILE_SIZE, BASE_TILE_SIZE * 2
            objects.append(Fire(x, y, BASE_TILE_SIZE, BASE_TILE_SIZE * 2))
        elif name == 'spike_head':
            objects.append(SpikeHead(x, y, BASE_TILE_SIZE * 2, BASE_TILE_SIZE * 2))
        elif name == 'saw':
            objects.append(Saw(x, y, BASE_TILE_SIZE * 2, BASE_TILE_SIZE * 2))
        elif name == 'trampoline':
            objects.append(Trampoline(x, y))
        elif name in ("melon", "pineapple", "strawberry"):
            objects.append(Fruit(x, y, name))
        elif name == 'start_point':
            start_pos = (x, y)
            objects.append(StartPoint(x, y, block_size))
        elif name == 'end_point':
            objects.append(EndPoint(x, y, block_size))
        elif name in ('check_point', 'checkpoint'):
            objects.append(CheckPoint(x, y, block_size))
    return objects, start_pos

# Editor utilities
def get_menu_background(name='Menu.jpg'):
    path = join('assets', 'Background', name)
    img = load_image(path, (WIDTH, HEIGHT))
    return pygame.transform.scale(img, (WIDTH, HEIGHT))

def draw_hud(window, player):
    start_x = 10
    for i in range(player.lives):
        x = start_x + i * (player.heart_size + player.heart_padding)
        window.blit(player.heart_image, (x, 10))

def draw(window, bg_image, bg_w, bg_h, player, objects, ox, oy, inv, game_over=False, level_complete=False):
    parallax = 0.5
    bg_ox = int(ox * parallax)
    bg_oy = int(oy * parallax)
    start_x = math.floor(bg_ox / bg_w) * bg_w
    start_y = math.floor(bg_oy / bg_h) * bg_h
    for x in range(start_x, start_x + WIDTH + bg_w, bg_w):
        for y in range(start_y, start_y + HEIGHT + bg_h, bg_h):
            window.blit(bg_image, (x - bg_ox, y - bg_oy))
    for obj in objects:
        obj.draw(window, ox, oy)
    player.draw(window, ox, oy, inv)
    draw_hud(window, player)
    if game_over:
        t = FONT.render('GAME OVER! Resetting', True, (255, 0, 0))
        window.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2))
    
def draw_completion_screen(window, current_time, restart_btn, close_btn):
    win_w, win_h = window.get_size()
    
    dim_surface = pygame.Surface((win_w, win_h))
    dim_surface.set_alpha(150)
    dim_surface.fill(('black'))
    window.blit(dim_surface, (0, 0))

    if current_time <= TIME_FOR_3_STARS:
        stars_achieved = 3
    elif current_time <= TIME_FOR_2_STARS:
        stars_achieved = 2
    elif current_time <= TIME_FOR_1_STARS:
        stars_achieved = 1
    else:
        stars_achieved = 0

    completion_image_path = LEVEL_COMPLETE_ASSETS.get(stars_achieved, LEVEL_COMPLETE_ASSETS.get(1))
    completion_image = load_image(completion_image_path, (500, 300))

    target_width = 600
    if completion_image.get_width() > target_width:
        scale_factor = target_width / completion_image.get_width()
        completion_image = pygame.transform.scale(
            completion_image,
            (target_width, int(completion_image.get_height() * scale_factor))
        )

    image_x = (win_w - completion_image.get_width()) // 2
    image_y = (win_h - completion_image.get_height()) // 2 - 100
    window.blit(completion_image, (image_x, image_y))

    time_text = FONT.render(f"Time: {current_time:.2f} seconds", 1, (255, 255, 255))

    time_text_x = (win_w - time_text.get_width()) //2
    time_text_y = image_y + completion_image.get_height() + 20
    window.blit(time_text, (time_text_x, time_text_y))

    btn_size = restart_btn.image.get_width()
    button_padding = 40
    total_btns_width = (2 * btn_size) + button_padding

    start_btn_x = (win_w - total_btns_width) // 2
    btn_y = time_text_y + time_text.get_height() + 30

    restart_btn.rect.topleft = (start_btn_x, btn_y)
    restart_btn.draw(window)

    close_btn.rect.topleft = (start_btn_x + btn_size + button_padding, btn_y)
    close_btn.draw(window)

# Collision & Movement
def handle_vertical_collision(player, objects, dy):
    collidable = [o for o in objects if o.name in ('block', 'tiny_block', 'mud', 'grass', 'ice')]
    collided = []
    for o in collidable:
        if pygame.sprite.collide_mask(player, o):
            if dy > 0:
                player.rect.bottom = o.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = o.rect.bottom
                player.hit_head()
            collided.append(o)
    return collided

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    result = None
    for o in [x for x in objects if x.name in ('block', 'tiny_block', 'end_point')]:
        if pygame.sprite.collide_mask(player, o):
            result = o
            break
    player.move(-dx, 0)
    player.update()
    return result

def handle_end_collision(player, objects):
    for o in objects:
        if o.name == 'end_point' and pygame.sprite.collide_mask(player, o):
            return True
    return False

def handle_special_terrain(player, objects):
    player.move(0, 1) 
    special_blocks = [o for o in objects if isinstance(o, SpecialBlock)]
    collided_blocks = pygame.sprite.spritecollide(player, objects, False, pygame.sprite.collide_mask)
    player.move(0, -1)

    on_special_block = False

    for obj in collided_blocks:
        player_bottom = player.rect.bottom
        obj_top = obj.rect.top

        if player_bottom >= obj_top and player_bottom < obj_top + 10:
            on_special_block = True
            
            if obj.name == 'ice':
                player.current_terrain_effect = 'ice'
                player.terrain_decay_time = 3
                break
            elif obj.name == 'mud':
                player.current_terrain_effect = 'mud'
                player.terrain_decay_time = 3
                break
            elif obj.name != 'grass':
                player.current_terrain_effect = 'grass'
                player.terrain_decay_time = 3
                break
                
    if player.current_terrain_effect == 'ice':
        player.terrain_friction = 1.2 # ICE FRICION
        player.terrain_modifier = 1.5 # ICE SPEED
    elif player.current_terrain_effect == 'mud':
        player.terrain_friction = 0.2 # MUD FRICION
        player.terrain_modifier = 0.3 # MUD SPEED
    else:
        player.terrain_friction = 0.8 # REGULAR FRICTION
        player.terrain_modifier = 1 # REGULAR SPEED

    if not on_special_block and player.terrain_decay_timer > 0:
        player.terrain_decay_timer -= 1
        if player.melon_active:
            player.terrain_modifier = 2
            player.terrain_friction = 0.8
    if player.terrain_decay_timer == 0 and not on_special_block:     
        player.current_terrain_effect = 'regular'
        player.melon_active = False

def handle_move(player, objects, particles):
    handle_special_terrain(player, objects)
    keys = pygame.key.get_pressed()
    player_speed = PLAYER_VEL * player.terrain_modifier

    desired_x_vel = 0
    if keys[pygame.K_LEFT]: 
        player.move_left(PLAYER_VEL)
        desired_x_vel = player.x_vel
    if keys[pygame.K_RIGHT]: 
        player.move_right(PLAYER_VEL)
        desired_x_vel = player.x_vel

    if desired_x_vel == 0 and player.jump_count == 0:
        player.x_vel *= player.terrain_friction

        if abs(player.x_vel) < 0.5:
            player.x_vel = 0
    else:
        if desired_x_vel != 0:
            max_speed = PLAYER_VEL * player.terrain_modifier
            player.x_vel = max(min(player.x_vel, max_speed), -max_speed)
            pass
        else:
            pass

    if player.x_vel != 0 and collide(player, objects, player.x_vel):
        player.x_vel = 0
   
    handle_vertical_collision(player, objects, player.y_vel)

    for trap in [o for o in objects if o.name in ('fire', 'spike_head', 'saw')]:
        if pygame.sprite.collide_mask(player, trap) and player.lives_invincibility_timer <= 0:
            player.make_hit()
   
    for cp in [o for o in objects if o.name == 'check_point']:
        if pygame.sprite.collide_mask(player, cp):
            player.start_pos = (cp.rect.x, cp.rect.y)
   
    for t in [o for o in objects if o.name == 'trampoline']:
        if player.rect.colliderect(t.rect) and player.y_vel >= 0 and player.rect.bottom <= t.rect.top + 10:
            t.bounce(player)
    for fruit in [o for o in objects if o.name in ("melon", "pineapple", "strawberry")]:
        if pygame.sprite.collide_mask(player, fruit):

            if fruit.name == "melon":
                player.melon_active = True
                player.terrain_modifier = 2
                player.terrain_decay_timer = FPS * 7

            elif fruit.name == "pineapple":
                player.jump_boost = True
                player.jump_boost_timer = player.jump_boost_duration

            elif fruit.name == "strawberry":
                if player.lives < 5:
                    player.lives += 1
            
            objects.remove(fruit)
    
    keys = pygame.key.get_pressed()
    is_moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]

    if is_moving and player.y_vel == 0 and player.animation_count % 3 == 0:

        terrain_type = player.current_terrain_effect
        image_path = PARTICLE_MAPPING.get(terrain_type, PARTICLE_MAPPING['regular'])

        px = player.rect.centerx
        py = player.rect.bottom

        vel_x = -player.x_vel * 0.1

        for _ in range(2):
            scatter_x = vel_x + (random.random() * 2 - 1) * 0.5
            scatter_y = random.uniform(-2, -4)

            new_particle = Particle(px, py, image_path, velocity=(scatter_x, scatter_y), lifetime=random.randint(15, 25))
            particles.add(new_particle)

# Menu and Main
def main_menu(window):
    clock = pygame.time.Clock()
    menu_bg = get_menu_background()
    title = MENU_FONT.render('PLATFORMER', True, (255, 105, 180))
    title_x = WIDTH//2 - title.get_width()//2
    title_y = HEIGHT//5
    button_paths = [join('assets','Menu','Levels','01.png'), join('assets','Menu','Levels','02.png'), join('assets','Menu','Levels','03.png'), join('assets','Menu','Levels','04.png'), join('assets','Menu','Levels','05.png'), join('assets','Menu','Levels','06.png')]
    map_files = ['level_data_1.json','level_data_2.json', 'level_data_3.json', 'level_data_4.json','level_data_5.json','level_data_6.json']
    button_size = 96; spacing = 50
    total_w = 6*button_size + 5*spacing
    start_x = (WIDTH - total_w)//2
    button_y = HEIGHT//2 + 50
    buttons = []
    x = start_x
    for i in range(6):
        buttons.append(Button(x, button_y, button_paths[i], map_files[i]))
        x += button_size + spacing
    run = True
    selected = None
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b.check_click(event.pos):
                        selected = b.map_file
                        run = False
                        break
        window.blit(menu_bg, (0,0))
        window.blit(title, (title_x, title_y))
        for b in buttons: b.draw(window)
        pygame.display.update()
    return selected

def main(window, map_filename):
    clock = pygame.time.Clock()
    bg_name = BACKGROUND_MAPPING.get(map_filename, 'Blue.png')
    bg_img, bg_w, bg_h = get_background(bg_name)

    FULL_PATH = join("assets", "Maps", map_filename)
    if exists(FULL_PATH):
        with open(FULL_PATH, 'r') as f:
            RAW_MAP_DATA = json.load(f)
    else:
        RAW_MAP_DATA = []
    
    objects, start_pos = load_level(RAW_MAP_DATA, EDITOR_BLOCK_SIZE)
    trampolines = [o for o in objects if o.name == 'trampoline']
    
    DEFAULT_START = (100, HEIGHT - EDITOR_BLOCK_SIZE*2)
    player_start = start_pos if start_pos else DEFAULT_START
    player = Player(player_start[0], player_start[1], 50, 50)
    objects, start_pos = load_map(map_filename, EDITOR_BLOCK_SIZE)
    restart_btn = GameButton(WIDTH-58, 10, join('assets','Menu','Buttons','Restart.png'), (48,48))
    close_btn = GameButton(WIDTH-116,10, join('assets','Menu','Buttons','Close.png'), (48,48))
    start_time = pygame.time.get_ticks()
    final_time = None
    particles = pygame.sprite.Group()

    offset_x = 0; offset_y = 0 
    scroll_w = 200 
    in_game = [restart_btn, close_btn]
    INITIAL = player_start  
    run = True; game_over = False; level_complete = False
    
    offset_x = player_start[0] - (WIDTH // 2)
    offset_y = player_start[1] - (HEIGHT // 2)

    #MUSIC background
    MUSIC_FILE = join('assets', 'Audio', 'game.mp3')
    pygame.mixer.music.load(MUSIC_FILE)
    pygame.mixer.music.play(-1)

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and player.jump_count < 2 and not game_over and not level_complete:
                max_jumps = 2
                if player.current_terrain_effect == 'mud':
                    max_jumps = 1

                if player.jump_count < max_jumps:
                    player.jump()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mp = event.pos
                
                if restart_btn.check_click(mp):
                    objects, start_pos = load_level(RAW_MAP_DATA, EDITOR_BLOCK_SIZE)
                    trampolines = [o for o in objects if o.name == 'trampoline']

                    player.lives = LIVES_START
                    player.start_pos = INITIAL
                    player.rect.topleft = INITIAL
                    player.x_vel = player.y_vel = 0
                    game_over = False
                    level_complete = False
                    final_time = None 
                    start_time = pygame.time.get_ticks() 
                    
                    offset_x = INITIAL[0] - (WIDTH // 2)
                    offset_y = INITIAL[1] - (HEIGHT // 2)
                    
                if close_btn.check_click(mp):
                    pygame.mixer.music.stop()
                    return 'menu'
                    
        if level_complete and final_time is None:
            final_time = (pygame.time.get_ticks() - start_time) / 1000.0
            
        # --- Main Game Logic and Movement + death plane
        if not game_over and not level_complete:
            player.loop(FPS)
            handle_move(player, objects, particles)
            if handle_end_collision(player, objects):
                level_complete = True
            if player.rect.y > DEATH_PLANE_HEIGHT and player.lives_invincibility_timer <= 0:
                player.make_hit()
            if player.hit:
                if player.lives_invincibility_timer <= 0:
                    player.lives -= 1
                    player.lives_invincibility_timer = FPS * 3
                    if player.lives <= 0:
                        game_over = True
                    else:
                        player.rect.topleft = player.start_pos 
                        player.x_vel = player.y_vel = 0
                        offset_x = player.start_pos[0] - (WIDTH // 2)
                        offset_y = player.start_pos[1] - (HEIGHT // 2)
                
                player.hit = False
            
            if ((player.rect.right - offset_x >= WIDTH - scroll_w) and player.x_vel > 0) or ((player.rect.left - offset_x <= scroll_w) and player.x_vel < 0):
                offset_x += player.x_vel
            target_y = player.rect.y - (HEIGHT // 2)
            offset_y += (target_y - offset_y) * 0.1
            
        for o in [x for x in objects if hasattr(x, 'loop')]:
            o.loop()
        
        particles.update()

        draw(window, bg_img, bg_w, bg_h, player, objects, offset_x, offset_y, player.lives_invincibility_timer, game_over, level_complete)
        
        for p in particles:
            p.draw(window, offset_x, offset_y)
        
        if level_complete and final_time is not None:
            draw_completion_screen(window, final_time, restart_btn, close_btn)
        else:
            restart_btn.rect.topleft = (WIDTH-58, 10)
            close_btn.rect.topleft = (WIDTH-116, 10)
            for b in [restart_btn, close_btn]: 
                b.draw(window)

        pygame.display.update()
            
        # --- Game Over Reset ---
        if game_over:
            pygame.time.delay(2000)
            
            player.lives = LIVES_START
            player.rect.topleft = INITIAL
            player.start_pos = INITIAL
            player.x_vel = player.y_vel = 0
            game_over = False
            level_complete = False 
            final_time = None 
            start_time = pygame.time.get_ticks() 
            
            offset_x = INITIAL[0] - (WIDTH // 2)
            offset_y = INITIAL[1] - (HEIGHT // 2)
    
    pygame.mixer.music.stop()
    pygame.quit(); sys.exit()

# Run
if __name__ == '__main__':
    current_map = None
    while True:
        if current_map is None:
            current_map = main_menu(WINDOW)
        if current_map:
            action = main(WINDOW, current_map)
            if action == 'menu':
                current_map = None
            elif action == 'quit':
                break
            else:
                current_map = None
        else:
            break 
