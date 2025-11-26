import pygame
import os
import math
import sys
import json
import random
from os import listdir
from os.path import isfile, join, exists

pygame.init()
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

def try_font(path, size):
    try:
        return pygame.font.Font(path, size)
    except FileNotFoundError:
        return pygame.font.Font(None, size) # Fallback

FONT = try_font(join("assets", "Menu", "Text", "Platform.TTF"), 40)
MENU_FONT = try_font(join("assets", "Menu", "Text", "Platform.TTF"), 80)

BACKGROUND_MAPPING = {
    "level_data_1.json": "Blue.png",
    "level_data_2.json": "Brown.png",
    "level_data_3.json": "Purple.png",
}

PARTICLE_MAPPING = {
    'ice': join("assets", "Traps", "Climate", "Iceparticle.png"),
    'mud': join("assets", "Traps", "Climate", "Mudparticle.png"),
    'regular': join("assets", "Traps", "Climate", "Sandparticle.png"),
}

def try_load_image(path, fallback_size=(32, 32)):
    if exists(path):
        return pygame.image.load(path).convert_alpha()
    s = pygame.Surface(fallback_size, pygame.SRCALPHA)
    s.fill((255, 0, 255, 128))
    return s

# Trampoline assets
TRAMP_IDLE = try_load_image("assets/Traps/Trampoline/Idle.png")
TRAMP_JUMP_SHEET = try_load_image("assets/Traps/Trampoline/Jump.png")

# ----------------------
# Utilities
# ----------------------

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    files = [f for f in listdir(path) if isfile(join(path, f))]
    all_sprites = {}
    for image in files:
        sheet = try_load_image(join(path, image), (width, height))
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
        try:
            rect = (i * fw, 0, fw, fh)
            frames.append(sheet.subsurface(rect).copy())
        except ValueError:
            # Handle case where rect is outside the surface boundaries
            continue
    return frames


def get_background(name):
    path = join("assets", "Background", name)
    img = try_load_image(path, (WIDTH, HEIGHT)).convert()
    return img, img.get_width(), img.get_height()


def get_block_variant(size, sx, sy):
    path = join("assets", "Terrain", "Terrain.png")
    img = try_load_image(path, (BASE_TILE_SIZE, BASE_TILE_SIZE))
    surf = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE), pygame.SRCALPHA)
    surf.blit(img, (0, 0), pygame.Rect(sx, sy, BASE_TILE_SIZE, BASE_TILE_SIZE))
    return pygame.transform.scale(surf, (size, size))

def get_special_block_variant(size, sx, sy):
    path = join("assets", "Traps", "Climate", "Special.png")
    TILE_SIZE = 48
    img = try_load_image(path, (TILE_SIZE, TILE_SIZE))
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    surf.blit(img, (0, 0), pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE))

    return pygame.transform.scale(surf, (size, size))

# ----------------------
# Base object classes
# ----------------------

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
        sheet = try_load_image(sheet_path, (frame_size[0], frame_size[1]))
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

        img = try_load_image(image_path, (5, 5))
        self.image = pygame.transform.scale(img, (10, 10))

        self.rect = self.image.get_rect(center=(x, y))
        self.x_vel, self.y_vel = velocity
        self.lifetime = lifetime
        self.current_age = 0
        
        angle = pygame.time.get_ticks() % 360
        self.image = pygame.transform.rotate(self.image, angle)

    def loop(self):
        self.rect.x += self.x_vel
        self.rect.y += self.y_vel

        self.y_vel += 0.5

        self.current_age += 1
        alpha = 255 - int(255 * (self.current_age / self.liftime))
        self.image.set_alpha(max(0, alpha))
        
        if self.current_age > self.lifetime:
            self.kill()

