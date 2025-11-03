import pygame
import esper
import random
import math
from components import Position, Velocity, Physics, Health, Damage, Renderable, ArenaBoundary, Class, Player, EquippedItem, Rotation, Item, OrbitalItem, HitboxRect, SpawnProtection, DamageCooldown
from systems import MovementSystem, WallCollisionSystem, BallCollisionSystem, HealthSystem, RotationSystem, OrbitalSystem, SpawnProtectionSystem, RenderSystem

# --- Game configuration ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60

# --- Items presets ---
ITEMS_PRESETS = {       
    'Knight Shield': {
        'name': 'Knight Shield', 'color': (0, 200, 200), 'image_path': 'images/knight_shield.png',
        'damage': 0, 'damage_reduction': 0.4, 'orbit_radius': 60, 'angular_speed': 90,
        'hitbox_w': 80, 'hitbox_h': 60, 'knockback_strength': 40.0
    },
    'Knight Sword': {
        'name': 'Knight Sword', 'color': (0, 180, 80), 'image_path': 'images/knight_sword.png',
        'damage': 30, 'damage_reduction': 0.0, 'orbit_radius': 80, 'angular_speed': 90,
        'hitbox_w': 60, 'hitbox_h': 60, 'knockback_strength': 40.0
    },
    'Mage Orb': {
        'name': 'Mage Orb', 'color': (200, 0, 200), 'image_path': 'images/mage_orb.png',
        'damage': 30, 'damage_reduction': 0.0, 'orbit_radius': 120, 'angular_speed': 300,
        'hitbox_w': 40, 'hitbox_h': 40, 'knockback_strength': 40.0
    },
    'Mage Staff': {
        'name': 'Mage Staff', 'color': (200, 0, 200), 'image_path': 'images/mage_staff.png',
        'damage': 10, 'damage_reduction': 0.0, 'orbit_radius': 60, 'angular_speed': 90,
        'hitbox_w': 60, 'hitbox_h': 80, 'knockback_strength': 70.0
    },
}

# --- Class presets ---
CLASS_PRESETS = {
    'Knight': {
        'radius': 40, 'color': (255, 0, 0), 'image_path': 'images/knight.png',
        'mass': 4.0, 'restitution': 1.0, 'speed_range': (600, 650),
        'max_hp': 200, 'body_damage': 10, 'items': ['Knight Shield', 'Knight Sword']
    },
    'Mage': {
        'radius': 30, 'color': (0, 0, 255), 'image_path': 'images/mage.png',
        'mass': 3.0, 'restitution': 1.0, 'speed_range': (500, 550),
        'max_hp': 180, 'body_damage': 5, 'items': ['Mage Orb', 'Mage Staff']
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

def select_classes_and_spawns(screen, clock, font, class_presets):
    '''Create the initial menu for class selection for two players and spawn selection.'''
    menu_options = list(class_presets.keys())
    selected_idx_p1 = 0
    selected_idx_p2 = 0
    confirmed_p1 = False
    confirmed_p2 = False

    # 1. Class selection
    selecting = True
    while selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return None

                # Player 1 Controls: W/S to move, E to confirm
                if not confirmed_p1:
                    if event.key == pygame.K_w:
                        selected_idx_p1 = (selected_idx_p1 - 1) % len(menu_options)
                    if event.key == pygame.K_s:
                        selected_idx_p1 = (selected_idx_p1 + 1) % len(menu_options)
                    if event.key == pygame.K_e:
                        confirmed_p1 = True

                # Player 2 Controls: Up/Down to move, Enter to confirm
                if not confirmed_p2:
                    if event.key == pygame.K_UP:
                        selected_idx_p2 = (selected_idx_p2 - 1) % len(menu_options)
                    if event.key == pygame.K_DOWN:
                        selected_idx_p2 = (selected_idx_p2 + 1) % len(menu_options)
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        confirmed_p2 = True

    # Draw the selection UI
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

        p2_title = font.render('Player 2', True, (200, 200, 255))
        screen.blit(p2_title, (col2_x - p2_title.get_width() // 2, 100))
        for i, opt in enumerate(menu_options):
            color = (255, 255, 0) if i == selected_idx_p2 and not confirmed_p2 else (200, 200, 200)
            text = font.render(opt + ('  [CONF]' if confirmed_p2 and i == selected_idx_p2 else ''), True, color)
            screen.blit(text, (col2_x - text.get_width() // 2, 150 + i * 30))

        info = font.render('Both players confirm to proceed to spawn selection.', True, (180, 180, 180))
        screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, SCREEN_HEIGHT - 60))

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

    cursor_p1 = [SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2]
    cursor_p2 = [3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2]
    move_speed = 6
    spawn_selecting = True

    while spawn_selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return None
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

        # Keep cursors inside the screen
        for c in (cursor_p1, cursor_p2):
            c[0] = max(1, min(SCREEN_WIDTH - 1, c[0]))
            c[1] = max(1, min(SCREEN_HEIGHT - 1, c[1]))

        screen.fill((20, 20, 20))
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

    result = select_classes_and_spawns(screen, clock, font, CLASS_PRESETS)
    if result is None:
        return
    (chosen_p1, preset_p1, px1, py1, vx1, vy1,
     chosen_p2, preset_p2, px2, py2, vx2, vy2) = result

    initialize_world()

    # Create arena bounds entity
    arena = esper.create_entity()
    esper.add_component(arena, ArenaBoundary(SCREEN_WIDTH, SCREEN_HEIGHT))

    create_ball(
        x=px1, y=py1,
        radius=preset_p1['radius'], color=preset_p1['color'],
        mass=preset_p1['mass'], restitution=preset_p1['restitution'],
        max_hp=preset_p1['max_hp'], body_damage=preset_p1['body_damage'],
        class_name=chosen_p1, items=preset_p1['items'],
        player_id=1, vx=vx1, vy=vy1
    )

    create_ball(
        x=px2, y=py2,
        radius=preset_p2['radius'], color=preset_p2['color'],
        mass=preset_p2['mass'], restitution=preset_p2['restitution'],
        max_hp=preset_p2['max_hp'], body_damage=preset_p2['body_damage'],
        class_name=chosen_p2, items=preset_p2['items'],
        player_id=2, vx=vx2, vy=vy2
    )

    esper.add_processor(RenderSystem(screen, font))
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        dt = clock.tick(FPS) / 1000.0
        esper.process(dt)
        
    pygame.quit()

if __name__ == '__main__':
    run_game()