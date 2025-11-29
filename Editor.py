import pygame
import json
import sys
from os import listdir
from os.path import isfile, join, exists

pygame.init()
pygame.font.init()
FONT = pygame.font.SysFont("comicsans", 15)

WIDTH, HEIGHT = 1000, 800
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platformer Editor (S: Save | I/O/P: Maps | 1–8 Tools | LC: Place | RC: Delete)")

FPS = 60
BASE_TILE_SIZE = 32
EDITOR_BLOCK_SIZE = 96
SMALL_GRID_SIZE = 48

EDITOR_TOOL = "block"
CURRENT_MAP_KEY = 1

def try_load(path):
    return pygame.image.load(path).convert_alpha()

trampoline_idle = try_load("assets/Traps/Trampoline/Idle.png")
trampoline_jump_sheet = try_load("assets/Traps/Trampoline/Jump.png")# chnage


MAP_FILES = {
    1: 'level_data_1.json', 
    2: 'level_data_2.json',
    3: 'level_data_3.json',
    4: 'level_data_4.json',
    5: 'level_data_5.json',
    6: 'level_data_6.json',
}

BACKGROUND_FILES = {
    1: "Blue.png",
    2: "Brown.png",
    3: "Purple.png",
    4: "Yellow.png",
    5: "Green.png",
    6: "Pink.png",
}

BLOCK_VARIANTS = { 
    1: {"block_x": 96, "tiny_x": 144, "y": 0},
    2: {"block_x": 96, "tiny_x": 144, "y": 64},
    3: {"block_x": 96, "tiny_x": 144, "y": 128},
    4: {"block_x": 96, "tiny_x": 144, "y": 0},
    5: {"block_x": 96, "tiny_x": 144, "y": 64},
    6: {"block_x": 96, "tiny_x": 144, "y": 128},
}

EDITOR_CATEGORY = None
CATEGORY_KEYS = {
    pygame.K_r: "terrain",
    pygame.K_t: "traps",
    pygame.K_y: "points",
}

TOOL_GROUPS = {
    "terrain": ["block", "tiny_block", "mud", "grass", "ice"],
    "traps": ["fire", "spike_head", "saw", "trampoline"],
    "points": ["start_point", "end_point", "checkpoint"],
}

def cut_spritesheet(sheet, fw, fh, count=None):
    frames = []
    total = count if count is not None else max(1, sheet.get_width() // fw)
    for i in range(total):
        rect = (i * fw, 0, fw, fh)
        if i * fw + fw > sheet.get_width():
            break
        frames.append(sheet.subsurface(rect).copy())
    return frames

def get_block_variant(size, sx, sy):
    imgpath = join("assets", "Terrain", "Terrain.png")
    img = try_load(imgpath)
    surf = pygame.Surface((BASE_TILE_SIZE, BASE_TILE_SIZE), pygame.SRCALPHA)
    surf.blit(img, (0, 0), pygame.Rect(sx, sy, BASE_TILE_SIZE, BASE_TILE_SIZE))
    return pygame.transform.scale(surf, (size, size))

def get_background(name):
    path = join("assets", "Background", name)
    img = try_load(path)
    return img, img.get_width(), img.get_height()

def get_grid_pos(mouse, ox, oy, size):
    wx, wy = mouse[0] + ox, mouse[1] + oy
    gx = (wx // size) * size
    gy = (wy // size) * size
    return gx, gy

def get_special_block_variant(size, sx, sy):
    path = join("assets", "Traps", "Climate", "Special.png")
    TILE_SIZE = 48
    img = try_load(path)
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    surf.blit(img, (0, 0), pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE))

    return pygame.transform.scale(surf, (size, size))

class SpecialBlock(pygame.sprite.Sprite):
    def __init__(self, x, y, name, vx, vy):
        size = EDITOR_BLOCK_SIZE
        super().__init__()
        self.rect = pygame.Rect(x, y, size, size)

        self.image = get_special_block_variant(size, vx, vy)

        self.name = name
        self.variant_x = vx
        self.variant_y = vy
        self.width = size
        self.height = size

class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, size, vx=96, vy=0):
        super().__init__()
        self.rect = pygame.Rect(x, y, size, size)
        self.image = get_block_variant(size, vx, vy)
        self.name = "block"
        self.variant_x = vx
        self.variant_y = vy
        self.width = size
        self.height = size

class TinyBlock(Block):
    def __init__(self, x, y, vx=144, vy=0):
        super().__init__(x, y, SMALL_GRID_SIZE, vx, vy)
        self.name = "tiny_block"

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, name):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.name = name
        self.width = w
        self.height = h

