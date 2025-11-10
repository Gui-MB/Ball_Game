import pygame
import os
import esper
import random
import math
from components import Position, Velocity, Physics, Health, Damage, Renderable, ArenaBoundary, Class, Player, EquippedItem, Rotation, Item, OrbitalItem, HitboxRect, SpawnProtection, DamageCooldown, UITransform, UIProgressBar, UIImage, UIButton, DesiredSpeed, Mana, Skill, SkillSlots, SkillEffect
import systems
from systems import MovementSystem, WallCollisionSystem, BallCollisionSystem, HealthSystem, RotationSystem, OrbitalSystem, SpawnProtectionSystem, RenderSystem, UISystem, ManaSystem, SkillSystem

# --- Game configuration ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60

# Arena configuration: 375x375 px centered on the screen
ARENA_SIZE = 375
ARENA_X = (SCREEN_WIDTH - ARENA_SIZE) // 2
ARENA_Y = (SCREEN_HEIGHT - ARENA_SIZE) // 2

# Fullscreen toggle default
FULLSCREEN = False


def apply_display_mode(fullscreen: bool) -> pygame.Surface:
    """Apply and return a pygame display surface according to fullscreen flag.

    Keeps the configured SCREEN_WIDTH/HEIGHT. Returns the created surface.
    """
    flags = 0
    try:
        if fullscreen:
            flags = pygame.FULLSCREEN
    except Exception:
        flags = 0

    # Create or recreate the display surface
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        return screen
    except Exception:
        # Fallback: create a basic windowed mode
        return pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Music configuration
MUSIC_VOLUME = 0.5
MUSIC_PATH = os.path.join('sounds', 'bards_of_wyverndale.mp3')


def wrap_text(font, text, max_width):
    """Wrap a block of text into lines that fit within max_width using the provided font."""
    lines = []
    paragraphs = text.split('\n')
    for p_idx, para in enumerate(paragraphs):
        words = para.split()
        cur = ''
        for w in words:
            test = f"{cur} {w}".strip()
            if font.size(test)[0] <= max_width or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        # add a blank spacer between paragraphs except after last
        if p_idx < len(paragraphs) - 1:
            lines.append('')
    return lines


