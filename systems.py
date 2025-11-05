import esper
import pygame
import math
import os
from components import (
    Position, Velocity, Physics, Health, Damage, Renderable,
    ArenaBoundary, Rotation, OrbitalItem, Item, EquippedItem, HitboxRect,
    SpawnProtection, DamageCooldown, Player,
    DesiredSpeed,
    # UI components
    UITransform, UIImage, UIButton, UIProgressBar, DamagePopup,
    # Mana and skill components
    Mana, Skill, SkillSlots, SkillEffect,
)

# Global debug prints (can be enabled during development)
DEBUG_ENABLED = False
# Toggle visibility of hitbox outlines in the renderer
SHOW_HITBOXES = True
# Shield will block only if the attack comes from within this half-angle (degrees)
SHIELD_BLOCK_HALF_ANGLE_DEG = 60.0
SHIELD_BLOCK_HALF_ANGLE_COS = math.cos(math.radians(SHIELD_BLOCK_HALF_ANGLE_DEG))


class MovementSystem(esper.Processor):
    """Update entity positions using their velocities."""
    
    def process(self, dt: float) -> None:
        """Process movement for all entities with Position and Velocity.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        for ent, (pos, vel) in esper.get_components(Position, Velocity):
            pos.x += vel.vx * dt
            pos.y += vel.vy * dt


class WallCollisionSystem(esper.Processor):
    """Handle collision between entities and the arena walls."""
    
    def process(self, dt: float) -> None:
        """Process wall collisions for all entities.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        arena_list = esper.get_component(ArenaBoundary)
        if not arena_list:
            return
        arena_ent, arena = arena_list[0]

        for ent, (pos, vel, phys) in esper.get_components(Position, Velocity, Physics):
            hitbox_rect = esper.try_component(ent, HitboxRect)
            
            if hitbox_rect:
                rot_comp = esper.try_component(ent, Rotation)
                angle = rot_comp.angle if rot_comp else 0.0
                half_w = hitbox_rect.width / 2.0
                half_h = hitbox_rect.height / 2.0
                corners = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
                a = math.radians(angle)
                ca = math.cos(a)
                sa = math.sin(a)
                
                cx = pos.x + hitbox_rect.offset_x
                cy = pos.y + hitbox_rect.offset_y
                
                xs = []
                ys = []
                for (ox, oy) in corners:
                    wx = ca * ox - sa * oy + cx
                    wy = sa * ox + ca * oy + cy
                    xs.append(wx)
                    ys.append(wy)
                
                minx, miny = min(xs), min(ys)
                maxx, maxy = max(xs), max(ys)
                
                # Collision with walls using AABB relative to arena rectangle
                left = arena.x
                top = arena.y
                right = arena.x + arena.width
                bottom = arena.y + arena.height

                if minx < left:
                    pos.x += (left - minx)
                    vel.vx *= -phys.restitution
                elif maxx > right:
                    pos.x -= (maxx - right)
                    vel.vx *= -phys.restitution

                if miny < top:
                    pos.y += (top - miny)
                    vel.vy *= -phys.restitution
                elif maxy > bottom:
                    pos.y -= (maxy - bottom)
                    vel.vy *= -phys.restitution
            else:
                # For circular entities, use radius
                left = arena.x
                top = arena.y
                right = arena.x + arena.width
                bottom = arena.y + arena.height

                if pos.x - pos.radius < left:
                    pos.x = left + pos.radius
                    vel.vx *= -phys.restitution
                elif pos.x + pos.radius > right:
                    pos.x = right - pos.radius
                    vel.vx *= -phys.restitution

                if pos.y - pos.radius < top:
                    pos.y = top + pos.radius
                    vel.vy *= -phys.restitution
                elif pos.y + pos.radius > bottom:
                    pos.y = bottom - pos.radius
                    vel.vy *= -phys.restitution