class AnimatedObject(Object):
    def __init__(self, x, y, w, h, name, sheet_path, frame_size, anim_delay=5):
        super().__init__(x, y, w, h, name)
        sheet = try_load(sheet_path)
        fw, fh = frame_size
        self.frames = []
        for i in range(sheet.get_width() // fw):
            fr = pygame.Surface((fw, fh), pygame.SRCALPHA)
            fr.blit(sheet, (0, 0), (i * fw, 0, fw, fh))
            self.frames.append(pygame.transform.scale(fr, (w, h)))
        self.animation_count = 0
        self.anim_delay = anim_delay
        if self.frames:
            self.image = self.frames[0]

    def loop(self):
        if not getattr(self, "frames", None):
            return
        idx = (self.animation_count // self.anim_delay) % len(self.frames)
        self.image = self.frames[idx]
        self.animation_count += 1

class SpikeHead(AnimatedObject):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "spike_head",
                         join("assets", "Traps", "Spike Head", "Blink.png"),
                         (54, 52), anim_delay=6)

class Fire(AnimatedObject):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "fire",
                         join("assets", "Traps", "Fire", "on.png"),
                         (16, 32), anim_delay=3)
class Saw(AnimatedObject):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "saw",
                         join("assets", "Traps", "Saw", "on.png"),
                         (38, 38), anim_delay=2)

class Trampoline(Object):
    TRAMPOLINE_WIDTH = EDITOR_BLOCK_SIZE
    TRAMPOLINE_HEIGHT = int(EDITOR_BLOCK_SIZE * 0.35)

    _idle_scaled = pygame.transform.scale(trampoline_idle, (TRAMPOLINE_WIDTH, TRAMPOLINE_HEIGHT))
    _jump_frames_scaled = [
        pygame.transform.scale(f, (TRAMPOLINE_WIDTH, TRAMPOLINE_HEIGHT)) # type: ignore
        for f in cut_spritesheet(trampoline_jump_sheet, 282, 28, count=8)
    ] or [ _idle_scaled ]

    def __init__(self, x, y):
        super().__init__(x, y, self.TRAMPOLINE_WIDTH, self.TRAMPOLINE_HEIGHT, "trampoline")
        self.idle = self._idle_scaled
        self.frames = self._jump_frames_scaled
        self.frame = 0
        self.image = self.idle
        self.animating = False
        self.timer = 0

    def loop(self):
        if self.animating:
            self.timer += 1
            if self.timer % 4 == 0:
                self.frame += 1
                if self.frame >= len(self.frames):
                    self.frame = 0
                    self.animating = False
                self.image = self.frames[self.frame]
        else:
            self.image = self.idle

    def bounce(self, player):
        player.y_vel = -20
        self.animating = True
        self.frame = 0
        self.timer = 0

class Checkpoint(AnimatedObject):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, "check_point",
                         join("assets", "Items", "Checkpoints", "Checkpoint", "Idle.png"),
                         (64, 64))

class StartPoint(AnimatedObject):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, "start_point",
                         join("assets", "Items", "Checkpoints", "Start", "start.png"),
                         (64, 64))

class EndPoint(AnimatedObject):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, "end_point",
                         join("assets", "Items", "Checkpoints", "End", "end.png"),
                         (64, 64))

def save_map(objects, key):
    fname = MAP_FILES[key]
    FULL_PATH = join("assets", "Maps", fname)
    data = []
    for o in objects:
        item = {"name": o.name, "x": o.rect.x, "y": o.rect.y, "width": o.width, "height": o.height}
        
        if o.name in ["block", "tiny_block"]:
            item["variant_x"] = getattr(o, "variant_x", 96)
            item["variant_y"] = getattr(o, "variant_y", 0)
        data.append(item)
    with open(FULL_PATH, "w") as f:
        json.dump(data, f, indent=4)
    print("Saved:", FULL_PATH)

def load_map(key):
    fname = MAP_FILES[key]
    FULL_PATH = join("assets", "Maps", fname)
    objs = []
    variants = BLOCK_VARIANTS[key]
    data = json.load(open(FULL_PATH))

    for it in data:
        n, x, y = it.get("name"), it.get("x", 0), it.get("y", 0)
        if n == "block":
            objs.append(Block(x, y, it.get("width", EDITOR_BLOCK_SIZE),
                             it.get("variant_x", variants["block_x"]),
                             it.get("variant_y", variants["y"])))
        elif n == "tiny_block":
            objs.append(TinyBlock(x, y, it.get("variant_x", variants["tiny_x"]),
                                  it.get("variant_y", variants["y"])))
        elif n in ("mud", "grass", "ice"):
            objs.append(SpecialBlock(x, y, n,
                                     it.get("variant_x", 0 if n=="mud" else(64 if n=="grass" else 128)),
                                     it.get("variant_y", 0)))
        elif n == "fire":
            objs.append(Fire(x, y, BASE_TILE_SIZE, BASE_TILE_SIZE * 2))
        elif n == "spike_head":
            objs.append(SpikeHead(x, y, BASE_TILE_SIZE * 2, BASE_TILE_SIZE * 2))
        elif n == "saw":
            objs.append(Saw(x, y, BASE_TILE_SIZE * 2, BASE_TILE_SIZE * 2))
        elif n == "start_point":
            objs.append(StartPoint(x, y, it.get("width", EDITOR_BLOCK_SIZE)))
        elif n == "end_point":
            objs.append(EndPoint(x, y, it.get("width", EDITOR_BLOCK_SIZE)))
        elif n in ("check_point", "checkpoint"):
            objs.append(Checkpoint(x, y, it.get("width", EDITOR_BLOCK_SIZE)))
        elif n == "trampoline":
            objs.append(Trampoline(x, y))
    return objs

