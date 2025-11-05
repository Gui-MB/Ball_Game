import pygame


class Position:
    """Position and radius for a ball or entity."""
    
    def __init__(self, x: float, y: float, radius: int) -> None:
        self.x = x
        self.y = y
        self.radius = radius


class Velocity:
    """Current velocity for an entity."""
    
    def __init__(self, vx: float = 0.0, vy: float = 0.0) -> None:
        self.vx = vx
        self.vy = vy


class Physics:
    """Physical properties used for collisions: mass and restitution (elasticity)."""
    
    def __init__(self, mass: float, restitution: float = 0.8) -> None:
        self.mass = mass
        self.restitution = restitution


class Stats:
    """Combat statistics for an entity."""
    
    def __init__(self, max_hp: int, current_hp: int, max_speed: float, body_damage: int) -> None:
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.max_speed = max_speed
        self.body_damage = body_damage


class Health:
    """Health component for entities that can take damage."""
    
    def __init__(self, max_hp: int, current_hp: int) -> None:
        self.max_hp = max_hp
        self.current_hp = current_hp


class Damage:
    """Component for body collision damage to apply on collision."""
    
    def __init__(self, body_damage: int) -> None:
        self.body_damage = body_damage


class Class:
    """Represents the class/type of a ball (e.g., Tank, Speedster)."""
    
    def __init__(self, name: str) -> None:
        self.name = name


class Player:
    """Identifies which player controls this entity."""
    
    def __init__(self, player_id: int) -> None:
        self.player_id = player_id


class EquippedItem:
    """Items currently equipped by a ball. Stores Item objects."""
    
    def __init__(self, item_dicts: list = None) -> None:
        self.items = []
        if item_dicts:
            for item_dict in item_dicts:
                self.items.append(Item(
                    item_dict['name'],
                    item_dict['damage'],
                    item_dict['damage_reduction'],
                    item_dict.get('speed_boost', 0.0),
                    item_dict.get('knockback_strength', 0.0)
                ))


class Item:
    """Item component with customizable attributes (damage, damage_reduction, speed_boost, knockback_strength)."""
    
    def __init__(
        self,
        name: str,
        damage: int = 0,
        damage_reduction: float = 0.0,
        speed_boost: float = 0.0,
        knockback_strength: float = 0.0
    ) -> None:
        self.name = name
        self.damage = damage
        self.damage_reduction = damage_reduction
        self.speed_boost = speed_boost
        self.knockback_strength = knockback_strength

class OrbitalItem:
    """Orbital component that ties an item to a parent entity and stores orbit parameters."""
    
    def __init__(self, parent_entity, orbit_radius: float, angular_speed: float, angle: float = 0.0) -> None:
        self.parent_entity = parent_entity
        self.orbit_radius = orbit_radius
        self.angular_speed = angular_speed
        self.angle = angle


class HitboxRect:
    """Axis-aligned rectangular hitbox for items.
    
    Attributes:
        width (float): Size of the rectangle (width).
        height (float): Size of the rectangle (height).
        offset_x (float): Offset relative to the Position center.
        offset_y (float): Offset relative to the Position center.
    """
    
    def __init__(self, width: float, height: float, offset_x: float = 0.0, offset_y: float = 0.0) -> None:
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y

class ArenaBoundary:
    """Defines the arena boundaries (top-left x, y and width, height).
    
    Represents a rectangular arena that may be smaller than the whole screen.
    
    Attributes:
        x (int): Top-left x-coordinate of the arena rectangle.
        y (int): Top-left y-coordinate of the arena rectangle.
        width (int): Width of the arena.
        height (int): Height of the arena.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

class Image:
    """Render wrapper for a pygame surface."""
    
    def __init__(self, surface) -> None:
        self.surface = surface


class Rotation:
    """Rotation angle in degrees for an entity."""
    
    def __init__(self, angle: float = 0.0) -> None:
        self.angle = angle


class DesiredSpeed:
    """Stores a target/fixed speed (magnitude) an entity should maintain.
    
    Used by the collision system to renormalize velocities after collisions
    so balls keep a constant speed (ricochet behavior with fixed magnitude).
    """
    
    def __init__(self, speed: float = 0.0) -> None:
        self.speed = speed


class SpawnProtection:
    """Temporary spawn protection that prevents damage for a short time."""
    
    def __init__(self, protection_time: float = 0.4) -> None:
        self.time = protection_time


class DamageCooldown:
    """Cooldown to prevent repeated damage from the same collision."""
    
    def __init__(self, cooldown_time: float = 0.1) -> None:
        self.cooldown_time = cooldown_time
        self.last_damage_time = 0.0


class Renderable:
    """Color and optional image path used for rendering an entity."""
    
    def __init__(self, color: tuple, image_path: str = None) -> None:
        self.color = color
        self.image_path = image_path
        self.image = None


# -------------------- UI Components --------------------

class UITransform:
    """Position and anchor for UI elements."""
    
    def __init__(self, x: float, y: float, anchor: str = 'topleft') -> None:
        self.x = x
        self.y = y
        self.anchor = anchor


class UIImage:
    """Reference to an image to draw as a UI element."""
    
    def __init__(self, image_path: str, scale: tuple = None, z: int = 0) -> None:
        self.image_path = image_path
        self.scale = scale
        self.z = z


class UIButton:
    """Simple clickable button marker. Stores an optional callback."""
    
    def __init__(self, callback=None) -> None:
        self.callback = callback


class UIProgressBar:
    """Progress bar UI that can show a fraction (0.0-1.0)."""
    
    def __init__(
        self,
        width: int,
        height: int,
        bg_color: tuple = (80, 80, 80),
        fg_color: tuple = (0, 200, 0),
        target_entity=None,
        target_comp_name: str = 'Health',
        cur_field: str = 'current_hp',
        max_field: str = 'max_hp',
        z: int = 0
    ) -> None:
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
    
    Attributes:
        amount (int): The damage amount to display.
        target_entity: The entity to which this damage popup is attached.
        duration (float): Total duration the popup should display (seconds).
        time_left (float): Time remaining before the popup disappears (seconds).
        color (tuple): RGB color of the damage text.
    """
    
    def __init__(self, amount: int, target_entity, duration: float = 0.8, color: tuple = (255, 255, 255)) -> None:
        self.amount = int(amount)
        self.target_entity = target_entity
        self.duration = float(duration)
        self.time_left = float(duration)
        self.color = color