class BallCollisionSystem(esper.Processor):
    """Handle physical collisions between balls and items (circle and AABB hitboxes)."""
    
    def process(self, dt: float) -> None:
        """Process collisions between all collidable entities.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        collidable_entities = []
        for ent, (pos, phys) in esper.get_components(Position, Physics):
            collidable_entities.append((ent, pos, phys))

        num_entities = len(collidable_entities)

        def circle_vs_rotated_rect(circle_x, circle_y, circle_r, rect_cx, rect_cy, rect_w, rect_h, rect_angle):
            a = math.radians(rect_angle)
            ca = math.cos(a)
            sa = math.sin(a)
            dx = circle_x - rect_cx
            dy = circle_y - rect_cy
            local_x = ca * dx + sa * dy
            local_y = -sa * dx + ca * dy

            half_w = rect_w / 2.0
            half_h = rect_h / 2.0
            nearest_x = max(-half_w, min(local_x, half_w))
            nearest_y = max(-half_h, min(local_y, half_h))

            nx_local = local_x - nearest_x
            ny_local = local_y - nearest_y
            dist_sq = nx_local * nx_local + ny_local * ny_local
            if dist_sq >= (circle_r * circle_r):
                return False, 0.0, 0.0, 0.0

            dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.0

            if dist == 0:
                nx_local_n, ny_local_n = 1.0, 0.0
            else:
                nx_local_n = nx_local / dist
                ny_local_n = ny_local / dist

            nx = ca * nx_local_n - sa * ny_local_n
            ny = sa * nx_local_n + ca * ny_local_n

            overlap = circle_r - dist
            return True, nx, ny, overlap

        def aabb_of_rotated_rect(rect_cx, rect_cy, rect_w, rect_h, rect_angle):
            half_w = rect_w / 2.0
            half_h = rect_h / 2.0
            corners = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
            a = math.radians(rect_angle)
            ca = math.cos(a)
            sa = math.sin(a)
            xs = []
            ys = []
            for (ox, oy) in corners:
                wx = ca * ox - sa * oy + rect_cx
                wy = sa * ox + ca * oy + rect_cy
                xs.append(wx)
                ys.append(wy)
            return min(xs), min(ys), max(xs), max(ys)

        for i in range(num_entities):
            ent1, pos1, phys1 = collidable_entities[i]

            for j in range(i + 1, num_entities):
                ent2, pos2, phys2 = collidable_entities[j]

                ent1_rect = esper.try_component(ent1, HitboxRect)
                ent2_rect = esper.try_component(ent2, HitboxRect)

                collision = False
                nx = 0.0
                ny = 0.0
                distance = 0.0
                overlap = 0.0

                # circle-circle
                if not ent1_rect and not ent2_rect:
                    dx = pos2.x - pos1.x
                    dy = pos2.y - pos1.y
                    distance_sq = dx*dx + dy*dy
                    min_distance = pos1.radius + pos2.radius
                    if distance_sq < (min_distance * min_distance) and distance_sq > 0:
                        collision = True
                        distance = math.sqrt(distance_sq)
                        nx = dx / distance
                        ny = dy / distance
                        overlap = min_distance - distance

                # circle (ent1) vs rect (ent2)
                elif not ent1_rect and ent2_rect:
                    rx = pos2.x + ent2_rect.offset_x
                    ry = pos2.y + ent2_rect.offset_y
                    rect_angle = 0.0
                    rot_comp = esper.try_component(ent2, Rotation)
                    if rot_comp:
                        rect_angle = rot_comp.angle

                    collided, nx, ny, overlap = circle_vs_rotated_rect(pos1.x, pos1.y, pos1.radius, rx, ry, ent2_rect.width, ent2_rect.height, rect_angle)
                    if collided:
                        collision = True

                # rect (ent1) vs circle (ent2)
                elif ent1_rect and not ent2_rect:
                    rx = pos1.x + ent1_rect.offset_x
                    ry = pos1.y + ent1_rect.offset_y
                    rect_angle = 0.0
                    rot_comp = esper.try_component(ent1, Rotation)
                    if rot_comp:
                        rect_angle = rot_comp.angle

                    collided, nx, ny, overlap = circle_vs_rotated_rect(pos2.x, pos2.y, pos2.radius, rx, ry, ent1_rect.width, ent1_rect.height, rect_angle)
                    if collided:
                        nx, ny = -nx, -ny
                        collision = True

                # rect vs rect (use AABB of rotated rects as conservative test)
                else:
                    rx1 = pos1.x + ent1_rect.offset_x
                    ry1 = pos1.y + ent1_rect.offset_y
                    angle1 = 0.0
                    rc1 = esper.try_component(ent1, Rotation)
                    if rc1:
                        angle1 = rc1.angle

                    rx2 = pos2.x + ent2_rect.offset_x
                    ry2 = pos2.y + ent2_rect.offset_y
                    angle2 = 0.0
                    rc2 = esper.try_component(ent2, Rotation)
                    if rc2:
                        angle2 = rc2.angle

                    minx1, miny1, maxx1, maxy1 = aabb_of_rotated_rect(rx1, ry1, ent1_rect.width, ent1_rect.height, angle1)
                    minx2, miny2, maxx2, maxy2 = aabb_of_rotated_rect(rx2, ry2, ent2_rect.width, ent2_rect.height, angle2)
                    if (minx1 <= maxx2 and maxx1 >= minx2 and miny1 <= maxy2 and maxy1 >= miny2):
                        collision = True
                        dx = (rx2 - rx1)
                        dy = (ry2 - ry1)
                        dist = math.sqrt(dx*dx + dy*dy)
                        if dist > 0:
                            nx = dx / dist
                            ny = dy / dist
                        else:
                            nx, ny = 1.0, 0.0
                        # Calculate overlap more accurately using penetration depth
                        overlap_x = min(maxx1 - minx2, maxx2 - minx1) if maxx1 > minx2 else 0
                        overlap_y = min(maxy1 - miny2, maxy2 - miny1) if maxy1 > miny2 else 0
                        overlap = min(overlap_x, overlap_y) if overlap_x > 0 and overlap_y > 0 else max(overlap_x, overlap_y)

                if not collision:
                    continue

                # Move entities out of overlap using computed normal and overlap
                total_mass = phys1.mass + phys2.mass
                if total_mass == 0:
                    total_mass = 1.0
                move_ratio1 = phys2.mass / total_mass
                move_ratio2 = phys1.mass / total_mass

                pos1.x -= nx * overlap * move_ratio1
                pos1.y -= ny * overlap * move_ratio1
                pos2.x += nx * overlap * move_ratio2
                pos2.y += ny * overlap * move_ratio2

                # 3. Velocity Resolution (Relative Elastic Collision)
                vel1 = esper.try_component(ent1, Velocity)
                vel2 = esper.try_component(ent2, Velocity)

                if vel1 and vel2:
                    rvx = vel2.vx - vel1.vx
                    rvy = vel2.vy - vel1.vy

                    # Relative velocity along the normal
                    vel_along_normal = rvx * nx + rvy * ny

                    # Only apply velocity resolution if entities are approaching
                    if vel_along_normal <= 0:
                        # Coefficient of restitution (use the smaller)
                        e = min(phys1.restitution, phys2.restitution)

                        # Scalar impulse
                        j_scalar = -(1 + e) * vel_along_normal

                        # Safe inverse masses to avoid division by zero
                        eps = 1e-8
                        inv_m1 = 1.0 / phys1.mass if phys1.mass > eps else 0.0
                        inv_m2 = 1.0 / phys2.mass if phys2.mass > eps else 0.0
                        denom = inv_m1 + inv_m2
                        if denom > eps:
                            j_scalar = j_scalar / denom
                        else:
                            j_scalar = 0.0

                        impulse_x = j_scalar * nx
                        impulse_y = j_scalar * ny

                        if phys1.mass > eps:
                            vel1.vx -= impulse_x * inv_m1
                            vel1.vy -= impulse_y * inv_m1
                        if phys2.mass > eps:
                            vel2.vx += impulse_x * inv_m2
                            vel2.vy += impulse_y * inv_m2

                current_time = pygame.time.get_ticks() / 1000.0
                
                ent1_is_item = esper.has_component(ent1, OrbitalItem) and esper.has_component(ent1, Item)
                ent2_is_item = esper.has_component(ent2, OrbitalItem) and esper.has_component(ent2, Item)
                
                def get_entity_damage(ent):
                    if esper.has_component(ent, Item):
                        return esper.component_for_entity(ent, Item).damage
                    elif esper.has_component(ent, Damage):
                        return esper.component_for_entity(ent, Damage).body_damage
                    return 0
                
                def get_damage_reduction(ent):
                    if esper.has_component(ent, EquippedItem):
                        equipped = esper.component_for_entity(ent, EquippedItem)
                        total_reduction = sum(item.damage_reduction for item in equipped.items)
                        return min(1.0, total_reduction)
                    return 0.0

                # --- Skill helpers ---
                def get_active_damage_boost_multiplier(ent):
                    """Return outgoing damage multiplier from an active SkillEffect.

                    If the entity has a SkillEffect of type 'damage_boost', use its
                    effect_value as a multiplicative boost (>1 means increase). If no
                    such effect is found, return 1.0.
                    """
                    try:
                        eff = esper.try_component(ent, SkillEffect)
                        if eff and getattr(eff, 'effect_type', None) == 'damage_boost' and getattr(eff, 'time_remaining', 0) > 0:
                            val = float(getattr(eff, 'effect_value', 1.0))
                            # Guard against non-sensical values
                            return max(0.0, val)
                    except Exception:
                        pass
                    return 1.0

                def get_active_damage_reduction_ratio(ent):
                    """Return incoming damage reduction ratio from active SkillEffect.

                    If the entity has a SkillEffect of type 'damage_reduction', treat
                    effect_value as a ratio in [0..1], where 0.5 means reduce damage by 50%.
                    """
                    try:
                        eff = esper.try_component(ent, SkillEffect)
                        if eff and getattr(eff, 'effect_type', None) == 'damage_reduction' and getattr(eff, 'time_remaining', 0) > 0:
                            val = float(getattr(eff, 'effect_value', 0.0))
                            # Clamp to [0,1]
                            return max(0.0, min(1.0, val))
                    except Exception:
                        pass
                    return 0.0
                
                def get_player_name(ent):
                    if esper.has_component(ent, Player):
                        player_id = esper.component_for_entity(ent, Player).player_id
                        return f"Player {player_id}"
                    return f"Entity {ent}"

                def get_damage_source_desc(attacker_ent):
                    if attacker_ent is None:
                        return "Unknown source"
                    if esper.has_component(attacker_ent, Item):
                        item_c = esper.component_for_entity(attacker_ent, Item)
                        orbital_c = esper.try_component(attacker_ent, OrbitalItem)
                        owner = orbital_c.parent_entity if orbital_c else None
                        owner_name = get_player_name(owner) if owner is not None else f"Entity {owner}"
                        return f"{owner_name}'s item '{item_c.name}'"
                    # If attacker is a body with Damage component
                    if esper.has_component(attacker_ent, Damage):
                        return f"{get_player_name(attacker_ent)}'s body"
                    return get_player_name(attacker_ent)
                
                vel1_comp = esper.try_component(ent1, Velocity)
                vel2_comp = esper.try_component(ent2, Velocity)

                if ent1_is_item or ent2_is_item:
                    knockback_impulse = 0.0
                    if ent1_is_item:
                        item1_comp = esper.component_for_entity(ent1, Item)
                        knockback_impulse += getattr(item1_comp, 'knockback_strength', 0.0)
                    if ent2_is_item:
                        item2_comp = esper.component_for_entity(ent2, Item)
                        knockback_impulse += getattr(item2_comp, 'knockback_strength', 0.0)
                    
                    if knockback_impulse > 0 and vel1_comp and vel2_comp:
                        eps = 1e-8
                        inv_m1 = 1.0 / phys1.mass if phys1.mass > eps else 0.0
                        inv_m2 = 1.0 / phys2.mass if phys2.mass > eps else 0.0
                        knockback_x = knockback_impulse * nx
                        knockback_y = knockback_impulse * ny
                        if phys1.mass > eps:
                            vel1_comp.vx -= knockback_x * inv_m1
                            vel1_comp.vy -= knockback_y * inv_m1
                        if phys2.mass > eps:
                            vel2_comp.vx += knockback_x * inv_m2
                            vel2_comp.vy += knockback_y * inv_m2

                    def _renormalize_if_desired(e, vel_comp):
                        try:
                            ds = esper.try_component(e, DesiredSpeed)
                        except Exception:
                            ds = None
                        if vel_comp and ds:
                            mag = math.hypot(vel_comp.vx, vel_comp.vy)
                            if mag > 1e-6:
                                target = float(ds.speed)
                                if target > 0:
                                    scale = target / mag
                                    vel_comp.vx *= scale
                                    vel_comp.vy *= scale

                    _renormalize_if_desired(ent1, vel1_comp)
                    _renormalize_if_desired(ent2, vel2_comp)

                # body vs body
                # NOTE: Bodies do NOT inflict HP damage on each other on contact.
                # Only item hitboxes (orbital items / weapons) apply damage when
                # they collide with a body. Preserve physics (position/velocity)
                # resolution above, but skip any HP modification here.
                if not ent1_is_item and not ent2_is_item:
                    continue

                # both are items -> do NOT apply damage to their parents
                # Items colliding with each other should not directly reduce the health
                # of the owning entities. Keep other collision effects (knockback) but
                # skip health changes here.
                elif ent1_is_item and ent2_is_item:
                    item1_comp = esper.component_for_entity(ent1, Item)
                    item2_comp = esper.component_for_entity(ent2, Item)
                    orbital1 = esper.component_for_entity(ent1, OrbitalItem)
                    orbital2 = esper.component_for_entity(ent2, OrbitalItem)

                    parent1 = getattr(orbital1, 'parent_entity', None)
                    parent2 = getattr(orbital2, 'parent_entity', None)

                    # If both items belong to the same parent, ignore entirely
                    if parent1 is not None and parent1 == parent2:
                        continue

                    # Optional: respect cooldowns or other side-effects, but do not
                    # modify Health components for either parent in item-vs-item collisions.
                    # This preserves intended knockback and physics while preventing
                    # unintended health loss when two orbitals overlap.
                    if DEBUG_ENABLED:
                        p1_name = get_player_name(parent1) if parent1 is not None else f"Entity {parent1}"
                        p2_name = get_player_name(parent2) if parent2 is not None else f"Entity {parent2}"
                        print(f"Item vs Item collision between {get_damage_source_desc(ent1)} and {get_damage_source_desc(ent2)}; not applying HP changes to {p1_name} or {p2_name}.")

                # one is item, other is body
                else:
                    if ent1_is_item:
                        item_ent = ent1
                        body_ent = ent2
                    else:
                        item_ent = ent2
                        body_ent = ent1

                    item_comp = esper.component_for_entity(item_ent, Item)
                    orbital_comp = esper.component_for_entity(item_ent, OrbitalItem)
                    parent_ent = getattr(orbital_comp, 'parent_entity', None)

                    # Skip if item collided with its own parent (no self-damage)
                    if parent_ent is not None and parent_ent == body_ent:
                        continue

                    # Skip damage if either entity has spawn protection
                    if esper.has_component(body_ent, SpawnProtection):
                        continue
                    if parent_ent and esper.has_component(parent_ent, SpawnProtection):
                        continue

                    # Check damage cooldowns
                    cooldown_body = esper.try_component(body_ent, DamageCooldown)
                    cooldown_parent = parent_ent and esper.try_component(parent_ent, DamageCooldown)
                    
                    # Skip if either entity is on cooldown
                    if cooldown_body and current_time - cooldown_body.last_damage_time < cooldown_body.cooldown_time:
                        continue
                    if cooldown_parent and current_time - cooldown_parent.last_damage_time < cooldown_parent.cooldown_time:
                        continue

                    # Item damages the body it collided with
                    # NOTE: do NOT apply global equipped-item reductions to the body here —
                    # reductions should only apply if the specific item (e.g., a shield)
                    # was involved in the collision. Since the item is the collider, the
                    # body's equipped items do not automatically reduce this hit.
                    # Base damage from item
                    item_damage = float(item_comp.damage)
                    # Apply attacker (item owner's) damage boost, if any
                    attacker_boost = 1.0
                    if parent_ent and esper.entity_exists(parent_ent):
                        attacker_boost = get_active_damage_boost_multiplier(parent_ent)
                    boosted_item_damage = item_damage * attacker_boost
                    damage_to_body = int(max(0, round(boosted_item_damage)))
                    
                    if esper.has_component(body_ent, Health) and damage_to_body > 0:
                        health_body = esper.component_for_entity(body_ent, Health)
                        # Check nearby orbital shields of the body to see if they intercepted the incoming item
                        attacker_pos = esper.component_for_entity(item_ent, Position)
                        attacker_radius = getattr(attacker_pos, 'radius', 0)
                        # total reduction accumulated from any shields that intercepted
                        intercepted_reduction = 0.0
                        for shield_ent, (s_pos, s_orb) in esper.get_components(Position, OrbitalItem):
                            if s_orb.parent_entity != body_ent:
                                continue
                            # shield must have an Item component and a HitboxRect to block
                            shield_item = esper.try_component(shield_ent, Item)
                            shield_hit = esper.try_component(shield_ent, HitboxRect)
                            if not shield_item or not shield_hit:
                                continue
                            # rotation of shield
                            shield_angle = 0.0
                            shield_rot = esper.try_component(shield_ent, Rotation)
                            if shield_rot:
                                shield_angle = shield_rot.angle

                            # precise test: circle (attacker item) vs rotated rect (shield)
                            collided_shield, _, _, _ = circle_vs_rotated_rect(attacker_pos.x, attacker_pos.y, attacker_radius, s_pos.x + shield_hit.offset_x, s_pos.y + shield_hit.offset_y, shield_hit.width, shield_hit.height, shield_angle)
                            if collided_shield:
                                intercepted_reduction = max(intercepted_reduction, getattr(shield_item, 'damage_reduction', 0.0))

                        # Combine reductions: intercepted shield(s) and defender's skill-based reduction
                        defender_skill_reduction = get_active_damage_reduction_ratio(body_ent)
                        total_multiplier = (1.0 - max(0.0, min(1.0, intercepted_reduction))) * (1.0 - defender_skill_reduction)
                        final_damage = int(max(0, round(damage_to_body * total_multiplier)))

                        health_body.current_hp -= final_damage
                        # Print feedback reflecting reductions if any
                        if final_damage != damage_to_body:
                            reduced_from = damage_to_body
                            # Compute overall reduction percent for display
                            overall_reduction = 1.0 - (final_damage / reduced_from if reduced_from > 0 else 1.0)
                            pct = int(round(overall_reduction * 100))
                            print(f"{get_damage_source_desc(item_ent)} dealt {final_damage} damage to {get_player_name(body_ent)} (reduced from {reduced_from} by {pct}%)")
                        else:
                            print(f"{get_damage_source_desc(item_ent)} dealt {final_damage} damage to {get_player_name(body_ent)}")
                        # Create a floating damage popup tied to this body
                        try:
                            popup_ent = esper.create_entity()
                            esper.add_component(popup_ent, DamagePopup(final_damage, body_ent, duration=0.9, color=(255, 220, 60)))
                        except Exception:
                            pass
                        if cooldown_body:
                            cooldown_body.last_damage_time = current_time

                    # Body damages the item's parent (mutual damage in collision)
                    # Apply reduction only from the colliding item itself (e.g., a shield)
                    # Outgoing body damage (from the non-item body that was hit by the item)
                    body_damage = float(get_entity_damage(body_ent))
                    # Apply attacker's damage boost if present
                    attacker2_boost = get_active_damage_boost_multiplier(body_ent)
                    boosted_body_damage = body_damage * attacker2_boost
                    # Determine if the colliding item is actually between the parent and the attacker
                    item_block_reduction = 0.0
                    try:
                        if item_comp and parent_ent and esper.entity_exists(parent_ent):
                            pos_item = esper.component_for_entity(item_ent, Position)
                            pos_parent = esper.component_for_entity(parent_ent, Position)
                            pos_body = esper.component_for_entity(body_ent, Position)
                            # shield forward = from parent -> item
                            fx = pos_item.x - pos_parent.x
                            fy = pos_item.y - pos_parent.y
                            f_len = math.hypot(fx, fy)
                            if f_len > 0:
                                fx /= f_len
                                fy /= f_len
                                # direction from parent to body
                                bx = pos_body.x - pos_parent.x
                                by = pos_body.y - pos_parent.y
                                b_len = math.hypot(bx, by)
                                if b_len > 0:
                                    bx /= b_len
                                    by /= b_len
                                    dot = fx * bx + fy * by
                                    # Debug info (prints removed to reduce log noise)

                                    # Also check item's Rotation-based facing (useful if offsets or image orientation differ)
                                    rot_comp = esper.try_component(item_ent, Rotation)
                                    dot_rot = dot
                                    if rot_comp:
                                        a_rad = math.radians(rot_comp.angle)
                                        rx = math.cos(a_rad)
                                        ry = math.sin(a_rad)
                                        dot_rot = rx * bx + ry * by

                                    # if either positional radial check or rotation-based check passes, apply reduction
                                    if dot >= SHIELD_BLOCK_HALF_ANGLE_COS or dot_rot >= SHIELD_BLOCK_HALF_ANGLE_COS:
                                        item_block_reduction = getattr(item_comp, 'damage_reduction', 0.0)
                    except Exception:
                        item_block_reduction = getattr(item_comp, 'damage_reduction', 0.0) if item_comp else 0.0

                    # Apply defender's skill reduction as well (on the item's parent taking damage)
                    defender2_skill_reduction = get_active_damage_reduction_ratio(parent_ent) if parent_ent else 0.0
                    total_multiplier2 = (1.0 - item_block_reduction) * (1.0 - defender2_skill_reduction)
                    damage_to_parent = int(max(0, round(boosted_body_damage * total_multiplier2)))
                    
                    if parent_ent and esper.entity_exists(parent_ent) and esper.has_component(parent_ent, Health) and damage_to_parent > 0:
                        parent_health = esper.component_for_entity(parent_ent, Health)
                        parent_health.current_hp -= damage_to_parent
                        # Feedback printing, showing combined reductions
                        original = int(max(0, round(boosted_body_damage)))
                        if damage_to_parent != original:
                            overall_reduction2 = 1.0 - (damage_to_parent / original if original > 0 else 1.0)
                            pct2 = int(round(overall_reduction2 * 100))
                            print(f"{get_damage_source_desc(body_ent)} dealt {damage_to_parent} damage to {get_player_name(parent_ent)} (reduced from {original} by {pct2}%)")
                        else:
                            print(f"{get_damage_source_desc(body_ent)} dealt {damage_to_parent} damage to {get_player_name(parent_ent)}")
                        if cooldown_parent:
                            cooldown_parent.last_damage_time = current_time


class HealthSystem(esper.Processor):
    """Check entity health and remove entities whose HP <= 0."""
    
    def process(self, dt: float) -> None:
        """Process health checks and destroy dead entities.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        entities_to_destroy = []
        for ent, health in esper.get_component(Health):
            if health.current_hp <= 0:
                entities_to_destroy.append(ent)

        for ent in entities_to_destroy:
            for item_ent, orbital in esper.get_component(OrbitalItem):
                if orbital.parent_entity == ent:
                    esper.delete_entity(item_ent)

            esper.delete_entity(ent)
            print(f'Entity {ent} has been destroyed.')