class Trampoline(BaseObject):
    WIDTH = EDITOR_BLOCK_SIZE
    HEIGHT = int(EDITOR_BLOCK_SIZE * 0.35)
    BOUNCE_VELOCITY = -44 #Trampoline Height
    ANIM_DELAY = 4

    _idle = pygame.transform.scale(TRAMP_IDLE, (WIDTH, HEIGHT))
    _jump_frames = [pygame.transform.scale(f, (WIDTH, HEIGHT)) for f in cut_spritesheet(TRAMP_JUMP_SHEET, 282, 28, count=8)]

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

        self.current_terrain_effect = 'regular'
        self.terrain_decay_timer = 0

        self.heart_image = try_load_image(join('assets', 'Other', 'heart.png'))
        self.heart_image = pygame.transform.scale(self.heart_image, (48, 48))
        self.heart_size = self.heart_image.get_width()
        self.heart_padding = 10

    def jump(self):
        if self.current_terrain_effect == 'mud':
            jump_factor = 4
        else:
            jump_factor = 8
        
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
        self.move(self.x_vel, self.y_vel)
        if self.hit:
            pass
        self.fall_count += 1
        self.update_sprite()
        if self.lives_invincibility_timer > 0:
            self.lives_invincibility_timer -= 1

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

# Save / Load level

MAP_FILES = {
    pygame.K_i: 'level_data_1.json',
    pygame.K_o: 'level_data_2.json',
    pygame.K_p: 'level_data_3.json',
}


def save_map(objects, key):
    fname = MAP_FILES[key]
    data = []
    for o in objects:
        item = {'name': o.name, 'x': o.rect.x, 'y': o.rect.y, 'width': o.width, 'height': o.height}
        if getattr(o, 'variant_x', None) is not None:
            item['variant_x'] = o.variant_x
            item['variant_y'] = getattr(o, 'variant_y', 0)
        data.append(item)
    with open(fname, 'w') as f:
        json.dump(data, f, indent=4)


def load_map(filename='level_data_1.json', block_size=EDITOR_BLOCK_SIZE):
    if not exists(filename):
        return [], None
    with open(filename, 'r') as f:
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
                      objects.append(SpecialBlock(
                          x, y, name, block_size,
                          item.get('variant_x', 0),
                          item.get('varaint_y', 0),
                      ))
        elif name == 'fire':
            fire_w, fire_h = BASE_TILE_SIZE, BASE_TILE_SIZE * 2
            objects.append(Fire(x, y, BASE_TILE_SIZE, BASE_TILE_SIZE * 2))
        elif name == 'spike_head':
            objects.append(SpikeHead(x, y, BASE_TILE_SIZE * 2, BASE_TILE_SIZE * 2))
        elif name == 'saw':
            objects.append(Saw(x, y, BASE_TILE_SIZE * 2, BASE_TILE_SIZE * 2))
        elif name == 'trampoline':
            objects.append(Trampoline(x, y))
        elif name == 'start_point':
            start_pos = (x, y)
            objects.append(StartPoint(x, y, block_size))
        elif name == 'end_point':
            objects.append(EndPoint(x, y, block_size))
        elif name in ('check_point', 'checkpoint'):
            objects.append(CheckPoint(x, y, block_size))
    return objects, start_pos

# ----------------------
# UI helpers
# ----------------------

def get_menu_background(name='Menu.jpg'):
    path = join('assets', 'Background', name)
    img = try_load_image(path, (WIDTH, HEIGHT))
    return pygame.transform.scale(img, (WIDTH, HEIGHT))


class Button:
    def __init__(self, x, y, image_path, map_file=None):
        self.map_file = map_file
        img = try_load_image(image_path, (96, 96))
        self.image = pygame.transform.scale(img, (96, 96))
        self.rect = self.image.get_rect(topleft=(x, y))
    def draw(self, surf):
        surf.blit(self.image, self.rect.topleft)
    def check_click(self, pos):
        return self.rect.collidepoint(pos)

class GameButton(Button):
    def __init__(self, x, y, image_path, size, map_file=None):
        img = try_load_image(image_path, size)
        self.image = pygame.transform.scale(img, size)
        self.rect = self.image.get_rect(topleft=(x, y))
    def check_click(self, pos):
        return self.rect.collidepoint(pos)

# ----------------------
# Editor utilities
# ----------------------

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
    if level_complete:
        t = FONT.render('LEVEL COMPLETE! Nice!', True, (0, 255, 0))
        window.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2))