def draw_text_box(
    screen: pygame.Surface,
    font: pygame.font.Font,
    title: str,
    text: str,
    rect: pygame.Rect,
    fg=(220, 220, 220),
    border=(60, 60, 60),
    fill=(20, 20, 24),
    *,
    accent: tuple | None = None,
    icon_color: tuple | None = None,
    title_font: pygame.font.Font | None = None,
    body_font: pygame.font.Font | None = None,
    border_radius: int = 8,
    shadow: bool = True,
) -> None:
    """Draw a rounded, shadowed info panel with optional accent bar and icon.

    - accent: draws a thin top bar using this color
    - icon_color: draws a small colored circle next to the title
    - title/body fonts default to derived sizes from `font`
    - respects newlines in text via wrap_text
    """
    try:
        # Derive fonts if not provided
        base_h = max(1, font.get_height())
        if title_font is None:
            title_font = pygame.font.Font(None, max(18, int(base_h * 1.1)))
        if body_font is None:
            body_font = pygame.font.Font(None, base_h)

        # Shadow
        if shadow:
            shadow_rect = pygame.Rect(rect.x + 3, rect.y + 4, rect.width, rect.height)
            srf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            srf.fill((0, 0, 0, 110))
            try:
                pygame.draw.rect(srf, (0, 0, 0, 110), srf.get_rect(), border_radius=border_radius)
            except Exception:
                pass
            screen.blit(srf, (shadow_rect.x, shadow_rect.y))

        # Panel
        try:
            pygame.draw.rect(screen, fill, rect, border_radius=border_radius)
            pygame.draw.rect(screen, border, rect, 2, border_radius=border_radius)
        except Exception:
            pygame.draw.rect(screen, fill, rect)
            pygame.draw.rect(screen, border, rect, 2)

        # Accent bar on top
        if accent is not None:
            bar_h = 4
            bar_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, bar_h)
            pygame.draw.rect(screen, accent, bar_rect, border_radius=max(0, border_radius - 4))

        # Title
        x = rect.x + 10
        y = rect.y + 8
        if title:
            ts = title_font.render(title, True, fg)
            # optional colored icon
            icon_pad = 0
            if icon_color is not None:
                try:
                    pygame.draw.circle(screen, icon_color, (x + 8, y + ts.get_height() // 2), 5)
                    icon_pad = 16
                except Exception:
                    icon_pad = 0
            screen.blit(ts, (x + icon_pad, y))
            y += ts.get_height() + 6

        # Body
        body_lines = wrap_text(body_font, text, rect.width - 20)
        for line in body_lines:
            ls = body_font.render(line, True, (200, 200, 200))
            screen.blit(ls, (x, y))
            y += ls.get_height() + 2
    except Exception:
        pass


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
    'Katana': {
        'name': 'Katana', 'color': (200, 0, 200), 'image_path': 'images/spt_Weapons/samurai_katana.png',
        'damage': 3, 'damage_reduction': 0.0, 'orbit_radius': 80, 'angular_speed': 500,
        'hitbox_w': 100, 'hitbox_h': 60, 'knockback_strength': 40.0
    },
}


# --- Class presets ---
CLASS_PRESETS = {
    'Knight': {
        'radius': 40, 'color': (255, 0, 0), 'image_path': 'images/spt_Balls/knight.png',
        'mass': 4.0, 'restitution': 1.0, 'speed_range': (600, 650),
        'max_hp': 220, 'body_damage': 0, 'items': ['Knight Shield', 'Knight Sword'],
        'description': 'Knight: sturdy brawler with a shield to block incoming hits and a balanced sword.'
    },
    'Mage': {
        'radius': 35, 'color': (0, 0, 255), 'image_path': 'images/spt_Balls/mage.png',
        'mass': 3.0, 'restitution': 1.0, 'speed_range': (500, 550),
        'max_hp': 180, 'body_damage': 0, 'items': ['Mage Orb', 'Mage Staff'],
        'description': 'Mage: fragile but dangerous. Fast orbiting orb and staff help poke from range.'
    },
    'Samurai': {
        'radius': 40, 'color': (255, 165, 0), 'image_path': 'images/spt_Balls/samurai.png',
        'mass': 10.0, 'restitution': 1.001, 'speed_range': (600, 650),
        'max_hp': 150, 'body_damage': 0, 'items': ['Katana'],
        'description': 'Samurai: aggressive duelist with a swift katana and heavy mass.'
    },
    'Ninja': {
        'radius': 30, 'color': (0, 255, 0), 'image_path': 'images/spt_Balls/ninja.png',
        'mass': 2.5, 'restitution': 1.001, 'speed_range': (700, 750),
        'max_hp': 180, 'body_damage': 5, 'items': [],
        'description': 'Ninja: swift and agile fighter who relies on body damage with no weapons. Fast movement compensates for lack of range.'
    },

    # 'Necromancer': {
    #     'radius': 40, 'color': (255, 0, 165), 'image_path': 'images/necromancer.png',
    #     'mass': 4.5, 'restitution': 1.0, 'speed_range': (600, 650),
    #     'max_hp': 200, 'body_damage': 0, 'items': []
    # },
}


# --- Skill Presets ---
SKILLS_PRESETS = {
    'Shield': Skill(
        name='Shield',
        mana_cost=3.0,
        cooldown=1.0,
        effect_type='damage_reduction',
        effect_value=0.5,
        effect_duration=2.0,
        icon_color=(100, 200, 255),
        description='Raise a protective aura that reduces incoming damage by 50% for 2s.'
    ),
    'Berserk': Skill(
        name='Berserk',
        mana_cost=4.0,
        cooldown=1.0,
        effect_type='damage_boost',
        effect_value=1.5,
        effect_duration=2.0,
        icon_color=(255, 100, 100),
        description='Go berserk, increasing outgoing damage by 50% for 2s.'
    ),
    'Heal': Skill(
        name='Heal',
        mana_cost=5.0,
        cooldown=5.0,
        effect_type='heal',
        effect_value=10.0,
        effect_duration=0.0,
        icon_color=(100, 255, 100),
        description='Restore 10 HP instantly.'
    ),
    'Giant': Skill(
        name='Giant',
        mana_cost=4.0,
        cooldown=3.0,
        effect_type='radius_boost',
        effect_value=1.5,
        effect_duration=3.0,
        icon_color=(255, 200, 50),
        description='Temporarily grow larger, increasing your radius by 50% for 3s.'
    ),
    'Shrink': Skill(
        name='Shrink',
        mana_cost=3.0,
        cooldown=2.5,
        effect_type='radius_boost',
        effect_value=0.6,
        effect_duration=2.5,
        icon_color=(150, 100, 255),
        description='Shrink your size, reducing your radius by 40% for 2.5s. Harder to hit!'
    ),
}


def ensure_music_playing() -> None:
    """Initialize mixer and start playing background music if available."""
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
        pass


def stop_music() -> None:
    """Stop background music playback."""
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


def main_menu(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font) -> str:
    """Display the initial main menu with header and 3 buttons.
    
    Args:
        screen: The pygame display surface.
        clock: The pygame clock for frame rate control.
        font: The pygame font for rendering text.
        
    Returns:
        'fight' to proceed to selection, 'quit' to exit.
    """
    header_path = os.path.join('images', 'spt_Menu', 'menu_header.png')
    header_img = None
    try:
        if os.path.exists(header_path):
            header_img = pygame.image.load(header_path).convert_alpha()
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
                if event.key in (pygame.K_w, pygame.K_UP):
                    selected_idx = (selected_idx - 1) % 3
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    selected_idx = (selected_idx + 1) % 3
                if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER):
                    if selected_idx == 0:
                        return 'fight'
                    if selected_idx == 1:
                        res = settings_menu(screen, clock, font)
                        if res == 'quit':
                            return 'quit'
                        if isinstance(res, tuple) and res[0] == 'back':
                            screen = res[1]
                    if selected_idx == 2:
                        credits_menu(screen, clock, font)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if fight_rect.collidepoint(mx, my):
                    return 'fight'
                if settings_rect.collidepoint(mx, my):
                    res = settings_menu(screen, clock, font)
                    if res == 'quit':
                        return 'quit'
                    if isinstance(res, tuple) and res[0] == 'back':
                        screen = res[1]
                if credits_rect.collidepoint(mx, my):
                    credits_menu(screen, clock, font)

        # draw
        try:
            screen.fill((12, 12, 18))
            if header_img:
                if header_img.get_size() == (SCREEN_WIDTH, SCREEN_HEIGHT):
                    screen.blit(header_img, (0, 0))
                else:
                    hx = SCREEN_WIDTH//2 - header_img.get_width()//2
                    screen.blit(header_img, (hx, 60))
        except Exception:
            screen.fill((12, 12, 18))

        # Buttons
        mx, my = pygame.mouse.get_pos()
        options = ((fight_rect, 'FIGHT'), (settings_rect, 'SETTINGS'), (credits_rect, 'CREDITS'))
        for idx, (rect, text) in enumerate(options):
            hovered = rect.collidepoint(mx, my)
            is_selected = (selected_idx == idx)
            color = (180, 180, 40) if (hovered or is_selected) else (200, 200, 200)
            try:
                pygame.draw.rect(screen, (30, 30, 30), rect)
                pygame.draw.rect(screen, color, rect, 2)
                txt = font.render(text, True, color)
                screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
            except Exception:
                pass

        pygame.display.flip()
        clock.tick(30)