class RotationSystem(esper.Processor):
    """Update entity rotation based on time."""
    
    def process(self, dt: float) -> None:
        """Update rotation for all non-orbital entities.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        # Only auto-rotate entities that are not orbital items. Orbital items
        # are oriented explicitly by the OrbitalSystem to face targets.
        for ent, rot in esper.get_component(Rotation):
            if esper.has_component(ent, OrbitalItem):
                continue
            rot.angle += 180 * dt
            rot.angle %= 360


class SpawnProtectionSystem(esper.Processor):
    """Decrement spawn protection timers and remove the component when expired."""
    
    def process(self, dt: float) -> None:
        """Update spawn protection timers for all protected entities.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        for ent, protection in list(esper.get_component(SpawnProtection)):
            protection.time -= dt
            if protection.time <= 0:
                try:
                    esper.remove_component(ent, SpawnProtection)
                except Exception:
                    protection.time = 0


class OrbitalSystem(esper.Processor):
    """Update positions of orbital items around their parent balls."""
    
    def process(self, dt: float) -> None:
        """Update orbital item positions and rotations.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        for ent, (pos, orbital) in esper.get_components(Position, OrbitalItem):
            # If parent is gone, delete the orbital item
            if not (esper.entity_exists(orbital.parent_entity) and esper.has_component(orbital.parent_entity, Position)):
                try:
                    esper.delete_entity(ent)
                except Exception:
                    pass
                continue

            parent_pos = esper.component_for_entity(orbital.parent_entity, Position)

            # Find an enemy target to face: look for the first entity with a Player
            # component whose player_id differs from the parent's player_id.
            target = None
            try:
                parent_player = esper.try_component(orbital.parent_entity, Player)
                parent_pid = parent_player.player_id if parent_player else None
                for e, p in esper.get_component(Position):
                    if e == orbital.parent_entity:
                        continue
                    pl = esper.try_component(e, Player)
                    if pl and parent_pid is not None and pl.player_id != parent_pid:
                        target = p
                        break
                # Fallback: if no Player found, pick nearest other entity with Health
                if target is None:
                    best = None
                    best_dist = None
                    for e, p in esper.get_component(Position):
                        if e == orbital.parent_entity:
                            continue
                        if esper.has_component(e, Health):
                            dx = p.x - parent_pos.x
                            dy = p.y - parent_pos.y
                            d = dx*dx + dy*dy
                            if best_dist is None or d < best_dist:
                                best_dist = d
                                best = p
                    target = best
            except Exception:
                target = None

            # Advance the orbital angle so the item keeps orbiting around its parent
            orbital.angle += orbital.angular_speed * dt
            orbital.angle %= 360

            # Compute orbital position using the orbital.angle (so item orbits)
            angle_rad = math.radians(orbital.angle)
            pos.x = parent_pos.x + orbital.orbit_radius * math.cos(angle_rad)
            pos.y = parent_pos.y + orbital.orbit_radius * math.sin(angle_rad)

            # Determine facing: compute angle from parent to target if available
            facing_angle = None
            if target is not None:
                dx = target.x - parent_pos.x
                dy = target.y - parent_pos.y
                facing_angle = math.degrees(math.atan2(dy, dx))

            # Update Rotation to face the enemy while the item continues to orbit.
            rot = esper.try_component(ent, Rotation)
            if rot:
                if facing_angle is not None:
                    rot.angle = facing_angle
                else:
                    # If no target, align visual rotation with orbital motion
                    rot.angle = orbital.angle


class RenderSystem(esper.Processor):
    """Render entities to the screen."""
    
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, bg_image: pygame.Surface = None) -> None:
        """Initialize the render system.
        
        Args:
            screen: The pygame display surface.
            font: The pygame font for rendering text.
            bg_image: Optional background image surface.
        """
        super().__init__()
        self.screen = screen
        self.font = font
        self.image_cache = {}  # Cache for loaded images
        # Visual scale factor for sprites (0.7 = 70% => reduce size by 30%)
        self.visual_scale = 0.7
        # Optional arena sprite: draw centered in the arena rectangle. Try
        # to load `images/spt_Menu/arena_background.png` if present.
        self.arena_sprite_path = os.path.join('images', 'spt_Menu', 'arena_background.png')
        self.arena_sprite = None
        try:
            if os.path.exists(self.arena_sprite_path):
                self.arena_sprite = pygame.image.load(self.arena_sprite_path).convert_alpha()
        except Exception:
            self.arena_sprite = None
        # Optional background image for the whole screen. If a surface is
        # provided by the caller, use it; otherwise try loading from disk.
        self.bg_image = bg_image
        if self.bg_image is None:
            self.bg_image_path = os.path.join('images', 'spt_Menu', 'background.png')
            try:
                if os.path.exists(self.bg_image_path):
                    self.bg_image = pygame.image.load(self.bg_image_path).convert()
            except Exception:
                self.bg_image = None

    def process(self, dt: float) -> None:
        """Render all game entities and UI to the screen.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        # Draw background (image if available, otherwise clear to black)
        if self.bg_image:
            try:
                sw, sh = self.screen.get_size()
                bg_scaled = pygame.transform.scale(self.bg_image, (sw, sh))
                self.screen.blit(bg_scaled, (0, 0))
            except Exception:
                self.screen.fill((0, 0, 0))
        else:
            self.screen.fill((0, 0, 0))

        # Draw arena background (image if available, otherwise outline)
        arena_list = esper.get_component(ArenaBoundary)
        if arena_list:
            _, arena = arena_list[0]
            try:
                if self.arena_sprite:
                    # Scale the sprite to fit within the arena while preserving aspect ratio
                    sw, sh = self.arena_sprite.get_size()
                    max_w = int(arena.width)
                    max_h = int(arena.height)
                    scale = min(max_w / sw, max_h / sh, 1.0)
                    draw_w = max(1, int(sw * scale))
                    draw_h = max(1, int(sh * scale))
                    try:
                        sprite_scaled = pygame.transform.scale(self.arena_sprite, (draw_w, draw_h))
                        draw_x = int(arena.x + (arena.width - draw_w) / 2)
                        draw_y = int(arena.y + (arena.height - draw_h) / 2)
                        self.screen.blit(sprite_scaled, (draw_x, draw_y))
                    except Exception:
                        pygame.draw.rect(self.screen, (30, 30, 30), pygame.Rect(int(arena.x), int(arena.y), int(arena.width), int(arena.height)), 2)
                else:
                    pygame.draw.rect(self.screen, (30, 30, 30), pygame.Rect(int(arena.x), int(arena.y), int(arena.width), int(arena.height)), 2)
            except Exception:
                pass

        # Draw balls (entities with Health)
        for ent, (pos, render, health) in esper.get_components(Position, Renderable, Health):
            if render.image_path and render.image_path not in self.image_cache:
                try:
                    self.image_cache[render.image_path] = pygame.image.load(render.image_path).convert_alpha()
                except Exception:
                    # Catch missing files and other image load errors
                    self.image_cache[render.image_path] = None

            image = self.image_cache.get(render.image_path)
            if image:
                # Scale visual sprite down by visual_scale (keep physics radius unchanged)
                draw_w = max(1, int(pos.radius * 2 * self.visual_scale))
                draw_h = max(1, int(pos.radius * 2 * self.visual_scale))
                scaled_image = pygame.transform.scale(image, (draw_w, draw_h))

                # NOTE: do not rotate the sprite image when drawing. Rotation
                # is still used by physics/hitbox logic, but visual sprites are
                # kept axis-aligned for a cleaner look.
                rect = scaled_image.get_rect(center=(int(pos.x), int(pos.y)))
                self.screen.blit(scaled_image, rect)
            else:
                # Fallback to circle (visual only scaled)
                pygame.draw.circle(self.screen, render.color, (int(pos.x), int(pos.y)), max(1, int(pos.radius * self.visual_scale)))


        # Draw orbital items (entities without Health)
        for ent, (pos, render) in esper.get_components(Position, Renderable):
            if esper.has_component(ent, Health):
                continue

            # Try to render image if provided
            image = None
            if render.image_path:
                if render.image_path not in self.image_cache:
                    try:
                        self.image_cache[render.image_path] = pygame.image.load(render.image_path).convert_alpha()
                    except Exception:
                        self.image_cache[render.image_path] = None
                image = self.image_cache.get(render.image_path)

            hb = esper.try_component(ent, HitboxRect)
            if image:
                if hb:
                    w, h = int(hb.width), int(hb.height)
                    cx = int(pos.x + hb.offset_x)
                    cy = int(pos.y + hb.offset_y)
                else:
                    w, h = int(pos.radius * 2), int(pos.radius * 2)
                    cx, cy = int(pos.x), int(pos.y)

                # Apply visual scale to item sprite dimensions
                draw_w = max(1, int(w * self.visual_scale))
                draw_h = max(1, int(h * self.visual_scale))

                scaled = pygame.transform.scale(image, (draw_w, draw_h))
                # Rotate orbital item sprites to face their target. Balls
                # (entities with Health) remain axis-aligned for clarity.
                rot_comp = esper.try_component(ent, Rotation)
                if esper.has_component(ent, OrbitalItem) and rot_comp:
                    try:
                        # Pygame rotates counter-clockwise; our rotation angle
                        # is world-space degrees where 0 points to the right, so
                        # negate to get the correct visual orientation.
                        rotated = pygame.transform.rotate(scaled, -rot_comp.angle)
                        rect = rotated.get_rect(center=(cx, cy))
                        self.screen.blit(rotated, rect)
                    except Exception:
                        rect = scaled.get_rect(center=(cx, cy))
                        self.screen.blit(scaled, rect)
                else:
                    rect = scaled.get_rect(center=(cx, cy))
                    self.screen.blit(scaled, rect)
            else:
                # Fallback to drawing a rect (if hitbox) or a circle
                if hb:
                    rect = pygame.Rect(int(pos.x + hb.offset_x - hb.width/2), int(pos.y + hb.offset_y - hb.height/2), int(hb.width), int(hb.height))
                    pygame.draw.rect(self.screen, render.color, rect)
                else:
                    pygame.draw.circle(self.screen, render.color, (int(pos.x), int(pos.y)), max(1, int(pos.radius * self.visual_scale)))
        # Debug: draw hitbox outlines and shield facing vectors
        if SHOW_HITBOXES:
            for ent, (pos, hb) in esper.get_components(Position, HitboxRect):
                rot_comp = esper.try_component(ent, Rotation)
                angle = rot_comp.angle if rot_comp else 0.0
                cx = pos.x + hb.offset_x
                cy = pos.y + hb.offset_y
                half_w = hb.width / 2.0
                half_h = hb.height / 2.0
                a = math.radians(angle)
                ca = math.cos(a)
                sa = math.sin(a)
                corners = []
                for (ox, oy) in [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]:
                    wx = ca * ox - sa * oy + cx
                    wy = sa * ox + ca * oy + cy
                    corners.append((int(wx), int(wy)))

                # Color shields differently
                item_comp = esper.try_component(ent, Item)
                color = (0, 255, 0) if (item_comp and getattr(item_comp, 'damage_reduction', 0) > 0) else (255, 0, 0)
                try:
                    pygame.draw.polygon(self.screen, color, corners, 1)
                except Exception:
                    pass

                # If this is an orbital item, draw a line from parent to item to show facing
                orbital = esper.try_component(ent, OrbitalItem)
                if orbital and orbital.parent_entity and esper.entity_exists(orbital.parent_entity) and esper.has_component(orbital.parent_entity, Position):
                    parent_pos = esper.component_for_entity(orbital.parent_entity, Position)
                    pygame.draw.line(self.screen, (0, 128, 255), (int(parent_pos.x), int(parent_pos.y)), (int(pos.x), int(pos.y)), 1)

            # Draw circular hitboxes for ball bodies (entities with Health)
            for ent_b, (pos_b, render_b, health_b) in esper.get_components(Position, Renderable, Health):
                try:
                    # Yellow outline for body hitboxes (visual size)
                    pygame.draw.circle(self.screen, (255, 255, 0), (int(pos_b.x), int(pos_b.y)), max(1, int(pos_b.radius * self.visual_scale)), 1)
                except Exception:
                    pass

    # NOTE: Present the frame after all rendering (UI is rendered by UISystem
    # so the flip is done there). RenderSystem does not call flip.


