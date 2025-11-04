import pygame
import os
import esper
import random
import math
from components import Position, Velocity, Physics, Health, Damage, Renderable, ArenaBoundary, Class, Player, EquippedItem, Rotation, Item, OrbitalItem, HitboxRect, SpawnProtection, DamageCooldown, UITransform, UIProgressBar, UIImage, UIButton, DesiredSpeed
from systems import MovementSystem, WallCollisionSystem, BallCollisionSystem, HealthSystem, RotationSystem, OrbitalSystem, SpawnProtectionSystem, RenderSystem, UISystem

# --- Game configuration ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60

# Arena configuration: 375x375 px centered on the screen
ARENA_SIZE = 375
ARENA_X = (SCREEN_WIDTH - ARENA_SIZE) // 2
ARENA_Y = (SCREEN_HEIGHT - ARENA_SIZE) // 2

# Music settings
MUSIC_VOLUME = 0.5
MUSIC_PATH = os.path.join('sounds', 'bards_of_wyverndale.mp3')

def ensure_music_playing():
    '''Initialize mixer and start playing background music if available.'''
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        if os.path.exists(MUSIC_PATH):
            try:
                pygame.mixer.music.load(MUSIC_PATH)
                pygame.mixer.music.set_volume(MUSIC_VOLUME)
                pygame.mixer.music.play(-1)
            except Exception:
                pass
    except Exception:
        # If audio initialization fails, skip silently
        pass

def stop_music():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