def place_object(x, y, objects, tool_name):
    variants = BLOCK_VARIANTS[CURRENT_MAP_KEY]
    block_vx = variants["block_x"]
    tiny_vx = variants["tiny_x"]
    variant_y = variants["y"]

    if tool_name == "block":
        objects.append(Block(x, y, EDITOR_BLOCK_SIZE, block_vx, variant_y))
    elif tool_name == "tiny_block":
        objects.append(TinyBlock(x, y, tiny_vx, variant_y))
    elif tool_name == "mud":
        objects.append(SpecialBlock(x, y, "mud", 0, 0))
    elif tool_name == "grass":
        objects.append(SpecialBlock(x, y, "grass", 64, 0))
    elif tool_name == "ice":
        objects.append(SpecialBlock(x, y, "ice", 128, 0))    
    elif tool_name == "fire":
        objects.append(Fire(x, y, BASE_TILE_SIZE, BASE_TILE_SIZE * 2))
    elif tool_name == "spike_head":
        objects.append(SpikeHead(x, y, BASE_TILE_SIZE*2, BASE_TILE_SIZE*2))
    elif tool_name == "saw":
        objects.append(Saw(x, y, BASE_TILE_SIZE*2, BASE_TILE_SIZE*2))  
    elif tool_name == "start_point":
        objects[:] = [o for o in objects if o.name != "start_point"]
        objects.append(StartPoint(x, y, EDITOR_BLOCK_SIZE))
    elif tool_name == "end_point":
        objects.append(EndPoint(x, y, EDITOR_BLOCK_SIZE))
    elif tool_name in ("checkpoint", "check_point"):
        objects.append(Checkpoint(x, y, EDITOR_BLOCK_SIZE))
    elif tool_name == "trampoline":
        objects.append(Trampoline(x, y))

def delete_object(objects, mx, my, ox, oy):
    wx, wy = mx + ox, my + oy
    for i in range(len(objects)-1, -1, -1):
        if objects[i].rect.collidepoint((wx, wy)):
            objects.pop(i)
            return

def draw_grid(win, ox, oy):
    color = (120, 120, 120)
    for x in range(-ox % EDITOR_BLOCK_SIZE, WIDTH, EDITOR_BLOCK_SIZE):
        pygame.draw.line(win, color, (x, 0), (x, HEIGHT))
    for y in range(-oy % EDITOR_BLOCK_SIZE, HEIGHT, EDITOR_BLOCK_SIZE):
        pygame.draw.line(win, color, (0, y), (WIDTH, y))

def draw_editor(win, bg, bw, bh, objects, ox, oy):

    for x in range(-ox % bw - bw, WIDTH + bw, bw):
        for y in range(-oy % bh - bh, HEIGHT + bh, bh):
            win.blit(bg, (x, y))
    for obj in objects:
        win.blit(obj.image, (obj.rect.x - ox, obj.rect.y - oy))
    draw_grid(win, ox, oy)

    if EDITOR_CATEGORY:
        menu_surf = pygame.Surface((300, 250), pygame.SRCALPHA)
        menu_surf.fill((0,0,0, 192))
        win.blit(menu_surf, (10, 130))

        y_offset = 140
        header_text = FONT.render(f"--- SELECT {EDITOR_CATEGORY.upper()} ---", True, (255, 255, 0))
        win.blit(header_text, (20, y_offset))
        y_offset += 25

        for i, tool_name in enumerate(TOOL_GROUPS[EDITOR_CATEGORY]):
            color = (255, 255, 255)
            if tool_name == EDITOR_TOOL:
                color = (0, 255, 255)

            tool_text = FONT.render(f"[{i+1}] {tool_name.replace('_', ' ').title()}", True, color)

            win.blit(tool_text, (20, y_offset))
            y_offset += 20

    text_map = FONT.render(f"MAP FILE: {MAP_FILES[CURRENT_MAP_KEY]} (I/O/PF to change)", True, (255, 255, 0))
    win.blit(text_map, (10, 10))

    tool_text_1 = f"Category: [{EDITOR_CATEGORY.upper() if EDITOR_CATEGORY else 'NONE'}] (R/T/Y)"
    tool_text_2 = f"Current Tool: {EDITOR_TOOL.upper()}"

    text_tool_1 = FONT.render(tool_text_1, True, (255, 255, 255)) # Used white
    text_tool_2 = FONT.render(tool_text_2, True, (255, 255, 255)) # Used white
    win.blit(text_tool_1, (10, 40))
    win.blit(text_tool_2, (10, 70))

    text_info = FONT.render("S: Save | RC: Delete | W/Z/A/D: Scroll", True, (255, 255, 255))
    win.blit(text_info, (10, 100))

    pygame.display.update()