class UISystem(esper.Processor):
    """Draw UI elements and handle simple UI events.
    
    Use components: UITransform + UIImage to draw images. UIButton enables
    click callbacks. UIProgressBar draws a bar and can sample a target
    entity's component (e.g., Health) to compute its fraction.
    """
    
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Initialize the UI system.
        
        Args:
            screen: The pygame display surface.
            font: The pygame font for rendering text.
        """
        super().__init__()
        self.screen = screen
        self.font = font
        self.image_cache = {}
        self.event_queue = []

    def load(self, path: str) -> pygame.Surface:
        """Load an image from disk or return cached version.
        
        Args:
            path: Path to the image file.
            
        Returns:
            The loaded pygame Surface, or None if loading failed.
        """
        if path not in self.image_cache:
            try:
                self.image_cache[path] = pygame.image.load(path).convert_alpha()
            except Exception:
                self.image_cache[path] = None
        return self.image_cache[path]

    def push_event(self, event: pygame.event.EventType) -> None:
        """Forward a pygame event to the UI system.
        
        Args:
            event: The pygame event to process.
        """
        # called from main loop to forward pygame events
        self.event_queue.append(event)

    def _pos_from_transform(self, tx, w: int, h: int) -> tuple:
        """Calculate screen position from UI transform.
        
        Args:
            tx: The UITransform component.
            w: Width of the element in pixels.
            h: Height of the element in pixels.
            
        Returns:
            Tuple of (x, y) screen coordinates.
        """
        if tx.anchor == 'center':
            return int(tx.x - w/2), int(tx.y - h/2)
        # default to topleft
        return int(tx.x), int(tx.y)

    def process(self, dt: float) -> None:
        """Render UI elements and process UI events.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        # First handle events (mouse clicks)
        evs = self.event_queue[:]
        self.event_queue.clear()
        for event in evs:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # check buttons (entities with UITransform + UIImage + UIButton)
                for ent, (tx, imgc, btn) in esper.get_components(UITransform, UIImage, UIButton):
                    surf = self.load(imgc.image_path)
                    if surf is None:
                        continue
                    w, h = surf.get_size()
                    if imgc.scale:
                        w, h = int(imgc.scale[0]), int(imgc.scale[1])
                    px, py = self._pos_from_transform(tx, w, h)
                    rect = pygame.Rect(px, py, w, h)
                    if rect.collidepoint(mx, my):
                        try:
                            if btn.callback:
                                btn.callback()
                        except Exception:
                            pass

        # Draw image-based UI elements sorted by z
        ui_images = []
        for ent, (tx, imgc) in esper.get_components(UITransform, UIImage):
            ui_images.append((getattr(imgc, 'z', 0), ent, tx, imgc))
        ui_images.sort(key=lambda t: t[0])
        for _z, ent, tx, imgc in ui_images:
            surf = None
            if imgc.image_path:
                surf = self.load(imgc.image_path)
            if surf:
                if imgc.scale:
                    try:
                        surf = pygame.transform.scale(surf, (int(imgc.scale[0]), int(imgc.scale[1])))
                    except Exception:
                        pass
                px, py = self._pos_from_transform(tx, surf.get_width(), surf.get_height())
                try:
                    self.screen.blit(surf, (px, py))
                except Exception:
                    pass

        # Draw progress bars (sorted by z as well)
        bars = []
        for ent, (tx, pb) in esper.get_components(UITransform, UIProgressBar):
            bars.append((getattr(pb, 'z', 0), ent, tx, pb))
        bars.sort(key=lambda t: t[0])
        for _z, ent, tx, pb in bars:
            # determine ratio
            ratio = 0.0
            if pb.target_entity is not None:
                try:
                    comp = esper.component_for_entity(pb.target_entity, globals().get(pb.target_comp_name))
                    cur = getattr(comp, pb.cur_field, None)
                    mx = getattr(comp, pb.max_field, None)
                    if cur is not None and mx:
                        ratio = max(0.0, min(1.0, float(cur) / float(mx)))
                except Exception:
                    ratio = 0.0
            # draw background
            px, py = self._pos_from_transform(tx, pb.width, pb.height)
            try:
                pygame.draw.rect(self.screen, pb.bg_color, pygame.Rect(px, py, pb.width, pb.height))
                fg_w = int(pb.width * ratio)
                if fg_w > 0:
                    pygame.draw.rect(self.screen, pb.fg_color, pygame.Rect(px, py, fg_w, pb.height))
            except Exception:
                pass
        # Draw damage popups (floating text tied to entities)
        try:
            # Collect popups grouped by target so we can stack them without overlap
            popups = list(esper.get_component(DamagePopup))
            groups = {}
            for d_ent, popup in popups:
                groups.setdefault(popup.target_entity, []).append((d_ent, popup))

            screen_w, screen_h = self.screen.get_size()
            for target, items in groups.items():
                # Find corresponding health-bar UITransform/UIProgressBar if present
                tx_found = None
                pb_found = None
                for u_ent, (utx, upb) in esper.get_components(UITransform, UIProgressBar):
                    if upb.target_entity == target:
                        tx_found = utx
                        pb_found = upb
                        break

                # Precompute base positions
                if tx_found and pb_found:
                    base_x, base_y = self._pos_from_transform(tx_found, pb_found.width, pb_found.height)
                    # compute current filled width to position popup over the decreasing edge
                    try:
                        ratio = 0.0
                        comp = None
                        try:
                            comp = esper.component_for_entity(pb_found.target_entity, globals().get(pb_found.target_comp_name))
                        except Exception:
                            comp = None
                        if comp is not None:
                            cur = getattr(comp, pb_found.cur_field, None)
                            mx = getattr(comp, pb_found.max_field, None)
                            if cur is not None and mx:
                                ratio = max(0.0, min(1.0, float(cur) / float(mx)))
                        fg_w = int(pb_found.width * ratio)
                    except Exception:
                        fg_w = int(pb_found.width / 2)
                    edge_x = base_x + max(2, min(pb_found.width - 2, fg_w))
                    default_px = edge_x
                    default_py = base_y - 8
                else:
                    pos_comp = esper.try_component(target, Position)
                    if pos_comp:
                        default_px = int(pos_comp.x)
                        default_py = int(pos_comp.y - getattr(pos_comp, 'radius', 0) - 8)
                    else:
                        default_px = None
                        default_py = None

                # Render stacked popups: newest first (items list order). Use index to offset vertically
                for idx, (d_ent, popup) in enumerate(items):
                    try:
                        if default_px is None:
                            # no position info, just remove popup
                            popup.time_left = 0
                            try:
                                esper.delete_entity(d_ent)
                            except Exception:
                                pass
                            continue

                        # Compute rise offset according to popup lifetime
                        progress = 1.0 - (popup.time_left / popup.duration) if popup.duration > 0 else 1.0
                        rise = int(-20 * progress)

                        # Stacking offset (stack upwards without overlapping)
                        font_h = self.font.get_height()
                        stack_offset = idx * (font_h + 4)

                        px = default_px
                        py = default_py + rise - stack_offset

                        # If the popup would be off the top of the window, place it below the bar instead
                        if py < 4 and tx_found and pb_found:
                            py = base_y + pb_found.height + 6 + stack_offset

                        # Clamp horizontally inside screen
                        # render text (without a leading minus, show positive number)
                        txt = f"{popup.amount}" if popup.amount >= 0 else f"{popup.amount}"
                        surf = self.font.render(txt, True, popup.color)
                        try:
                            alpha = max(0, min(255, int(255 * (popup.time_left / popup.duration)))) if popup.duration > 0 else 255
                            surf.set_alpha(alpha)
                        except Exception:
                            pass
                        rect = surf.get_rect(center=(int(px), int(py)))
                        # clamp rect inside screen horizontally
                        if rect.left < 4:
                            rect.left = 4
                        if rect.right > screen_w - 4:
                            rect.right = screen_w - 4
                        self.screen.blit(surf, rect)

                        # Countdown and removal
                        popup.time_left -= dt
                        if popup.time_left <= 0:
                            try:
                                esper.delete_entity(d_ent)
                            except Exception:
                                pass
                    except Exception:
                        try:
                            popup.time_left -= dt
                            if popup.time_left <= 0:
                                esper.delete_entity(d_ent)
                        except Exception:
                            pass
        except Exception:
            pass

        # Present frame after UI rendering
        try:
            pygame.display.flip()
        except Exception:
            pass