def main_menu(screen, clock, font):
    '''Display the initial main menu with header and 3 buttons.

    Returns: 'fight' to proceed to selection, 'quit' to exit, or None
    '''
    header_path = os.path.join('images', 'spt_Menu', 'Menu Header.png')
    header_img = None
    try:
        if os.path.exists(header_path):
            header_img = pygame.image.load(header_path).convert_alpha()
            # scale header to cover the whole window
            header_img = pygame.transform.scale(header_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception:
        header_img = None

    btn_w, btn_h = 260, 56
    center_x = SCREEN_WIDTH // 2
    start_y = SCREEN_HEIGHT // 2 - 20
    fight_rect = pygame.Rect(center_x - btn_w//2, start_y, btn_w, btn_h)
    settings_rect = pygame.Rect(center_x - btn_w//2, start_y + btn_h + 12, btn_w, btn_h)
    credits_rect = pygame.Rect(center_x - btn_w//2, start_y + 2*(btn_h + 12), btn_w, btn_h)

    selected_idx = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'quit'
                # keyboard navigation: W/S or Up/Down, select with E or Enter
                if event.key in (pygame.K_w, pygame.K_UP):
                    selected_idx = (selected_idx - 1) % 3
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    selected_idx = (selected_idx + 1) % 3
                if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER):
                    if selected_idx == 0:
                        return 'fight'
                    if selected_idx == 1:
                        res = settings_menu(screen, clock, font)
                    if selected_idx == 2:
                        credits_menu(screen, clock, font)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if fight_rect.collidepoint(mx, my):
                    return 'fight'
                if settings_rect.collidepoint(mx, my):
                    res = settings_menu(screen, clock, font)
                if credits_rect.collidepoint(mx, my):
                    credits_menu(screen, clock, font)

        # draw
        try:
            screen.fill((12, 12, 18))
            if header_img:
                # If header covers the whole screen, draw at 0,0
                if header_img.get_size() == (SCREEN_WIDTH, SCREEN_HEIGHT):
                    screen.blit(header_img, (0, 0))
                else:
                    hx = SCREEN_WIDTH//2 - header_img.get_width()//2
                    screen.blit(header_img, (hx, 60))
        except Exception:
            screen.fill((12,12,18))

        # buttons (mouse hover or keyboard selected)
        mx, my = pygame.mouse.get_pos()
        options = ((fight_rect, 'FIGHT'), (settings_rect, 'SETTINGS'), (credits_rect, 'CREDITS'))
        for idx, (rect, text) in enumerate(options):
            hovered = rect.collidepoint(mx, my)
            is_selected = (selected_idx == idx)
            color = (180,180,40) if (hovered or is_selected) else (200,200,200)
            try:
                pygame.draw.rect(screen, (30,30,30), rect)
                pygame.draw.rect(screen, color, rect, 2)
                txt = font.render(text, True, color)
                screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
            except Exception:
                pass

        pygame.display.flip()
        clock.tick(30)

def settings_menu(screen, clock, font):
    global MUSIC_VOLUME
    slider_w = 360
    slider_h = 8
    slider_x = SCREEN_WIDTH//2 - slider_w//2
    slider_y = SCREEN_HEIGHT//2

    back_rect = pygame.Rect(SCREEN_WIDTH//2 - 80, slider_y + 80, 160, 44)

    dragging = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'back'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if pygame.Rect(slider_x, slider_y - 10, slider_w, slider_h+20).collidepoint(mx, my):
                    dragging = True
                if back_rect.collidepoint(mx, my):
                    return 'back'
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False

        if dragging:
            mx, my = pygame.mouse.get_pos()
            t = (mx - slider_x) / float(slider_w)
            t = max(0.0, min(1.0, t))
            MUSIC_VOLUME = t
            try:
                pygame.mixer.music.set_volume(MUSIC_VOLUME)
            except Exception:
                pass

        # draw
        try:
            screen.fill((14,14,20))
            title = font.render('Settings - Music Volume', True, (220,220,220))
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, slider_y - 80))

            # draw slider background
            pygame.draw.rect(screen, (80,80,80), (slider_x, slider_y, slider_w, slider_h))
            filled = int(MUSIC_VOLUME * slider_w)
            pygame.draw.rect(screen, (200,60,60), (slider_x, slider_y, filled, slider_h))
            knob_x = slider_x + filled
            pygame.draw.circle(screen, (220,220,220), (knob_x, slider_y + slider_h//2), 10)

            vol_txt = font.render(f'Volume: {int(MUSIC_VOLUME*100)}%', True, (200,200,200))
            screen.blit(vol_txt, (SCREEN_WIDTH//2 - vol_txt.get_width()//2, slider_y + 28))

            # back button
            pygame.draw.rect(screen, (40,40,40), back_rect)
            pygame.draw.rect(screen, (200,200,200), back_rect, 2)
            bt = font.render('BACK', True, (200,200,200))
            screen.blit(bt, (back_rect.centerx - bt.get_width()//2, back_rect.centery - bt.get_height()//2))

            pygame.display.flip()
        except Exception:
            pass

        clock.tick(30)

def credits_menu(screen, clock, font):
    lines = ['Credits', 'Dilson Simões', 'Guilherme Burkert', '\nPress ESC or click to return']
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                return 'back'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return 'back'

        try:
            screen.fill((6,6,12))
            y = 120
            for i, line in enumerate(lines):
                txt = font.render(line, True, (220,220,220) if i==0 else (200,200,200))
                screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, y))
                y += 40
            pygame.display.flip()
        except Exception:
            pass
        clock.tick(30)

world = None


def reset_world():
    global world
    import time, random

    # Use a unique name per match to guarantee a fresh context
    name = f'match_{int(time.time()*1000)}_{random.randint(0,9999)}'
    esper.switch_world(name)
    world = name

# --- Items presets ---
ITEMS_PRESETS = {       
    'Knight Shield': {
        'name': 'Knight Shield', 'color': (0, 200, 200), 'image_path': 'images/spt_Weapons/knight_shield.png',
        'damage': 0, 'damage_reduction': 0.6,'orbit_radius': 60, 'angular_speed': 90,
        'hitbox_w': 80, 'hitbox_h': 60, 'knockback_strength': 40.0
    },
    'Knight Sword': {
        'name': 'Knight Sword', 'color': (0, 180, 80), 'image_path': 'images/spt_Weapons/knight_sword.png',
        'damage': 5, 'damage_reduction': 0.0, 'orbit_radius': 80, 'angular_speed': 90,
        'hitbox_w': 80, 'hitbox_h': 60, 'knockback_strength': 40.0
    },
    'Mage Orb': {
        'name': 'Mage Orb', 'color': (200, 0, 200), 'image_path': 'images/spt_Weapons/mage_orb.png',
        'damage': 8,'damage_reduction': 0.0, 'orbit_radius': 120, 'angular_speed': 300,
        'hitbox_w': 40, 'hitbox_h': 40, 'knockback_strength': 40.0
    },
    'Mage Staff': {
        'name': 'Mage Staff', 'color': (200, 0, 200), 'image_path': 'images/spt_Weapons/mage_staff.png',
        'damage': 1, 'damage_reduction': 0.0, 'orbit_radius': 60, 'angular_speed': 90,
        'hitbox_w': 60, 'hitbox_h': 80, 'knockback_strength': 70.0
    },
}

# --- Class presets ---
CLASS_PRESETS = {
    'Knight': {
        'radius': 40, 'color': (255, 0, 0), 'image_path': 'images/spt_Balls/knight.png',
        'mass': 4.0, 'restitution': 1.0, 'speed_range': (600, 650),
        'max_hp': 220, 'body_damage': 0, 'items': ['Knight Shield', 'Knight Sword']
    },
    'Mage': {
        'radius': 35, 'color': (0, 0, 255), 'image_path': 'images/spt_Balls/mage.png',
        'mass': 3.0, 'restitution': 1.0, 'speed_range': (500, 550),
        'max_hp': 180, 'body_damage': 0, 'items': ['Mage Orb', 'Mage Staff']
    },
    # 'Ninja': {
    #     'radius': 30, 'color': (0, 255, 0), 'image_path': 'images/ninja.png',
    #     'mass': 2.5, 'restitution': 1.0, 'speed_range': (700, 750),
    #     'max_hp': 200, 'body_damage': 5, 'items': []
    # },
    # 'Samurai': {
    #     'radius': 40, 'color': (255, 165, 0), 'image_path': 'images/samurai.png',
    #     'mass': 4.5, 'restitution': 1.0, 'speed_range': (600, 650),
    #     'max_hp': 200, 'body_damage': 5, 'items': []
    # },
    # 'Necromancer': {
    #     'radius': 40, 'color': (255, 0, 165), 'image_path': 'images/necromancer.png',
    #     'mass': 4.5, 'restitution': 1.0, 'speed_range': (600, 650),
    #     'max_hp': 200, 'body_damage': 5, 'items': []
    # },
}

def initialize_world():
    '''Register systems in the world in the desired processing order.'''
    esper.add_processor(MovementSystem())
    esper.add_processor(WallCollisionSystem())
    esper.add_processor(SpawnProtectionSystem())
    esper.add_processor(BallCollisionSystem())
    esper.add_processor(HealthSystem())
    esper.add_processor(RotationSystem())
    esper.add_processor(OrbitalSystem())

# --- Initialization Functions ---
def create_orbital_item(parent_ball, item_data, index, total_items):
    '''Create an orbital item for a ball.'''
    item = esper.create_entity()

    esper.add_component(item, Position(0, 0, 6))
    esper.add_component(item, Physics(0.1, 1.0))
    esper.add_component(item, Item(item_data['name'], item_data.get('damage', 0), item_data.get('damage_reduction', 0.0), item_data.get('speed_boost', 0.0), item_data.get('knockback_strength', 0.0)))

    hb_w = item_data.get('hitbox_w', 18)
    hb_h = item_data.get('hitbox_h', 10)

    esper.add_component(item, HitboxRect(hb_w, hb_h))
    esper.add_component(item, Rotation(index * (360 / total_items)))
    esper.add_component(item, OrbitalItem(parent_ball, item_data.get('orbit_radius', 40), item_data.get('angular_speed', 180), index * (360 / total_items)))
    esper.add_component(item, Renderable(item_data.get('color', (255, 255, 255)), item_data.get('image_path', None)))
    return item

def create_ball(x, y, radius, color, mass, restitution, max_hp, body_damage, class_name, items, player_id, vx=0.0, vy=0.0):
    '''Create a ball entity with all necessary components.'''
    ball = esper.create_entity()

    esper.add_component(ball, Position(x, y, radius))
    esper.add_component(ball, Velocity(vx, vy))
    speed_mag = math.hypot(vx, vy)
    esper.add_component(ball, DesiredSpeed(speed_mag))
    esper.add_component(ball, Physics(mass, restitution))
    esper.add_component(ball, Health(max_hp, max_hp))
    esper.add_component(ball, Damage(body_damage))
    esper.add_component(ball, Renderable(color, CLASS_PRESETS[class_name]['image_path']))
    esper.add_component(ball, Class(class_name))
    esper.add_component(ball, Player(player_id))
    esper.add_component(ball, SpawnProtection())
    esper.add_component(ball, DamageCooldown())

    resolved_items = []
    for it in items:
        if isinstance(it, str):
            preset = ITEMS_PRESETS.get(it)
            if preset:
                resolved_items.append(preset.copy())
            else:
                continue
        elif isinstance(it, dict):
            resolved_items.append(it)
        else:
            continue

    esper.add_component(ball, EquippedItem(resolved_items))
    esper.add_component(ball, Rotation())

    # Create orbital items for this ball
    for i, item_data in enumerate(resolved_items):
        create_orbital_item(ball, item_data, i, len(resolved_items))
    
    return ball

def select_classes_and_spawns(screen, clock, font, class_presets, bg_image=None):
    '''Create the initial menu for class selection for two players and spawn selection.'''
    menu_options = list(class_presets.keys())
    selected_idx_p1 = 0
    selected_idx_p2 = 0
    confirmed_p1 = False
    confirmed_p2 = False

    # 1. Class selection
    selecting = True
    # cache for menu preview sprites
    menu_image_cache = {}
    back_btn_rect = pygame.Rect(12, SCREEN_HEIGHT - 60, 96, 36)
    while selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None

            # Mouse clicks: only used here for the back button
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if back_btn_rect.collidepoint(mx, my):
                    return 'back'

            # Keyboard controls for navigation and confirmation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # go back to main menu
                    return 'back'

                # Player 1 Controls: W/S to move selection, E to confirm
                if not confirmed_p1:
                    if event.key == pygame.K_w:
                        selected_idx_p1 = (selected_idx_p1 - 1) % len(menu_options)
                    if event.key == pygame.K_s:
                        selected_idx_p1 = (selected_idx_p1 + 1) % len(menu_options)
                    if event.key == pygame.K_e:
                        confirmed_p1 = True

                # Player 2 Controls: Up/Down to move selection, Enter to confirm
                if not confirmed_p2:
                    if event.key == pygame.K_UP:
                        selected_idx_p2 = (selected_idx_p2 - 1) % len(menu_options)
                    if event.key == pygame.K_DOWN:
                        selected_idx_p2 = (selected_idx_p2 + 1) % len(menu_options)
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        confirmed_p2 = True

    # Draw the selection UI
        if bg_image:
            try:
                screen.blit(bg_image, (0, 0))
            except Exception:
                screen.fill((10, 10, 10))
        else:
            screen.fill((10, 10, 10))
        title = font.render('Select your class (Player 1: W/S + E)  (Player 2: Up/Down + Enter)', True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        col1_x = SCREEN_WIDTH // 4
        col2_x = 3 * SCREEN_WIDTH // 4

        p1_title = font.render('Player 1', True, (255, 200, 200))
        screen.blit(p1_title, (col1_x - p1_title.get_width() // 2, 100))
        for i, opt in enumerate(menu_options):
            color = (255, 255, 0) if i == selected_idx_p1 and not confirmed_p1 else (200, 200, 200)
            text = font.render(opt + ('  [CONF]' if confirmed_p1 and i == selected_idx_p1 else ''), True, color)
            screen.blit(text, (col1_x - text.get_width() // 2, 150 + i * 30))
        # draw preview sprite for the currently selected option (player 1)
        try:
            sel_name = menu_options[selected_idx_p1]
            sel_preset = class_presets.get(sel_name)
            if sel_preset and sel_preset.get('image_path'):
                ip = sel_preset.get('image_path')
                surf = menu_image_cache.get(ip)
                if surf is None:
                    try:
                        surf = pygame.image.load(ip).convert_alpha()
                    except Exception:
                        surf = None
                    menu_image_cache[ip] = surf
                if surf:
                    # scale preview to class radius * 2 or max 120 (apply global visual reduction)
                    r = sel_preset.get('radius', 32)
                    size = min(120, int(r * 2 * 0.7))
                    try:
                        img = pygame.transform.scale(surf, (size, size))
                        py = 150 + selected_idx_p1 * 30
                        px = col1_x + 100
                        screen.blit(img, (int(px - size/2), int(py - size/2)))
                    except Exception:
                        pass
        except Exception:
            pass

        p2_title = font.render('Player 2', True, (200, 200, 255))
        screen.blit(p2_title, (col2_x - p2_title.get_width() // 2, 100))
        for i, opt in enumerate(menu_options):
            color = (255, 255, 0) if i == selected_idx_p2 and not confirmed_p2 else (200, 200, 200)
            text = font.render(opt + ('  [CONF]' if confirmed_p2 and i == selected_idx_p2 else ''), True, color)
            screen.blit(text, (col2_x - text.get_width() // 2, 150 + i * 30))
        # draw preview sprite for the currently selected option (player 2)
        try:
            sel_name = menu_options[selected_idx_p2]
            sel_preset = class_presets.get(sel_name)
            if sel_preset and sel_preset.get('image_path'):
                ip = sel_preset.get('image_path')
                surf = menu_image_cache.get(ip)
                if surf is None:
                    try:
                        surf = pygame.image.load(ip).convert_alpha()
                    except Exception:
                        surf = None
                    menu_image_cache[ip] = surf
                if surf:
                    r = sel_preset.get('radius', 32)
                    size = min(120, int(r * 2 * 0.7))
                    try:
                        img = pygame.transform.scale(surf, (size, size))
                        py = 150 + selected_idx_p2 * 30
                        px = col2_x - 100
                        screen.blit(img, (int(px - size/2), int(py - size/2)))
                    except Exception:
                        pass
        except Exception:
            pass

        info = font.render('Both players confirm to proceed to spawn selection.', True, (180, 180, 180))
        screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, SCREEN_HEIGHT - 60))

        # Back button to return to main menu
        back_btn = pygame.Rect(12, SCREEN_HEIGHT - 60, 96, 36)
        try:
            pygame.draw.rect(screen, (30,30,30), back_btn)
            bt = font.render('VOLTAR', True, (200,200,200))
            screen.blit(bt, (back_btn.centerx - bt.get_width()//2, back_btn.centery - bt.get_height()//2))
        except Exception:
            pass

        pygame.display.flip()
        clock.tick(30)

        if confirmed_p1 and confirmed_p2:
            selecting = False

    # Resolve chosen presets
    chosen_p1 = menu_options[selected_idx_p1]
    chosen_p2 = menu_options[selected_idx_p2]
    preset_p1 = class_presets[chosen_p1]
    preset_p2 = class_presets[chosen_p2]

    # 2. Spawn selection
    spawn_confirmed_p1 = False
    spawn_confirmed_p2 = False

    # Start cursors inside the arena: left and right quarters of the arena
    cursor_p1 = [ARENA_X + ARENA_SIZE * 0.25, ARENA_Y + ARENA_SIZE * 0.5]
    cursor_p2 = [ARENA_X + ARENA_SIZE * 0.75, ARENA_Y + ARENA_SIZE * 0.5]
    move_speed = 6
    spawn_selecting = True

    while spawn_selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'back'
                if event.key == pygame.K_e and not spawn_confirmed_p1:
                    if spawn_confirmed_p2:
                        dx = cursor_p2[0] - cursor_p1[0]
                        dy = cursor_p2[1] - cursor_p1[1]
                        min_dist = preset_p1['radius'] + preset_p2['radius']
                        if dx*dx + dy*dy < (min_dist * min_dist):
                            pass
                        else:
                            spawn_confirmed_p1 = True
                    else:
                        spawn_confirmed_p1 = True
                if (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and not spawn_confirmed_p2:
                    if spawn_confirmed_p1:
                        dx = cursor_p2[0] - cursor_p1[0]
                        dy = cursor_p2[1] - cursor_p1[1]
                        min_dist = preset_p1['radius'] + preset_p2['radius']
                        if dx*dx + dy*dy < (min_dist * min_dist):
                            pass
                        else:
                            spawn_confirmed_p2 = True
                    else:
                        spawn_confirmed_p2 = True

        keys = pygame.key.get_pressed()
        if not spawn_confirmed_p1:
            if keys[pygame.K_a]:
                cursor_p1[0] -= move_speed
            if keys[pygame.K_d]:
                cursor_p1[0] += move_speed
            if keys[pygame.K_w]:
                cursor_p1[1] -= move_speed
            if keys[pygame.K_s]:
                cursor_p1[1] += move_speed
        if not spawn_confirmed_p2:
            if keys[pygame.K_LEFT]:
                cursor_p2[0] -= move_speed
            if keys[pygame.K_RIGHT]:
                cursor_p2[0] += move_speed
            if keys[pygame.K_UP]:
                cursor_p2[1] -= move_speed
            if keys[pygame.K_DOWN]:
                cursor_p2[1] += move_speed

        # Keep cursors inside the arena rectangle
        for c in (cursor_p1, cursor_p2):
            c[0] = max(ARENA_X + 1, min(ARENA_X + ARENA_SIZE - 1, c[0]))
            c[1] = max(ARENA_Y + 1, min(ARENA_Y + ARENA_SIZE - 1, c[1]))

        if bg_image:
            try:
                screen.blit(bg_image, (0, 0))
            except Exception:
                screen.fill((20, 20, 20))
        else:
            screen.fill((20, 20, 20))
        # Draw the arena rectangle so players can see spawning bounds
        try:
            pygame.draw.rect(screen, (40, 40, 40), pygame.Rect(int(ARENA_X), int(ARENA_Y), int(ARENA_SIZE), int(ARENA_SIZE)), 2)
        except Exception:
            pass
        info = font.render('Spawn select - P1: WASD + E to confirm | P2: Arrows + Enter', True, (220, 220, 220))
        screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 20))
        pygame.draw.circle(screen, preset_p1['color'], (int(cursor_p1[0]), int(cursor_p1[1])), preset_p1['radius'], 2)
        pygame.draw.circle(screen, preset_p2['color'], (int(cursor_p2[0]), int(cursor_p2[1])), preset_p2['radius'], 2)
        p1_status = 'CONFIRMED' if spawn_confirmed_p1 else 'Choosing'
        p2_status = 'CONFIRMED' if spawn_confirmed_p2 else 'Choosing'
        t1 = font.render(f'P1: {chosen_p1} - {p1_status}', True, (255, 255, 255))
        t2 = font.render(f'P2: {chosen_p2} - {p2_status}', True, (255, 255, 255))
        screen.blit(t1, (20, SCREEN_HEIGHT - 60))
        screen.blit(t2, (20, SCREEN_HEIGHT - 30))
        # Back button (interactive)
        back_btn = pygame.Rect(12, SCREEN_HEIGHT - 60, 96, 36)
        try:
            pygame.draw.rect(screen, (30,30,30), back_btn)
            bt = font.render('VOLTAR', True, (200,200,200))
            screen.blit(bt, (back_btn.centerx - bt.get_width()//2, back_btn.centery - bt.get_height()//2))
        except Exception:
            pass

        # handle mouse click for back button (poll immediate mouse state)
        try:
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if back_btn.collidepoint(mx, my):
                    return 'back'
        except Exception:
            pass

        pygame.display.flip()
        clock.tick(60)

        if spawn_confirmed_p1 and spawn_confirmed_p2:
            spawn_selecting = False

    # Initial random velocities sampled inside each class speed range
    def random_velocity_for_preset(preset):
        sr = preset.get('speed_range', (0, 0))
        speed = random.uniform(sr[0], sr[1])
        angle = random.uniform(0, 2 * math.pi)
        return speed * math.cos(angle), speed * math.sin(angle)

    vx1, vy1 = random_velocity_for_preset(preset_p1)
    vx2, vy2 = random_velocity_for_preset(preset_p2)

    return (chosen_p1, preset_p1, cursor_p1[0], cursor_p1[1], vx1, vy1,
        chosen_p2, preset_p2, cursor_p2[0], cursor_p2[1], vx2, vy2)

def run_game():
    '''Main function that initializes and runs the game loop.'''
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('ECS Pygame Ball Arena')
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    # Outer loop: allow returning to selection and restarting matches
    quit_game = False
    # Load a global background image once (used in menus and passed to RenderSystem)
    bg_scaled = None
    bg_path = os.path.join('images', 'spt_Menu', 'Background.png')
    try:
        if os.path.exists(bg_path):
            bg_img = pygame.image.load(bg_path).convert()
            sw, sh = screen.get_size()
            bg_scaled = pygame.transform.scale(bg_img, (sw, sh))
    except Exception:
        bg_scaled = None

    # Start music and show main menu before entering selection
    ensure_music_playing()

    while not quit_game:
        menu_choice = main_menu(screen, clock, font)
        if menu_choice is None or menu_choice == 'quit':
            break
        if menu_choice == 'fight':
            result = select_classes_and_spawns(screen, clock, font, CLASS_PRESETS, bg_image=bg_scaled)
            if result is None:
                break
        (chosen_p1, preset_p1, px1, py1, vx1, vy1,
         chosen_p2, preset_p2, px2, py2, vx2, vy2) = result

        # Reset and build a fresh world for this match
        reset_world()
        initialize_world()

        # Create arena bounds entity
        arena = esper.create_entity()
        esper.add_component(arena, ArenaBoundary(ARENA_X, ARENA_Y, ARENA_SIZE, ARENA_SIZE))

        id1 = create_ball(
            x=px1, y=py1,
            radius=preset_p1['radius'], color=preset_p1['color'],
            mass=preset_p1['mass'], restitution=preset_p1['restitution'],
            max_hp=preset_p1['max_hp'], body_damage=preset_p1['body_damage'],
            class_name=chosen_p1, items=preset_p1['items'],
            player_id=1, vx=vx1, vy=vy1
        )

        id2 = create_ball(
            x=px2, y=py2,
            radius=preset_p2['radius'], color=preset_p2['color'],
            mass=preset_p2['mass'], restitution=preset_p2['restitution'],
            max_hp=preset_p2['max_hp'], body_damage=preset_p2['body_damage'],
            class_name=chosen_p2, items=preset_p2['items'],
            player_id=2, vx=vx2, vy=vy2
        )

        # Add rendering + UI systems to this world
        render_sys = RenderSystem(screen, font, bg_image=bg_scaled)
        esper.add_processor(render_sys)
        ui_system = UISystem(screen, font)
        esper.add_processor(ui_system)

        # Create health bars for the two players: player 1 on top-right, player 2 on top-left
        BAR_W = 220
        BAR_H = 18
        PADDING = 12

        try:
            r1 = esper.component_for_entity(id1, Renderable)
            fg1 = getattr(r1, 'color', (0, 200, 0))
        except Exception:
            fg1 = (0, 200, 0)
        try:
            r2 = esper.component_for_entity(id2, Renderable)
            fg2 = getattr(r2, 'color', (200, 0, 0))
        except Exception:
            fg2 = (200, 0, 0)

        # Ensure Mage health bar is red regardless of sprite color
        try:
            if chosen_p1 == 'Mage':
                fg1 = (200, 0, 0)
        except Exception:
            pass
        try:
            if chosen_p2 == 'Mage':
                fg2 = (200, 0, 0)
        except Exception:
            pass

        # Player 1 (top-right)
        pb1 = esper.create_entity()
        esper.add_component(pb1, UITransform(SCREEN_WIDTH - PADDING - BAR_W, PADDING, 'topleft'))
        esper.add_component(pb1, UIProgressBar(BAR_W, BAR_H, bg_color=(60,60,60), fg_color=fg1, target_entity=id1, target_comp_name='Health', cur_field='current_hp', max_field='max_hp', z=100))

        # Player 1 character image to the left of the bar (larger icon)
        try:
            img1 = esper.create_entity()
            # scale image larger than bar height (30% larger)
            img_path1 = getattr(r1, 'image_path', None)
            ICON_H1 = int(BAR_H * 1.6)
            if img_path1:
                img_x = SCREEN_WIDTH - PADDING - BAR_W - (ICON_H1 + 12)
                esper.add_component(img1, UITransform(img_x, PADDING - (ICON_H1 - BAR_H)//2, 'topleft'))
                esper.add_component(img1, UIImage(img_path1, scale=(ICON_H1, ICON_H1), z=101))
        except Exception:
            pass

        # Player 2 (top-left)
        pb2 = esper.create_entity()
        esper.add_component(pb2, UITransform(PADDING, PADDING, 'topleft'))
        esper.add_component(pb2, UIProgressBar(BAR_W, BAR_H, bg_color=(60,60,60), fg_color=fg2, target_entity=id2, target_comp_name='Health', cur_field='current_hp', max_field='max_hp', z=100))

        # Player 2 character image to the right of the bar (larger icon)
        try:
            img2 = esper.create_entity()
            img_path2 = getattr(r2, 'image_path', None)
            ICON_H2 = int(BAR_H * 1.6)
            if img_path2:
                img2_x = PADDING + BAR_W + 12
                esper.add_component(img2, UITransform(img2_x, PADDING - (ICON_H2 - BAR_H)//2, 'topleft'))
                esper.add_component(img2, UIImage(img_path2, scale=(ICON_H2, ICON_H2), z=101))
        except Exception:
            pass

        # In-game settings button (bottom-right) with menu icon
        try:
            icon_path = os.path.join('images', 'spt_Menu', 'Sprite_Botao_menu.png')
            ICON_H = 56
            btn_ent = esper.create_entity()
            btn_x = SCREEN_WIDTH - PADDING - ICON_H
            btn_y = SCREEN_HEIGHT - PADDING - ICON_H
            esper.add_component(btn_ent, UITransform(btn_x, btn_y, 'topleft'))
            esper.add_component(btn_ent, UIImage(icon_path, scale=(ICON_H, ICON_H), z=200))
            # callback opens settings menu (blocks until closed)
            def _open_settings():
                settings_menu(screen, clock, font)
            esper.add_component(btn_ent, UIButton(_open_settings))
        except Exception:
            pass

        # Match loop
        match_running = True
        winner = None
        while match_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    match_running = False
                    quit_game = True
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    match_running = False
                    quit_game = True
                    break
                # forward events to UI
                try:
                    ui_system.push_event(event)
                except Exception:
                    pass

            dt = clock.tick(FPS) / 1000.0
            esper.process(dt)

            # Check victory condition: one of the player entities was destroyed
            alive1 = esper.entity_exists(id1)
            alive2 = esper.entity_exists(id2)
            if not alive1 or not alive2:
                if alive1 and not alive2:
                    winner = 1
                elif alive2 and not alive1:
                    winner = 2
                else:
                    winner = 0
                match_running = False

        if quit_game:
            break

        # Show victory overlay and wait for space (restart) or ESC/Quit
        if winner == 0:
            msg = 'Draw'
        elif winner == 1:
            # Show which player and their chosen class
            msg = f'Player 1 Wins! ({chosen_p1})'
        else:
            # Show which player and their chosen class
            msg = f'Player 2 Wins! ({chosen_p2})'
        info = 'Press SPACE to return to class selection or ESC to quit.'

        showing = True
        while showing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    showing = False
                    quit_game = True
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        showing = False
                        break
                    if event.key == pygame.K_ESCAPE:
                        showing = False
                        quit_game = True
                        break

            # Draw overlay
            # Let the render and ui systems draw a final frame first
            try:
                # draw a translucent overlay
                s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((0,0,0,160))
                screen.blit(s, (0,0))
            except Exception:
                pass

            try:
                title = font.render(msg, True, (255,255,255))
                subtitle = font.render(info, True, (220,220,220))
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//2 - 30))
                screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, SCREEN_HEIGHT//2 + 8))
                pygame.display.flip()
            except Exception:
                pass

            clock.tick(10)

    pygame.quit()

if __name__ == '__main__':
    run_game()