def handle_editor_input(event, objects, ox, oy):
    global EDITOR_TOOL, CURRENT_MAP_KEY, EDITOR_CATEGORY
    dx = dy = 0
    changed = False 

    if event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = pygame.mouse.get_pos()
        if event.button == 1:
            if EDITOR_TOOL == "tiny_block":
                size = SMALL_GRID_SIZE
            elif EDITOR_TOOL in ("fire"):
                size = BASE_TILE_SIZE 
            elif EDITOR_TOOL == "spike_head":
                size = BASE_TILE_SIZE * 2
            else:
                size = EDITOR_BLOCK_SIZE
            
            gx, gy = get_grid_pos((mx, my), ox, oy, size)
            
            if EDITOR_TOOL == "trampoline":
                gy += EDITOR_BLOCK_SIZE - Trampoline.TRAMPOLINE_HEIGHT
            if EDITOR_TOOL == "saw":
                gx += 16
                gy += 16
            place_object(gx, gy, objects, EDITOR_TOOL)

        elif event.button == 3:
            mx, my = pygame.mouse.get_pos()
            delete_object(objects, mx, my, ox, oy)

    if event.type == pygame.KEYDOWN:
        if event.key in CATEGORY_KEYS:
            target_category = CATEGORY_KEYS[event.key]

            if EDITOR_CATEGORY == target_category:
                EDITOR_CATEGORY = None
            else:
                EDITOR_CATEGORY = target_category
            return dx, dy, CURRENT_MAP_KEY if changed else None
            
        if EDITOR_CATEGORY and event.key >= pygame.K_1 and event.key <= pygame.K_9:
            key_index = event.key - pygame.K_1

            current_tools = TOOL_GROUPS[EDITOR_CATEGORY]
            if key_index < len(current_tools):
                EDITOR_TOOL = current_tools[key_index]
                EDITOR_CATEGORY = None
            return dx, dy, CURRENT_MAP_KEY if changed else None
        
        if event.key >= pygame.K_1 and event.key <= pygame.K_6:
            target_key = event.key - pygame.K_0 

            if target_key in MAP_FILES:
                if target_key != CURRENT_MAP_KEY:
                    CURRENT_MAP_KEY = target_key 
                    changed = True

        elif event.key == pygame.K_s:
            save_map(objects, CURRENT_MAP_KEY)
        elif event.key == pygame.K_w:
            dy = -EDITOR_BLOCK_SIZE
        elif event.key == pygame.K_z:
            dy = EDITOR_BLOCK_SIZE
        elif event.key == pygame.K_a:
            dx = -EDITOR_BLOCK_SIZE
        elif event.key == pygame.K_d:
            dx = EDITOR_BLOCK_SIZE
    
    return dx, dy, CURRENT_MAP_KEY if changed else None

def main_editor(window):
    clock = pygame.time.Clock()
    
    current_bg_file = BACKGROUND_FILES[CURRENT_MAP_KEY]
    bg, bw, bh = get_background(current_bg_file)
    objects = load_map(CURRENT_MAP_KEY)
    
    ox = oy = 0
    run = True
    while run:
        dt = clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            dx, dy, new_map_key = handle_editor_input(event, objects, ox, oy)
            
            if new_map_key is not None:
                objects [:] = load_map(new_map_key)
                new_bg_file = BACKGROUND_FILES[new_map_key]
                bg, bw, bh = get_background(new_bg_file)
                current_bg_file = new_bg_file
                ox = 0 
                oy = 0

            ox += dx if dx is not None else 0
            oy += dy if dy is not None else 0
            
        for obj in objects:
            if hasattr(obj, "loop"):
                obj.loop()
                
        draw_editor(window, bg, bw, bh, objects, ox, oy)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main_editor(WINDOW)
    except Exception as e:
        print("CRITICAL EDITOR ERROR")
        print(e)
        pygame.time.delay(3000)
        pygame.quit()
        sys.exit()
        # plans for game
        #Achievments
        #Better maps ughhhhhhhh
        # trampoling boing
        # Maybe setting (hard do later)
        # Get more blocks like space theme
        # stars in main screen counting them up
        # Makew maps more organized