class ManaSystem(esper.Processor):
    """Regenerate mana over time for entities with a Mana component."""
    
    def process(self, dt: float) -> None:
        """Process mana regeneration for all entities.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        for ent, mana in esper.get_component(Mana):
            mana.current_mana = min(mana.max_mana, mana.current_mana + mana.regen_rate * dt)


class SkillSystem(esper.Processor):
    """Handle skill effects and duration management."""
    
    def process(self, dt: float) -> None:
        """Process active skill effects for all entities.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        # Process active skill effects
        effects_to_remove = []
        for ent, effect in esper.get_component(SkillEffect):
            effect.time_remaining -= dt
            
            # Apply effect based on type/
            if effect.effect_type == 'damage_reduction':
                # This effect is applied during collision, just maintain it
                pass
            
            elif effect.effect_type == 'damage_boost':
                # Multiplier applied during collision
                pass
            
            elif effect.effect_type == 'heal' and effect.time_remaining < 0:
                # Apply healing (one-time at start, so only when expired)
                if esper.has_component(ent, Health):
                    health = esper.component_for_entity(ent, Health)
                    health.current_hp = min(health.max_hp, health.current_hp + int(effect.effect_value))

            # Mark for removal if expired
            if effect.time_remaining <= 0:
                effects_to_remove.append((ent, effect))
        
        # Remove expired effects
        for ent, effect in effects_to_remove:
            try:
                esper.remove_component(ent, SkillEffect)
            except Exception:
                pass