# ----------------------
# Collision & Movement
# ----------------------

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

    if player.terrain_decay_timer == 0 and not on_special_block:
        player.current_terrain_effect = 'regular'

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

    # damage traps
    for trap in [o for o in objects if o.name in ('fire', 'spike_head', 'saw')]:
        if pygame.sprite.collide_mask(player, trap) and player.lives_invincibility_timer <= 0:
            player.make_hit()
   
    # checkpoints
    for cp in [o for o in objects if o.name == 'check_point']:
        if pygame.sprite.collide_mask(player, cp):
            player.start_pos = (cp.rect.x, cp.rect.y)
   
    # trampolines
    for t in [o for o in objects if o.name == 'trampoline']:
        if player.rect.colliderect(t.rect) and player.y_vel >= 0 and player.rect.bottom <= t.rect.top + 10:
            t.bounce(player)

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
    button_paths = [join('assets','Menu','Levels','01.png'), join('assets','Menu','Levels','02.png'), join('assets','Menu','Levels','03.png')]
    map_files = ['level_data_1.json','level_data_2.json','level_data_3.json']
    button_size = 96; spacing = 50
    total_w = 3*button_size + 2*spacing
    start_x = (WIDTH - total_w)//2
    button_y = HEIGHT//2 + 50
    buttons = []
    x = start_x
    for i in range(3):
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
    objects, start_pos = load_map(map_filename, EDITOR_BLOCK_SIZE)
    trampolines = [o for o in objects if o.name == 'trampoline']
    DEFAULT_START = (100, HEIGHT - EDITOR_BLOCK_SIZE*2)
    player_start = start_pos if start_pos else DEFAULT_START
    player = Player(player_start[0], player_start[1], 50, 50)
    
    particles = pygame.sprite.Group()

    # Camera reset
    offset_x = 0; offset_y = 0
    
    scroll_w = 200
    restart_btn = GameButton(WIDTH-58, 10, join('assets','Menu','Buttons','Restart.png'), (48,48))
    close_btn = GameButton(WIDTH-116,10, join('assets','Menu','Buttons','Close.png'), (48,48))
    in_game = [restart_btn, close_btn]
    INITIAL = player_start
    
    run = True; game_over = False; level_complete = False
    
    # Initialize camera to player start position
    offset_x = player_start[0] - (WIDTH // 2)
    offset_y = player_start[1] - (HEIGHT // 2)

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
                    player.lives = LIVES_START
                    player.start_pos = INITIAL
                    player.rect.topleft = INITIAL
                    player.x_vel = player.y_vel = 0
                    # FIX: Reset camera on manual restart
                    offset_x = INITIAL[0] - (WIDTH // 2)
                    offset_y = INITIAL[1] - (HEIGHT // 2)
                if close_btn.check_click(mp):
                    return 'menu'
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
            # camera
            if ((player.rect.right - offset_x >= WIDTH - scroll_w) and player.x_vel > 0) or ((player.rect.left - offset_x <= scroll_w) and player.x_vel < 0):
                offset_x += player.x_vel
            target_y = player.rect.y - (HEIGHT // 2)
            offset_y += (target_y - offset_y) * 0.1
        # animate
        for o in [x for x in objects if hasattr(x, 'loop')]:
            o.loop()
        
        particles.update()

        draw(window, bg_img, bg_w, bg_h, player, objects, offset_x, offset_y, player.lives_invincibility_timer, game_over, level_complete)
        
        particles.draw(window)
        for p in particles:
            p.draw(window, offset_x, offset_y)
        
        for b in in_game: b.draw(window)
        pygame.display.update()
        if game_over or level_complete:
            pygame.time.delay(2000)
            if level_complete:
                return 'menu'
            # reset for new game
            player.lives = LIVES_START
            player.rect.topleft = INITIAL
            player.start_pos = INITIAL
            player.x_vel = player.y_vel = 0
            game_over = False
            level_complete = False
            
            # FIX: Reset offsets for the next game start
            offset_x = INITIAL[0] - (WIDTH // 2)
            offset_y = INITIAL[1] - (HEIGHT // 2)
            
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