def settings_menu(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font):
    """Display the settings menu with a music volume slider.
    
    Args:
        screen: The pygame display surface.
        clock: The pygame clock for frame rate control.
        font: The pygame font for rendering text.
        
    Returns:
        'quit' to exit the game, 'back' to return to the main menu.
    """
    global MUSIC_VOLUME
    slider_w = 360
    slider_h = 8
    slider_x = SCREEN_WIDTH//2 - slider_w//2
    slider_y = SCREEN_HEIGHT//2

    # Fullscreen toggle button
    fs_rect = pygame.Rect(SCREEN_WIDTH//2 - 140, slider_y + 28, 280, 36)
    # Debug toggle button (shows hitboxes)
    debug_rect = pygame.Rect(SCREEN_WIDTH//2 - 140, slider_y + 72, 280, 36)
    # Back button moved down to make room for debug toggle
    back_rect = pygame.Rect(SCREEN_WIDTH//2 - 80, slider_y + 116, 160, 44)

    dragging = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return ('back', pygame.display.get_surface())
                if event.key == pygame.K_f:
                    # Keyboard toggle fullscreen
                    globals()['FULLSCREEN'] = not globals()['FULLSCREEN']
                    screen = apply_display_mode(globals()['FULLSCREEN'])
                if event.key == pygame.K_d:
                    # Toggle debug hitbox display
                    try:
                        systems.SHOW_HITBOXES = not systems.SHOW_HITBOXES
                        systems.DEBUG_ENABLED = systems.SHOW_HITBOXES
                    except Exception:
                        pass
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if pygame.Rect(slider_x, slider_y - 10, slider_w, slider_h+20).collidepoint(mx, my):
                    dragging = True
                if back_rect.collidepoint(mx, my):
                    return ('back', pygame.display.get_surface())
                if fs_rect.collidepoint(mx, my):
                    globals()['FULLSCREEN'] = not globals()['FULLSCREEN']
                    screen = apply_display_mode(globals()['FULLSCREEN'])
                if debug_rect.collidepoint(mx, my):
                    try:
                        systems.SHOW_HITBOXES = not systems.SHOW_HITBOXES
                        systems.DEBUG_ENABLED = systems.SHOW_HITBOXES
                        print(f"[DEBUG] Toggled SHOW_HITBOXES -> {systems.SHOW_HITBOXES}")
                    except Exception:
                        pass
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

        try:
            screen.fill((14, 14, 20))
            title = font.render('Settings', True, (220, 220, 220))
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, slider_y - 100))
            subtitle = font.render('Music Volume', True, (200, 200, 200))
            screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, slider_y - 72))

            pygame.draw.rect(screen, (80, 80, 80), (slider_x, slider_y, slider_w, slider_h))
            filled = int(MUSIC_VOLUME * slider_w)
            pygame.draw.rect(screen, (200, 60, 60), (slider_x, slider_y, filled, slider_h))
            knob_x = slider_x + filled
            pygame.draw.circle(screen, (220, 220, 220), (knob_x, slider_y + slider_h//2), 10)

            vol_txt = font.render(f'Volume: {int(MUSIC_VOLUME*100)}%', True, (200, 200, 200))
            screen.blit(vol_txt, (SCREEN_WIDTH//2 - vol_txt.get_width()//2, slider_y + 28))

            # Fullscreen toggle UI
            fs_on = FULLSCREEN
            fs_color = (60, 120, 200) if fs_on else (80, 80, 80)
            try:
                pygame.draw.rect(screen, (30, 30, 30), fs_rect)
                pygame.draw.rect(screen, fs_color, fs_rect, 2)
                fs_txt = font.render(f'Fullscreen: {"ON" if fs_on else "OFF"}  (F)', True, (200, 200, 200))
                screen.blit(fs_txt, (fs_rect.centerx - fs_txt.get_width()//2, fs_rect.centery - fs_txt.get_height()//2))
            except Exception:
                pass

            # Debug toggle UI (hitboxes)
            try:
                dbg_on = getattr(systems, 'SHOW_HITBOXES', False)
                dbg_color = (120, 200, 120) if dbg_on else (80, 80, 80)
                pygame.draw.rect(screen, (30, 30, 30), debug_rect)
                pygame.draw.rect(screen, dbg_color, debug_rect, 2)
                dbg_txt = font.render(f'Debug Hitboxes: {"ON" if dbg_on else "OFF"}  (D)', True, (200, 200, 200))
                screen.blit(dbg_txt, (debug_rect.centerx - dbg_txt.get_width()//2, debug_rect.centery - dbg_txt.get_height()//2))
            except Exception:
                pass

            pygame.draw.rect(screen, (40, 40, 40), back_rect)
            pygame.draw.rect(screen, (200, 200, 200), back_rect, 2)
            bt = font.render('BACK', True, (200, 200, 200))
            screen.blit(bt, (back_rect.centerx - bt.get_width()//2, back_rect.centery - bt.get_height()//2))

            pygame.display.flip()
        except Exception:
            pass

        clock.tick(30)


def credits_menu(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font) -> None:
    """Display the credits menu.
    
    Args:
        screen: The pygame display surface.
        clock: The pygame clock for frame rate control.
        font: The pygame font for rendering text.
    """
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


def reset_world() -> None:
    """Reset the ECS world for a new match.
    
    Creates a unique world name and switches to it to guarantee a fresh context.
    """
    global world
    import time
    
    # Use a unique name per match to guarantee a fresh context
    name = f'match_{int(time.time()*1000)}_{random.randint(0, 9999)}'
    esper.switch_world(name)
    world = name


def initialize_world() -> None:
    """Register systems in the world in the desired processing order."""
    esper.add_processor(MovementSystem())
    esper.add_processor(WallCollisionSystem())
    esper.add_processor(SpawnProtectionSystem())
    esper.add_processor(ManaSystem())
    esper.add_processor(SkillSystem())
    esper.add_processor(BallCollisionSystem())
    esper.add_processor(HealthSystem())
    esper.add_processor(RotationSystem())
    esper.add_processor(OrbitalSystem())


# --- Initialization Functions ---

def create_orbital_item(parent_ball, item_data: dict, index: int, total_items: int):
    """Create an orbital item for a ball.
    
    Args:
        parent_ball: The ball entity to which this item orbits.
        item_data: Dictionary containing item configuration.
        index: The index of this item among all orbiting items.
        total_items: Total number of items orbiting the parent ball.
        
    Returns:
        The entity ID of the created orbital item.
    """
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


def create_ball(
    x: float,
    y: float,
    radius: int,
    color: tuple,
    mass: float,
    restitution: float,
    max_hp: int,
    body_damage: int,
    class_name: str,
    items: list,
    player_id: int,
    skills: list = None,
    vx: float = 0.0,
    vy: float = 0.0
):
    """Create a ball entity with all necessary components.
    
    Args:
        x, y: Initial position coordinates.
        radius: Visual radius of the ball.
        color: RGB color tuple of the ball.
        mass: Physical mass for collision calculations.
        restitution: Elasticity/bounce factor (0.0 to 1.0+).
        max_hp: Maximum health points.
        body_damage: Damage dealt on body collision.
        class_name: Class type of the ball (e.g., 'Knight', 'Mage').
        items: List of equipped item names or dictionaries.
        player_id: Player ID (1 or 2) controlling this ball.
        skills: List of 4 Skill objects for this player.
        vx: Initial x-velocity (default 0.0).
        vy: Initial y-velocity (default 0.0).
        
    Returns:
        The entity ID of the created ball.
    """
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

    # Add mana component (max 10 mana, 0.5 regen per second)
    esper.add_component(ball, Mana(max_mana=10.0, regen_rate=0.5))
    
    # Add skills as a container
    if skills:
        esper.add_component(ball, SkillSlots(skills))

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


def select_skills(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    font: pygame.font.Font,
    bg_image: pygame.Surface = None
):
    """Allow each player to select 4 skills from available skill pool.
    
    Args:
        screen: The pygame display surface.
        clock: The pygame clock for frame rate control.
        font: The pygame font for rendering text.
        bg_image: Optional background image surface.
        
    Returns:
        Tuple of (skills_p1, skills_p2) where each is a list of 4 Skill objects,
        or 'back' if user returns to main menu.
    """
    skill_names = list(SKILLS_PRESETS.keys())
    
    # Track selected skills for each player (list of skill names or None)
    selected_p1 = [None, None, None, None]
    selected_p2 = [None, None, None, None]
    
    # Current cursor position for each player (which slot they're customizing)
    cursor_p1 = 0
    cursor_p2 = 0
    
    # Current highlighted skill in the pool for each player
    highlight_p1 = 0
    highlight_p2 = 0
    
    done_p1 = False
    done_p2 = False
    
    back_btn_rect = pygame.Rect(12, SCREEN_HEIGHT - 60, 96, 36)
    
    selecting = True
    while selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'back'
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if back_btn_rect.collidepoint(mx, my):
                    return 'back'
                # PRONTO clickable buttons for each player -- positioned under slot 4
                col1_x = SCREEN_WIDTH // 4
                col2_x = 3 * SCREEN_WIDTH // 4
                PRONTO_W, PRONTO_H = 120, 36
                # slots start at y_start + 40 and each slot is 30px high; place PRONTO below slot 4
                y_start = 80
                slots_top = y_start + 40
                pronto_y = slots_top + 4 * 30 + 12
                pronto_p1_rect = pygame.Rect(col1_x - PRONTO_W // 2, pronto_y, PRONTO_W, PRONTO_H)
                pronto_p2_rect = pygame.Rect(col2_x - PRONTO_W // 2, pronto_y, PRONTO_W, PRONTO_H)

                # P1: require all slots filled to mark done
                if pronto_p1_rect.collidepoint(mx, my) and not done_p1:
                    # focus PRONTO when clicked
                    cursor_p1 = 4
                    print('[DEBUG] PRONTO clicked P1 at', mx, my)
                    # Mark ready even if not all slots are filled (user requested no requirement)
                    done_p1 = True

                if pronto_p2_rect.collidepoint(mx, my) and not done_p2:
                    # focus PRONTO when clicked
                    cursor_p2 = 4
                    print('[DEBUG] PRONTO clicked P2 at', mx, my)
                    # Mark ready even if not all slots are filled
                    done_p2 = True
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'back'
                
                # Player 1 controls (if not done)
                # cursor_p1 allowed values: 0..3 -> slots, 4 -> PRONTO button
                if not done_p1:
                    if event.key == pygame.K_w:
                        # move up through slots and onto PRONTO (wrap)
                        cursor_p1 = (cursor_p1 - 1) % 5
                    elif event.key == pygame.K_s:
                        cursor_p1 = (cursor_p1 + 1) % 5
                    elif event.key == pygame.K_a:
                        # change highlighted skill only when focused on a slot
                        if cursor_p1 < 4:
                            highlight_p1 = (highlight_p1 - 1) % len(skill_names)
                    elif event.key == pygame.K_d:
                        if cursor_p1 < 4:
                            highlight_p1 = (highlight_p1 + 1) % len(skill_names)
                    elif event.key == pygame.K_e:
                        # assign only if on a slot
                        if cursor_p1 < 4:
                            selected_p1[cursor_p1] = skill_names[highlight_p1]
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # If PRONTO is focused, activate it (require all slots filled)
                        # Also accept Enter if the mouse is currently over the PRONTO button.
                        # Recompute PRONTO rect same as the drawing code.
                        col1_x = SCREEN_WIDTH // 4
                        PRONTO_W, PRONTO_H = 120, 36
                        y_start_local = 80
                        slots_top_local = y_start_local + 40
                        pronto_y_local = slots_top_local + 4 * 30 + 12
                        pronto_p1_rect_local = pygame.Rect(col1_x - PRONTO_W // 2, pronto_y_local, PRONTO_W, PRONTO_H)
                        mx, my = pygame.mouse.get_pos()
                        if cursor_p1 == 4 or pronto_p1_rect_local.collidepoint(mx, my):
                            if all(s is not None for s in selected_p1):
                                done_p1 = True
                            else:
                                # focus PRONTO so user can press Enter again after filling slots
                                cursor_p1 = 4
                
                # Player 2 controls (if not done)
                # cursor_p2 allowed values: 0..3 -> slots, 4 -> PRONTO button
                if not done_p2:
                    if event.key == pygame.K_UP:
                        cursor_p2 = (cursor_p2 - 1) % 5
                    elif event.key == pygame.K_DOWN:
                        cursor_p2 = (cursor_p2 + 1) % 5
                    elif event.key == pygame.K_LEFT:
                        if cursor_p2 < 4:
                            highlight_p2 = (highlight_p2 - 1) % len(skill_names)
                    elif event.key == pygame.K_RIGHT:
                        if cursor_p2 < 4:
                            highlight_p2 = (highlight_p2 + 1) % len(skill_names)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # If focused on a slot, assign; if focused on PRONTO, activate
                        if cursor_p2 < 4:
                            selected_p2[cursor_p2] = skill_names[highlight_p2]
                        else:
                            if all(s is not None for s in selected_p2):
                                done_p2 = True
        
        # Draw
        if bg_image:
            try:
                screen.blit(bg_image, (0, 0))
            except Exception:
                screen.fill((10, 10, 10))
        else:
            screen.fill((10, 10, 10))
        
        title = font.render('Select 4 Skills (P1: WASD/E | P2: Arrows/Enter) - Click PRONTO to finish', True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Left side: Player 1
        col1_x = SCREEN_WIDTH // 4
        y_start = 80
        p1_title = font.render('Player 1 Skills', True, (255, 200, 200))
        screen.blit(p1_title, (col1_x - p1_title.get_width() // 2, y_start))
        
        y = y_start + 40
        for i in range(4):
            slot_text = f'Slot {i+1}: '
            if selected_p1[i]:
                slot_text += selected_p1[i]
                color = (100, 255, 100) if i == cursor_p1 else (200, 200, 200)
            else:
                slot_text += '(empty)'
                color = (255, 100, 100) if i == cursor_p1 else (150, 150, 150)
            
            if i == cursor_p1 and not done_p1:
                color = (255, 255, 0)
            
            text = font.render(slot_text, True, color)
            screen.blit(text, (col1_x - text.get_width() // 2, y))
            y += 30
        
        # Available skills for P1
        # Draw available skills as a horizontal list under the slots
        avail_y = y + 70
        try:
            avail_title = font.render('Available:', True, (200, 200, 200))
            screen.blit(avail_title, (col1_x - avail_title.get_width() // 2, avail_y))
        except Exception:
            pass
        # prepare surfaces to compute total width
        gap = 24
        skill_surfaces = []
        total_w = 0
        for idx, skill_name in enumerate(skill_names):
            color = (255, 255, 0) if idx == highlight_p1 and not done_p1 else (180, 180, 180)
            surf = font.render(skill_name, True, color)
            skill_surfaces.append((surf, color))
            total_w += surf.get_width()
        if skill_surfaces:
            total_w += gap * (len(skill_surfaces) - 1)
        sx = col1_x - total_w // 2
        sy = avail_y + 28
        for surf, color in skill_surfaces:
            screen.blit(surf, (sx, sy))
            sx += surf.get_width() + gap

        # Description box for P1 highlighted skill
        try:
            sname = skill_names[highlight_p1]
            sref = SKILLS_PRESETS.get(sname)
            if sref:
                # Build a concise meta description line
                effect = sref.effect_type
                if effect == 'damage_reduction':
                    extra = f"Reduces damage by {int(sref.effect_value*100)}% for {int(sref.effect_duration)}s"
                elif effect == 'damage_boost':
                    extra = f"Increases damage by {int((sref.effect_value-1)*100)}% for {int(sref.effect_duration)}s"
                elif effect == 'heal':
                    extra = f"Heals {int(sref.effect_value)} HP instantly"
                else:
                    extra = effect
                desc_text = f"Mana: {sref.mana_cost} | Cooldown: {int(sref.cooldown)}s\n{extra}.\n{getattr(sref, 'description', '')}"
                box_w, box_h = 360, 140
                box_rect = pygame.Rect(max(8, col1_x - box_w//2), SCREEN_HEIGHT - box_h - 12, box_w, box_h)
                draw_text_box(screen, font, sref.name, desc_text, box_rect, accent=sref.icon_color, icon_color=sref.icon_color)
        except Exception:
            pass
        
        # Right side: Player 2
        col2_x = 3 * SCREEN_WIDTH // 4
        y_start = 80
        p2_title = font.render('Player 2 Skills', True, (200, 200, 255))
        screen.blit(p2_title, (col2_x - p2_title.get_width() // 2, y_start))
        
        y = y_start + 40
        for i in range(4):
            slot_text = f'Slot {i+1}: '
            if selected_p2[i]:
                slot_text += selected_p2[i]
                color = (100, 255, 100) if i == cursor_p2 else (200, 200, 200)
            else:
                slot_text += '(empty)'
                color = (255, 100, 100) if i == cursor_p2 else (150, 150, 150)
            
            if i == cursor_p2 and not done_p2:
                color = (255, 255, 0)
            
            text = font.render(slot_text, True, color)
            screen.blit(text, (col2_x - text.get_width() // 2, y))
            y += 30
        
        # Available skills for P2
        # Draw available skills as a horizontal list under the slots for P2
        avail_y = y + 70
        try:
            avail_title = font.render('Available:', True, (200, 200, 200))
            screen.blit(avail_title, (col2_x - avail_title.get_width() // 2, avail_y))
        except Exception:
            pass
        gap = 24
        skill_surfaces2 = []
        total_w2 = 0
        for idx, skill_name in enumerate(skill_names):
            color = (255, 255, 0) if idx == highlight_p2 and not done_p2 else (180, 180, 180)
            surf = font.render(skill_name, True, color)
            skill_surfaces2.append((surf, color))
            total_w2 += surf.get_width()
        if skill_surfaces2:
            total_w2 += gap * (len(skill_surfaces2) - 1)
        sx2 = col2_x - total_w2 // 2
        sy2 = avail_y + 28
        for surf, color in skill_surfaces2:
            screen.blit(surf, (sx2, sy2))
            sx2 += surf.get_width() + gap

        # Description box for P2 highlighted skill
        try:
            sname2 = skill_names[highlight_p2]
            sref2 = SKILLS_PRESETS.get(sname2)
            if sref2:
                if sref2.effect_type == 'damage_reduction':
                    extra2 = f"Reduces damage by {int(sref2.effect_value*100)}% for {int(sref2.effect_duration)}s"
                elif sref2.effect_type == 'damage_boost':
                    extra2 = f"Increases damage by {int((sref2.effect_value-1)*100)}% for {int(sref2.effect_duration)}s"
                elif sref2.effect_type == 'heal':
                    extra2 = f"Heals {int(sref2.effect_value)} HP instantly"
                else:
                    extra2 = sref2.effect_type
                desc_text2 = f"Mana: {sref2.mana_cost} | Cooldown: {int(sref2.cooldown)}s\n{extra2}.\n{getattr(sref2, 'description', '')}"
                box_w2, box_h2 = 360, 140
                box_rect2 = pygame.Rect(min(SCREEN_WIDTH - box_w2 - 8, col2_x - box_w2//2), SCREEN_HEIGHT - box_h2 - 12, box_w2, box_h2)
                draw_text_box(screen, font, sref2.name, desc_text2, box_rect2, accent=sref2.icon_color, icon_color=sref2.icon_color)
        except Exception:
            pass
        
        # Status
        p1_status = 'READY' if done_p1 else 'Selecting'
        p2_status = 'READY' if done_p2 else 'Selecting'
        status_text = f'P1: {p1_status}  |  P2: {p2_status}'
        if done_p1 and done_p2:
            status_color = (100, 255, 100)
        else:
            status_color = (180, 180, 180)
        
        txt = font.render(status_text, True, status_color)
        screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, SCREEN_HEIGHT // 2))
        
        # Back button
        try:
            pygame.draw.rect(screen, (30, 30, 30), back_btn_rect)
            bt = font.render('RETURN', True, (200, 200, 200))
            screen.blit(bt, (back_btn_rect.centerx - bt.get_width()//2, back_btn_rect.centery - bt.get_height()//2))
        except Exception:
            pass

        # Draw PRONTO buttons for skills selection under slot 4 (clickable)
        try:
            col1_x = SCREEN_WIDTH // 4
            col2_x = 3 * SCREEN_WIDTH // 4
            PRONTO_W, PRONTO_H = 120, 40
            y_start = 80
            slots_top = y_start + 40
            pronto_y = slots_top + 4 * 30 + 12
            pronto_p1_rect = pygame.Rect(col1_x - PRONTO_W // 2, pronto_y, PRONTO_W, PRONTO_H)
            pronto_p2_rect = pygame.Rect(col2_x - PRONTO_W // 2, pronto_y, PRONTO_W, PRONTO_H)
            mx, my = pygame.mouse.get_pos()
            for rect, done, is_focused in ((pronto_p1_rect, done_p1, cursor_p1 == 4), (pronto_p2_rect, done_p2, cursor_p2 == 4)):
                hovered = rect.collidepoint(mx, my)
                if done:
                    color = (120, 200, 120)
                elif is_focused:
                    color = (255, 255, 0)
                elif hovered:
                    color = (180, 180, 40)
                else:
                    color = (200, 200, 200)
                pygame.draw.rect(screen, (30, 30, 30), rect)
                pygame.draw.rect(screen, color, rect, 2)
                lbl = font.render('PRONTO', True, color)
                screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))
        except Exception:
            pass
        
        pygame.display.flip()
        clock.tick(30)
        
        if done_p1 and done_p2:
            selecting = False
    
    # Convert selected skill names to Skill objects
    skills_p1 = [SKILLS_PRESETS[name] for name in selected_p1]
    skills_p2 = [SKILLS_PRESETS[name] for name in selected_p2]
    
    return skills_p1, skills_p2


def select_classes_and_spawns(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    font: pygame.font.Font,
    class_presets: dict,
    bg_image: pygame.Surface = None
):
    """Create the initial menu for class selection for two players and spawn selection.
    
    Args:
        screen: The pygame display surface.
        clock: The pygame clock for frame rate control.
        font: The pygame font for rendering text.
        class_presets: Dictionary of class configurations.
        bg_image: Optional background image surface.
        
    Returns:
        Tuple containing (class_name_p1, preset_p1, x1, y1, vx1, vy1,
                         class_name_p2, preset_p2, x2, y2, vx2, vy2)
        or 'back' if user returns to main menu.
    """
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

            # Keyboard navigation and confirmation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
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
        title = font.render('Select your class (Click PRONTO to confirm)', True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        col1_x = SCREEN_WIDTH // 4
        col2_x = 3 * SCREEN_WIDTH // 4

        p1_title = font.render('Player 1', True, (255, 200, 200))
        screen.blit(p1_title, (col1_x - p1_title.get_width() // 2, 100))
        # Show which controls this player uses for skills/powers
        try:
            ctrl1 = font.render('Use: WASD', True, (200,200,200))
            screen.blit(ctrl1, (col1_x - ctrl1.get_width() // 2, 128))
        except Exception:
            pass
        for i, opt in enumerate(menu_options):
            color = (255, 255, 0) if i == selected_idx_p1 and not confirmed_p1 else (200, 200, 200)
            text = font.render(opt + ('  [CONF]' if confirmed_p1 and i == selected_idx_p1 else ''), True, color)
            screen.blit(text, (col1_x - text.get_width() // 2, 150 + i * 30))
        # Draw player 1 preview sprite
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
        try:
            ctrl2 = font.render('Use: Arrow Keys', True, (200,200,200))
            screen.blit(ctrl2, (col2_x - ctrl2.get_width() // 2, 128))
        except Exception:
            pass
        for i, opt in enumerate(menu_options):
            color = (255, 255, 0) if i == selected_idx_p2 and not confirmed_p2 else (200, 200, 200)
            text = font.render(opt + ('  [CONF]' if confirmed_p2 and i == selected_idx_p2 else ''), True, color)
            screen.blit(text, (col2_x - text.get_width() // 2, 150 + i * 30))
        
        # Draw player 2 preview sprite
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

        # Class descriptions for each player's current selection
        try:
            sel1 = menu_options[selected_idx_p1]
            pr1 = class_presets.get(sel1, {})
            text1 = []
            text1.append(f"HP: {pr1.get('max_hp','?')} | Mass: {pr1.get('mass','?')}")
            sr1 = pr1.get('speed_range', (0,0))
            text1.append(f"Speed: {int(sr1[0])}-{int(sr1[1])} | Restitution: {pr1.get('restitution','?')}")
            items1 = ", ".join(pr1.get('items', []))
            if items1:
                text1.append(f"Items: {items1}")
            d1 = pr1.get('description', '')
            desc1 = "\n".join(text1) + ("\n" + d1 if d1 else "")
            box_w, box_h = 380, 160
            lrect = pygame.Rect(max(8, (SCREEN_WIDTH//4) - box_w//2), SCREEN_HEIGHT - box_h - 70, box_w, box_h)
            draw_text_box(screen, font, sel1, desc1, lrect, accent=pr1.get('color'))
        except Exception:
            pass

        try:
            sel2 = menu_options[selected_idx_p2]
            pr2 = class_presets.get(sel2, {})
            text2 = []
            text2.append(f"HP: {pr2.get('max_hp','?')} | Mass: {pr2.get('mass','?')}")
            sr2 = pr2.get('speed_range', (0,0))
            text2.append(f"Speed: {int(sr2[0])}-{int(sr2[1])} | Restitution: {pr2.get('restitution','?')}")
            items2 = ", ".join(pr2.get('items', []))
            if items2:
                text2.append(f"Items: {items2}")
            d2 = pr2.get('description', '')
            desc2 = "\n".join(text2) + ("\n" + d2 if d2 else "")
            box_w2, box_h2 = 380, 160
            rrect = pygame.Rect(min(SCREEN_WIDTH - box_w2 - 8, (3*SCREEN_WIDTH//4) - box_w2//2), SCREEN_HEIGHT - box_h2 - 70, box_w2, box_h2)
            draw_text_box(screen, font, sel2, desc2, rrect, accent=pr2.get('color'))
        except Exception:
            pass

        info = font.render('Both players confirm to proceed to spawn selection. (P1: E to confirm | P2: Enter)', True, (180, 180, 180))
        screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, SCREEN_HEIGHT - 60))

        # Back button to return to main menu
        back_btn = pygame.Rect(12, SCREEN_HEIGHT - 60, 96, 36)
        try:
            pygame.draw.rect(screen, (30,30,30), back_btn)
            bt = font.render('RETURN', True, (200,200,200))
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

    spawn_confirmed_p1 = False
    spawn_confirmed_p2 = False

    # Start cursors inside the arena: left and right quarters
    cursor_p1 = [ARENA_X + ARENA_SIZE * 0.25, ARENA_Y + ARENA_SIZE * 0.5]
    cursor_p2 = [ARENA_X + ARENA_SIZE * 0.75, ARENA_Y + ARENA_SIZE * 0.5]
    move_speed = 6
    spawn_selecting = True

    while spawn_selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if back_btn_rect.collidepoint(mx, my):
                    return 'back'
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
        
        # Draw arena bounds
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
        # (Confirmation via keyboard: P1: E, P2: Enter)
        
        # Back button
        back_btn = pygame.Rect(12, SCREEN_HEIGHT - 60, 96, 36)
        try:
            pygame.draw.rect(screen, (30, 30, 30), back_btn)
            bt = font.render('RETURN', True, (200, 200, 200))
            screen.blit(bt, (back_btn.centerx - bt.get_width()//2, back_btn.centery - bt.get_height()//2))
        except Exception:
            pass

        pygame.display.flip()
        clock.tick(60)

        if spawn_confirmed_p1 and spawn_confirmed_p2:
            spawn_selecting = False

    # Initial random velocities sampled inside each class speed range
    def random_velocity_for_preset(preset: dict) -> tuple:
        """Generate a random velocity vector within the preset speed range.
        
        Args:
            preset: Class preset dictionary containing 'speed_range' field.
            
        Returns:
            Tuple of (vx, vy) velocity components.
        """
        sr = preset.get('speed_range', (0, 0))
        speed = random.uniform(sr[0], sr[1])
        angle = random.uniform(0, 2 * math.pi)
        return speed * math.cos(angle), speed * math.sin(angle)

    vx1, vy1 = random_velocity_for_preset(preset_p1)
    vx2, vy2 = random_velocity_for_preset(preset_p2)

    return (chosen_p1, preset_p1, cursor_p1[0], cursor_p1[1], vx1, vy1,
            chosen_p2, preset_p2, cursor_p2[0], cursor_p2[1], vx2, vy2)


def run_game() -> None:
    """Main function that initializes and runs the game loop.
    
    Handles the overall game flow including menus, game initialization,
    and the main game loop with event processing and frame rendering.
    """
    pygame.init()
    # Ensure the video/display subsystem is initialized before creating a surface.
    try:
        if not pygame.display.get_init():
            pygame.display.init()
    except Exception:
        # If display init fails, proceed; apply_display_mode will try as well.
        pass
    screen = apply_display_mode(FULLSCREEN)
    pygame.display.set_caption('ECS Pygame Ball Arena')
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    # Outer loop: allow returning to selection and restarting matches
    quit_game = False
    # Load a global background image once (used in menus and passed to RenderSystem)
    bg_scaled = None
    bg_path = os.path.join('images', 'spt_Menu', 'background.png')
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
        # Ensure local screen references the current display surface (in case settings toggled it)
        try:
            screen = pygame.display.get_surface() or screen
        except Exception:
            pass
        if menu_choice is None or menu_choice == 'quit':
            break
        if menu_choice == 'fight':
            result = select_classes_and_spawns(screen, clock, font, CLASS_PRESETS, bg_image=bg_scaled)
            if result is None or result == 'back':
                continue
        (chosen_p1, preset_p1, px1, py1, vx1, vy1,
         chosen_p2, preset_p2, px2, py2, vx2, vy2) = result

        # Select skills for both players
        skills_result = select_skills(screen, clock, font, bg_image=bg_scaled)
        if skills_result == 'back':
            continue
        skills_p1, skills_p2 = skills_result

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
            player_id=1, skills=skills_p1, vx=vx1, vy=vy1
        )

        id2 = create_ball(
            x=px2, y=py2,
            radius=preset_p2['radius'], color=preset_p2['color'],
            mass=preset_p2['mass'], restitution=preset_p2['restitution'],
            max_hp=preset_p2['max_hp'], body_damage=preset_p2['body_damage'],
            class_name=chosen_p2, items=preset_p2['items'],
            player_id=2, skills=skills_p2, vx=vx2, vy=vy2
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

        # Player 1 (top-left) - Health bar
        pb1 = esper.create_entity()
        esper.add_component(pb1, UITransform(PADDING, PADDING, 'topleft'))
        esper.add_component(pb1, UIProgressBar(BAR_W, BAR_H, bg_color=(60,60,60), fg_color=fg1, target_entity=id1, target_comp_name='Health', cur_field='current_hp', max_field='max_hp', z=100))

        # Player 1 (top-left) - Mana bar (below health)
        mb1 = esper.create_entity()
        esper.add_component(mb1, UITransform(PADDING, PADDING + BAR_H + 4, 'topleft'))
        esper.add_component(mb1, UIProgressBar(BAR_W, BAR_H, bg_color=(30,30,60), fg_color=(100, 150, 255), target_entity=id1, target_comp_name='Mana', cur_field='current_mana', max_field='max_mana', z=100))

        # Player 1 character image to the right of the bar (larger icon)
        try:
            img1 = esper.create_entity()
            # scale image larger than bar height (30% larger)
            img_path1 = getattr(r1, 'image_path', None)
            ICON_H1 = int(BAR_H * 1.6)
            if img_path1:
                img_x = PADDING + BAR_W + 12
                esper.add_component(img1, UITransform(img_x, PADDING - (ICON_H1 - BAR_H)//2, 'topleft'))
                esper.add_component(img1, UIImage(img_path1, scale=(ICON_H1, ICON_H1), z=101))
        except Exception:
            pass

        # Player 2 (top-right) - Health bar
        pb2 = esper.create_entity()
        esper.add_component(pb2, UITransform(SCREEN_WIDTH - PADDING - BAR_W, PADDING, 'topleft'))
        esper.add_component(pb2, UIProgressBar(BAR_W, BAR_H, bg_color=(60,60,60), fg_color=fg2, target_entity=id2, target_comp_name='Health', cur_field='current_hp', max_field='max_hp', z=100))

        # Player 2 (top-right) - Mana bar (below health)
        mb2 = esper.create_entity()
        esper.add_component(mb2, UITransform(SCREEN_WIDTH - PADDING - BAR_W, PADDING + BAR_H + 4, 'topleft'))
        esper.add_component(mb2, UIProgressBar(BAR_W, BAR_H, bg_color=(30,30,60), fg_color=(100, 150, 255), target_entity=id2, target_comp_name='Mana', cur_field='current_mana', max_field='max_mana', z=100))

        # Player 2 character image to the left of the bar (larger icon)
        try:
            img2 = esper.create_entity()
            img_path2 = getattr(r2, 'image_path', None)
            ICON_H2 = int(BAR_H * 1.6)
            if img_path2:
                img2_x = SCREEN_WIDTH - PADDING - BAR_W - (ICON_H2 + 12)
                esper.add_component(img2, UITransform(img2_x, PADDING - (ICON_H2 - BAR_H)//2, 'topleft'))
                esper.add_component(img2, UIImage(img_path2, scale=(ICON_H2, ICON_H2), z=101))
        except Exception:
            pass

        # In-game settings button (bottom-right) with menu icon
        try:
            icon_path = os.path.join('images', 'spt_Menu', 'settings_button.png')
            ICON_H = 56
            btn_ent = esper.create_entity()
            btn_x = SCREEN_WIDTH - PADDING - ICON_H
            btn_y = SCREEN_HEIGHT - PADDING - ICON_H
            esper.add_component(btn_ent, UITransform(btn_x, btn_y, 'topleft'))
            esper.add_component(btn_ent, UIImage(icon_path, scale=(ICON_H, ICON_H), z=200))
            # callback opens settings menu (blocks until closed)
            def _open_settings():
                nonlocal screen
                res = settings_menu(screen, clock, font)
                try:
                    # Always refresh screen from current display
                    new_screen = pygame.display.get_surface()
                    if new_screen is not None:
                        screen = new_screen
                        # update systems to new screen
                        render_sys.screen = screen
                        ui_system.screen = screen
                except Exception:
                    pass
            esper.add_component(btn_ent, UIButton(_open_settings))
        except Exception:
            pass

        # Match loop
        match_running = True
        winner = None
        current_time = 0.0
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
                
                # Handle skill casting
                if event.type == pygame.KEYDOWN:
                    # Player 1: W, A, S, D for skills 0, 1, 2, 3
                    skill_map_p1 = {
                        pygame.K_w: 0,
                        pygame.K_a: 1,
                        pygame.K_s: 2,
                        pygame.K_d: 3,
                    }
                    if event.key in skill_map_p1:
                        skill_idx = skill_map_p1[event.key]
                        # Cast skill for player 1
                        try:
                            if esper.entity_exists(id1):
                                skill_slots = esper.try_component(id1, SkillSlots)
                                mana = esper.try_component(id1, Mana)
                                if skill_slots and mana:
                                    slot = skill_slots.get_slot(skill_idx)
                                    if slot and slot.skill:
                                        if mana.current_mana >= slot.skill.mana_cost and current_time - slot.last_cast_time >= slot.skill.cooldown:
                                            slot.last_cast_time = current_time
                                            mana.current_mana -= slot.skill.mana_cost
                                            effect = SkillEffect(slot.skill.effect_type, slot.skill.effect_value, slot.skill.effect_duration)
                                            esper.add_component(id1, effect)
                                            print(f"Player 1 cast {slot.skill.name}!")
                        except Exception as e:
                            pass

                    # Player 2: up, down, left, right for skills 0, 1, 2, 3
                    skill_map_p2 = {
                        pygame.K_UP: 0,
                        pygame.K_DOWN: 1,
                        pygame.K_LEFT: 2,
                        pygame.K_RIGHT: 3,
                    } 
                    if event.key in skill_map_p2:
                        skill_idx = skill_map_p2[event.key]
                        # Cast skill for player 2
                        try:
                            if esper.entity_exists(id2):
                                skill_slots = esper.try_component(id2, SkillSlots)
                                mana = esper.try_component(id2, Mana)
                                if skill_slots and mana:
                                    slot = skill_slots.get_slot(skill_idx)
                                    if slot and slot.skill:
                                        if mana.current_mana >= slot.skill.mana_cost and current_time - slot.last_cast_time >= slot.skill.cooldown:
                                            slot.last_cast_time = current_time
                                            mana.current_mana -= slot.skill.mana_cost
                                            effect = SkillEffect(slot.skill.effect_type, slot.skill.effect_value, slot.skill.effect_duration)
                                            esper.add_component(id2, effect)
                                            print(f"Player 2 cast {slot.skill.name}!")
                        except Exception as e:
                            pass
                
                # forward events to UI
                try:
                    ui_system.push_event(event)
                except Exception:
                    pass

            dt = clock.tick(FPS) / 1000.0
            current_time += dt
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