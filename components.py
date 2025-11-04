import pygame

class Position:
    '''Position and radius for a ball or entity.'''
    def __init__(self, x: float, y: float, radius: int):
        self.x = x
        self.y = y
        self.radius = radius

class Velocity:
    '''Current velocity for an entity.'''
    def __init__(self, vx: float = 0.0, vy: float = 0.0):
        self.vx = vx
        self.vy = vy

class Physics:
    '''Physical properties used for collisions: mass and restitution (elasticity).'''
    def __init__(self, mass: float, restitution: float = 0.8):
        self.mass = mass
        self.restitution = restitution

class Stats:
    '''Combat statistics for an entity.'''
    def __init__(self, max_hp: int, current_hp: int, max_speed: float, body_damage: int):
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.max_speed = max_speed
        self.body_damage = body_damage

class Health:
    '''Health component for entities that can take damage.'''
    def __init__(self, max_hp: int, current_hp: int):
        self.max_hp = max_hp
        self.current_hp = current_hp

class Damage:
    '''Component for body collision damage to apply on collision.'''
    def __init__(self, body_damage: int):
        self.body_damage = body_damage

class Class:
    '''Represents the class/type of a ball (e.g., Tank, Speedster).'''
    def __init__(self, name: str):
        self.name = name

class Player:
    '''Identifies which player controls this entity.'''
    def __init__(self, player_id: int):
        self.player_id = player_id  # 1 or 2

class EquippedItem:
    '''Items currently equipped by a ball. Stores Item objects.'''
    def __init__(self, item_dicts: list = None):
        self.items = []
        if item_dicts:
            for item_dict in item_dicts:
                self.items.append(Item(item_dict['name'], item_dict['damage'], item_dict['damage_reduction'], item_dict.get('speed_boost', 0.0), item_dict.get('knockback_strength', 0.0)))

class Item:
    '''Item component with customizable attributes (damage, damage_reduction, speed_boost, knockback_strength).'''
    def __init__(self, name: str, damage: int = 0, damage_reduction: float = 0.0, speed_boost: float = 0.0, knockback_strength: float = 0.0):
        self.name = name
        self.damage = damage
        self.damage_reduction = damage_reduction
        self.speed_boost = speed_boost
        self.knockback_strength = knockback_strength

class OrbitalItem:
    '''Orbital component that ties an item to a parent entity and stores orbit parameters.'''
    def __init__(self, parent_entity, orbit_radius: float, angular_speed: float, angle: float = 0.0):
        self.parent_entity = parent_entity
        self.orbit_radius = orbit_radius
        self.angular_speed = angular_speed
        self.angle = angle
class HitboxRect:
    '''Axis-aligned rectangular hitbox for items.

    width, height: size of the rectangle
    offset_x, offset_y: offset relative to the Position center
    '''
    def __init__(self, width: float, height: float, offset_x: float = 0.0, offset_y: float = 0.0):
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y

class ArenaBoundary:
        '''Defines the arena boundaries (top-left x,y and width and height).

        Use this to represent a rectangular arena that may be smaller than the
        whole screen. Fields:
            x, y: top-left coordinates of the arena rectangle
            width, height: size of the arena
        '''
        def __init__(self, x: int, y: int, width: int, height: int):
                self.x = x
                self.y = y
                self.width = width
                self.height = height

class Image:
    '''Render wrapper for a pygame surface.'''
    def __init__(self, surface):
        self.surface = surface

class Rotation:
    '''Rotation angle in degrees for an entity.'''
    def __init__(self, angle: float = 0.0):
        self.angle = angle


class DesiredSpeed:
    """Stores a target/fixed speed (magnitude) an entity should maintain.

    This is used by the collision system to renormalize velocities after
    collisions so balls keep a constant speed (ricochet behavior with fixed
    magnitude).
    """
    def __init__(self, speed: float = 0.0):
        self.speed = speed

class SpawnProtection:
    '''Temporary spawn protection that prevents damage for a short time.'''
    def __init__(self, protection_time: float = 0.4):
        self.time = protection_time

class DamageCooldown:
    '''Cooldown to prevent repeated damage from the same collision.'''
    def __init__(self, cooldown_time: float = 0.1):
        self.cooldown_time = cooldown_time
        self.last_damage_time = 0.0

class Renderable:
    '''Color and optional image path used for rendering an entity.'''
    def __init__(self, color: tuple, image_path: str = None):
        self.color = color
        self.image_path = image_path
        self.image = None


# -------------------- UI Components --------------------
class UITransform:
    """Position and anchor for UI elements.

    x,y are pixel coordinates. anchor can be 'topleft' or 'center'.
    """
    def __init__(self, x: float, y: float, anchor: str = 'topleft'):
        self.x = x
        self.y = y
        self.anchor = anchor


class UIImage:
    """Reference to an image to draw as a UI element.

    image_path: path to the image file relative to project root
    scale: optional (w,h) to draw image scaled
    z: draw order (lower drawn first)
    """
    def __init__(self, image_path: str, scale: tuple = None, z: int = 0):
        self.image_path = image_path
        self.scale = scale
        self.z = z


class UIButton:
    """Simple clickable button marker. Stores an optional callback.

    callback: callable invoked when button is clicked (no args).
    """
    def __init__(self, callback=None):
        self.callback = callback


class UIProgressBar:
    """Progress bar UI that can show a fraction (0.0-1.0).

    If target_entity is provided together with component/field names, the
    bar will sample the target's component fields each frame to compute
    the current ratio (e.g., Health.current_hp / Health.max_hp).
    """
    def __init__(self, width: int, height: int, bg_color=(80,80,80), fg_color=(0,200,0),
                 target_entity=None, target_comp_name='Health', cur_field='current_hp', max_field='max_hp', z: int = 0):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.target_entity = target_entity
        self.target_comp_name = target_comp_name
        self.cur_field = cur_field
        self.max_field = max_field
        self.z = z


class DamagePopup:
        """Temporary floating damage text tied to a target entity.

        Fields:
            amount: int damage amount to display
            target_entity: entity id the popup should appear over
            duration: total lifetime in seconds
            time_left: remaining lifetime in seconds
            color: RGB tuple
        """
        def __init__(self, amount: int, target_entity, duration: float = 0.8, color=(255, 255, 255)):
                self.amount = int(amount)
                self.target_entity = target_entity
                self.duration = float(duration)
                self.time_left = float(duration)
                self.color = color