# Balls?!?! The Game 🎮⚔️

A fast-paced 2D battle arena game built with Python, Pygame, and the Esper ECS (Entity Component System) framework. Two players control unique character classes with distinct abilities, weapons, and skills in intense head-to-head combat.

![Game Version](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📋 Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [How to Play](#how-to-play)
- [Game Features](#game-features)
- [Architecture](#architecture)
- [Character Classes](#character-classes)
- [Skills System](#skills-system)
- [Project Structure](#project-structure)
- [Credits](#credits)

## 🎯 Overview

Ball Game Arena is a physics-based 2D combat game where players control spherical characters in an arena. Each character has unique stats, weapons, and abilities. The game uses an Entity Component System (ECS) architecture for clean separation of data and logic, making it highly modular and extensible.

### Key Features:
- **4 Unique Character Classes**: Knight, Mage, Samurai, and Ninja
- **Skill System**: 6 different skills including damage boosts, shields, healing, and size manipulation
- **Physics-Based Combat**: Realistic collision detection and elastic bouncing
- **Orbital Weapons**: Items orbit around characters and automatically track enemies
- **Local Multiplayer**: Two players on the same keyboard
- **Customizable Loadouts**: Each player selects their class and 4 skills before battle

## 💻 Requirements

### Python Version
- **Python 3.8 or higher** (tested on Python 3.8+)

### Dependencies
- **pygame** (version 2.0.0+) - Game engine and rendering
- **esper** (version 2.0+) - Entity Component System framework

### System Requirements
- OS: Windows, macOS, or Linux
- RAM: 512 MB minimum
- Display: 960x540 minimum resolution

## 🚀 Installation

### Step 1: Clone or Download the Repository
```bash
git clone https://github.com/Gui-MB/Ball_Game.git
cd Ball_Game
```

### Step 2: Install Python Dependencies
```bash
pip install pygame esper
```

Or create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate
pip install pygame esper
```

### Step 3: Verify Assets
Ensure the following directories contain game assets:
- `images/spt_Balls/` - Character sprites
- `images/spt_Weapons/` - Weapon sprites
- `images/spt_Menu/` - Menu backgrounds and UI elements
- `sounds/` - Background music and sound effects

### Step 4: Run the Game
```bash
python main.py
```

## 🎮 How to Play

### Main Menu
- Navigate using **W/S** or **Arrow Keys**
- Press **E** or **Enter** to select
- Access **Settings** to adjust music volume and toggle fullscreen

### Character Selection
1. **Player 1 (Left)**: Use **W/S** to select class, press **E** to confirm
2. **Player 2 (Right)**: Use **Arrow Keys** to select class, press **Enter** to confirm

### Skill Selection
Each player selects 4 skills from the available pool:
- **Player 1**: Navigate with **W/S**, select with **A/D**, confirm with **E**
- **Player 2**: Navigate with **Arrow Keys**, confirm with **Enter**

### Spawn Positioning
- **Player 1**: Move with **WASD**, confirm position with **E**
- **Player 2**: Move with **Arrow Keys**, confirm position with **Enter**

### In-Game Controls

#### Player 1:
- **Movement**: Automatic (physics-based)
- **Skill 1**: W
- **Skill 2**: A
- **Skill 3**: S
- **Skill 4**: D

#### Player 2:
- **Movement**: Automatic (physics-based)
- **Skill 1**: ↑ (Up Arrow)
- **Skill 2**: ↓ (Down Arrow)
- **Skill 3**: ← (Left Arrow)
- **Skill 4**: → (Right Arrow)

### Win Condition
Reduce your opponent's health to 0 to win the match!

## ⚡ Game Features

### Combat Mechanics
- **Body Damage**: Direct collision damage (Ninja specialty)
- **Weapon Damage**: Orbital weapons deal damage on contact
- **Damage Reduction**: Shields and defensive items reduce incoming damage
- **Knockback**: Weapons push enemies away on impact
- **Spawn Protection**: Brief invulnerability after spawning
- **Damage Cooldown**: Prevents rapid consecutive damage

### Physics System
- **Elastic Collisions**: Realistic bouncing with configurable restitution
- **Mass-Based Physics**: Heavier characters push lighter ones more
- **Wall Bouncing**: Arena boundaries reflect entities
- **Velocity Preservation**: Characters maintain speed after collisions

### UI Elements
- **Health Bars**: Real-time HP display for both players
- **Mana Bars**: Track available mana for skills
- **Damage Popups**: Floating combat text shows damage dealt
- **Character Icons**: Visual indicators for each player
- **Settings Menu**: Accessible in-game via button

## 🏗️ Architecture

The game uses the **Entity Component System (ECS)** pattern via the Esper library, separating data (Components) from logic (Systems).

### Why ECS?

ECS provides several advantages:
- **Modularity**: Components are reusable pieces of data
- **Performance**: Cache-friendly data layout
- **Flexibility**: Easy to add new features without breaking existing code
- **Composition Over Inheritance**: Mix and match components for different behaviors

### Core Architecture

```
┌─────────────────┐
│    Entities     │  (IDs that group components together)
└────────┬────────┘
         │
         ├──────> ┌─────────────────┐
         │        │   Components    │  (Pure data: Position, Health, Velocity, etc.)
         │        └─────────────────┘
         │
         └──────> ┌─────────────────┐
                  │    Systems      │  (Logic: MovementSystem, CollisionSystem, etc.)
                  └─────────────────┘
```

### Main Modules

1. **main.py** (1695 lines)
   - Game loop and initialization
   - Menu systems (main, character selection, skill selection)
   - Entity creation and configuration
   - Presets for classes, items, and skills

2. **components.py** (300+ lines)
   - Component definitions (Position, Velocity, Health, etc.)
   - UI components (UITransform, UIProgressBar, etc.)
   - Skill components (Mana, Skill, SkillEffect)

3. **systems.py** (1290+ lines)
   - Movement and physics systems
   - Collision detection and resolution
   - Rendering system with sprite scaling
   - UI system with event handling
   - Skill system with effect management

## 🎭 Character Classes

### Knight 🛡️
- **HP**: 220 (Highest)
- **Mass**: 4.0 (Balanced)
- **Speed**: 600-650
- **Body Damage**: 0
- **Items**: Knight Shield (60% damage reduction), Knight Sword (5 damage)
- **Playstyle**: Tank with defensive capabilities

### Mage 🔮
- **HP**: 180 (Low)
- **Mass**: 3.0 (Light)
- **Speed**: 500-550
- **Body Damage**: 0
- **Items**: Mage Orb (8 damage, fast orbit), Mage Staff (1 damage, knockback)
- **Playstyle**: Glass cannon with ranged poke

### Samurai ⚔️
- **HP**: 150 (Lowest)
- **Mass**: 10.0 (Heaviest)
- **Speed**: 600-650
- **Body Damage**: 0
- **Items**: Katana (3 damage, extremely fast rotation)
- **Playstyle**: High-risk aggressive fighter

### Ninja 🥷
- **HP**: 180 (Balanced)
- **Mass**: 2.5 (Lightest)
- **Speed**: 700-750 (Fastest)
- **Body Damage**: 5 (Only class with body damage)
- **Items**: None
- **Playstyle**: Hit-and-run melee specialist

## ✨ Skills System

### Available Skills

1. **Shield** 🛡️
   - Mana: 3 | Cooldown: 1s
   - Reduces incoming damage by 50% for 2s

2. **Berserk** 💪
   - Mana: 4 | Cooldown: 1s
   - Increases outgoing damage by 50% for 2s

3. **Heal** 💚
   - Mana: 5 | Cooldown: 5s
   - Restores 10 HP instantly

4. **Giant** 📏
   - Mana: 4 | Cooldown: 3s
   - Increases radius by 50% for 3s

5. **Shrink** 🔬
   - Mana: 3 | Cooldown: 2.5s
   - Decreases radius by 40% for 2.5s (harder to hit)

### Mana System
- **Max Mana**: 10
- **Regen Rate**: 0.5 per second
- Skills cannot be cast without sufficient mana

## 📁 Project Structure

```
Ball_Game/
├── main.py              # Main game loop, menus, and initialization
├── components.py        # ECS component definitions
├── systems.py           # ECS system implementations
├── README.md            # This file
├── images/
│   ├── spt_Balls/       # Character sprites
│   │   ├── knight.png
│   │   ├── mage.png
│   │   ├── samurai.png
│   │   └── ninja.png
│   ├── spt_Weapons/     # Weapon sprites
│   │   ├── knight_shield.png
│   │   ├── knight_sword.png
│   │   ├── mage_orb.png
│   │   ├── mage_staff.png
│   │   └── samurai_katana.png
│   └── spt_Menu/        # Menu backgrounds and UI
│       ├── background.png
│       ├── menu_header.png
│       ├── arena_background.png
│       └── settings_button.png
└── sounds/
    └── BardsofWyverndale.mp3  # Background music
```

## 🎨 Extending the Game

### Adding a New Character Class

1. Add sprite to `images/spt_Balls/`
2. Add entry to `CLASS_PRESETS` in `main.py`:
```python
'NewClass': {
    'radius': 35,
    'color': (255, 100, 0),
    'image_path': 'images/spt_Balls/newclass.png',
    'mass': 3.5,
    'restitution': 1.0,
    'speed_range': (550, 600),
    'max_hp': 200,
    'body_damage': 0,
    'items': ['ItemName'],
    'description': 'Description of the class.'
}
```

### Adding a New Skill

Add to `SKILLS_PRESETS` in `main.py`:
```python
'SkillName': Skill(
    name='SkillName',
    mana_cost=4.0,
    cooldown=3.0,
    effect_type='new_effect',
    effect_value=1.5,
    effect_duration=2.0,
    icon_color=(255, 255, 0),
    description='What the skill does.'
)
```

Then implement the effect in `SkillSystem.process()` in `systems.py`.

### Adding a New Item/Weapon

Add to `ITEMS_PRESETS` in `main.py`:
```python
'ItemName': {
    'name': 'ItemName',
    'color': (200, 100, 50),
    'image_path': 'images/spt_Weapons/item.png',
    'damage': 5,
    'damage_reduction': 0.0,
    'orbit_radius': 80,
    'angular_speed': 120,
    'hitbox_w': 60,
    'hitbox_h': 40,
    'knockback_strength': 30.0
}
```

## 🔮 Future Enhancements

- [ ] Add more character classes (Necromancer, Archer, etc.)
- [ ] Implement special moves/ultimate abilities
- [ ] Add AI opponents for single-player
- [ ] Character customization (colors, effects)

## 👥 Credits

**Developers:**
- Dilson Simões
- Guilherme Burkert

**Music:**
- "Bards of Wyverndale" (included in sounds/)

**Libraries:**
- [Pygame](https://www.pygame.org/) - Game development library
- [Esper](https://github.com/benmoran56/esper) - Entity Component System

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

---

**Enjoy the game!** 🎮✨

For questions or support, please open an issue on GitHub.