# -------------------- Mana & Skill Components --------------------

class Mana:
    """Mana pool for an entity (for casting skills).
    
    Attributes:
        max_mana (float): Maximum mana capacity.
        current_mana (float): Current mana available.
        regen_rate (float): Mana regenerated per second.
    """
    
    def __init__(self, max_mana: float, regen_rate: float = 1.0) -> None:
        self.max_mana = max_mana
        self.current_mana = max_mana
        self.regen_rate = regen_rate


class Skill:
    """A skill definition with properties and effects.
    
    Attributes:
        name (str): Display name of the skill.
        mana_cost (float): Mana required to cast.
        cooldown (float): Time before the skill can be cast again (seconds).
        effect_type (str): Type of effect ('speed_boost', 'dash', 'shield', etc.).
        effect_value (float): Magnitude of the effect.
        effect_duration (float): How long the effect lasts (seconds).
        icon_color (tuple): RGB color for UI display.
        description (str): Player-facing description of what the skill does.
    """
    
    def __init__(
        self,
        name: str,
        mana_cost: float,
        cooldown: float,
        effect_type: str,
        effect_value: float,
        effect_duration: float = 0.0,
        icon_color: tuple = (100, 100, 255),
        description: str = ""
    ) -> None:
        self.name = name
        self.mana_cost = mana_cost
        self.cooldown = cooldown
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.effect_duration = effect_duration
        self.icon_color = icon_color
        self.description = description


class SkillSlot:
    """An equipped skill slot for an entity.
    
    Attributes:
        skill (Skill): The skill object.
        slot_index (int): Which slot this skill occupies (0-3).
        last_cast_time (float): Timestamp of last cast (for cooldown tracking).
    """
    
    def __init__(self, skill: Skill, slot_index: int) -> None:
        self.skill = skill
        self.slot_index = slot_index
        self.last_cast_time = -float('inf')
    
    def is_available(self, current_time: float, current_mana: float) -> bool:
        """Check if this skill can be cast.
        
        Args:
            current_time: Current game time in seconds.
            current_mana: Current mana of the caster.
            
        Returns:
            True if cooldown is up and mana is sufficient.
        """
        time_since_last = current_time - self.last_cast_time
        return (time_since_last >= self.skill.cooldown and 
                current_mana >= self.skill.mana_cost)


class SkillSlots:
    """Container for equipped skill slots (up to 4 skills).
    
    Attributes:
        slots (list): List of SkillSlot objects indexed 0-3.
    """
    
    def __init__(self, skills: list = None) -> None:
        """Initialize skill slots.
        
        Args:
            skills: List of Skill objects (up to 4).
        """
        self.slots = [None, None, None, None]
        if skills:
            for i, skill in enumerate(skills[:4]):
                self.slots[i] = SkillSlot(skill, i)
    
    def get_slot(self, index: int) -> SkillSlot:
        """Get a skill slot by index."""
        if 0 <= index < 4:
            return self.slots[index]
        return None


class SkillEffect:
    """An active skill effect on an entity.
    
    Attributes:
        effect_type (str): Type of effect.
        effect_value (float): Magnitude.
        time_remaining (float): Duration left (seconds).
    """
    
    def __init__(self, effect_type: str, effect_value: float, duration: float) -> None:
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.time_remaining = duration