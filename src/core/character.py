from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional, Dict
from src.battle.skills import Attack
from src.battle.elements import *
from src.core.equipment import (
    Weapon,
    Accessory,
    Armor,
    Equipment,
    make_weapon,
    make_armor,
    make_accessory,
)
from src.battle.stats import CharacterStats, generate_stats, calculate_xp_for_level
from src.api.llm import get_llm
from src.game.response_manager import print_event_text
from src.api.images import generate_npc_portrait
import random
from src.core.spells import SpellManager, spell_map
from src.battle.skills import (
    Inspect,
    skill_map,
    Requiem,
)
from src.utils.utils import load_config

if TYPE_CHECKING:
    from src.battle.effects import StatusEffect
    from src.core.spells import Spell
    from src.battle.skills import Skill


class Character:
    def __init__(
        self,
        name: str,
        description: str = None,
        job_class: str = None,
        level: int = 1,
        appearance: str = None,
        element: Element = NONE,
        portrait: str = None,
    ):
        self.name = name
        self.job_class = job_class
        self.level = level
        self.spells: List[Spell] = []
        self.attack_skill = Attack()
        self.skills: List[Skill] = []
        self.stat_biases = get_llm().generate_stats(job_class=job_class)
        self.stats = CharacterStats(**generate_stats(self.stat_biases, self.level))
        self.reset_sp()
        self.stats.on_death = self.on_death  # Set the on_death callback
        self.description = description
        self.status_effects: List[StatusEffect] = []
        self.can_cast_spells = True
        self.can_act = True
        self.active_turn = False
        self.element = element
        self.equipment: Dict[str, Optional[Equipment]] = {
            "weapon": None,
            "armor": None,
            "accessory": None,
        }
        if portrait is None:
            if appearance:
                appearance_text = appearance
            else:
                appearance_text = description
            self.portrait = generate_npc_portrait(
                self.name, appearance_text, self.job_class
            )
        else:
            self.portrait = portrait
        self.next_spell_free = False

    async def attack(self, target):
        await self.attack_skill.use(target, self)

    def __str__(self):
        status_effects = ", ".join([effect.name for effect in self.status_effects])
        return f"{self.name:30} {self.stats.hp:4}/{self.stats.max_hp:4} HP, {self.stats.mp:4}/{self.stats.max_mp:4} MP, {self.dead_status()}{status_effects}"

    def to_dict(self):
        char_dict = {
            "name": self.name,
            "description": self.description,
            "job_class": self.job_class,
            "level": self.level,
            "stats": self.stats.to_dict(),
            "status_effects": [effect.name for effect in self.status_effects],
            "portrait": self.portrait,
            "spells": [spell.name for spell in self.spells],
            "skills": [skill.name for skill in self.skills],
            "equipment": {
                slot: item.name if item else None
                for slot, item in self.equipment.items()
            },
            "element": self.element.name if self.element != NONE else "NONE",
            "active_turn": self.active_turn,
            "next_spell_free": self.next_spell_free,
            "sp": f"{self.stats.sp}/{self.stats.max_sp} SP",
        }
        return char_dict

    def dead_status(self):
        if self.stats.hp <= 0:
            return "Dead "
        return ""

    def on_death(self):
        self.remove_all_status_effects()

    def remove_all_status_effects(self):
        self.status_effects = []

    def get_details_text(self):
        details = f"Level {self.level} {self.job_class}\n\n"
        details += f"{self.description}\n\n"
        details += f"{self.stats}\n"
        if self.status_effects:
            details += "Status Effects:\n"
            for effect in self.status_effects:
                details += f"- {effect.name} ({effect.duration} turns remaining)\n"
        if self.element != NONE:
            details += f"Elemental affinity: {self.element.name}\n"
        return details

    async def equip(self, item: Equipment):
        slot = self._get_equipment_slot(item)
        if slot:
            if self.equipment[slot]:
                self.equipment[slot].remove(self)
            self.equipment[slot] = item
            await item.apply(self)
        else:
            await print_event_text(f"Cannot equip {item.name}. Unknown equipment type.")

    async def unequip(self, slot: str):
        if slot in self.equipment and self.equipment[slot]:
            item = self.equipment[slot]
            item.remove(self)
            await print_event_text(f"{self.name} unequipped {item.name}.")
            self.equipment[slot] = None
        else:
            await print_event_text(f"No {slot} equipped.")

    def get_attack_element(self):
        weapon = self.equipment.get("weapon")
        return weapon.element if weapon and weapon.element != NONE else self.element

    def get_defense_element(self):
        armor = self.equipment.get("armor")
        return armor.element if armor and armor.element != NONE else self.element

    @staticmethod
    def _get_equipment_slot(item: Equipment) -> Optional[str]:
        if isinstance(item, Weapon):
            return "weapon"
        elif isinstance(item, Armor):
            return "armor"
        elif isinstance(item, Accessory):
            return "accessory"
        return None

    async def add_status_effect(self, effect: StatusEffect):
        # Check if the character already has the status effect
        for existing_effect in self.status_effects:
            if existing_effect.name == effect.name:
                existing_effect.duration = effect.duration
                return
        self.status_effects.append(effect)
        await effect.apply(self)

    async def remove_status_effect(self, effect: StatusEffect):
        for existing_effect in self.status_effects:
            if existing_effect.name == effect.name:
                await existing_effect.remove(self)
                self.status_effects.remove(existing_effect)
                return

    async def update_status_effects(self):
        for effect in self.status_effects[:]:
            await effect.update(self)
            effect.duration -= 1
            if effect.duration <= 0:
                await self.remove_status_effect(effect)

    def reset_sp(self):
        """Reset SP to 0 at the start/end of battle"""
        self.stats.sp = 0
        self.next_spell_free = False


class PlayerCharacter(Character):
    def __init__(
        self,
        name: str,
        description: str = None,
        job_class: str = None,
        level: int = 1,
        appearance: str = None,
        base_class: str = None,
        portrait: str = None,
    ):
        super().__init__(
            name,
            description,
            job_class,
            level,
            appearance=appearance,
            portrait=portrait,
        )
        self.experience = 0
        self.exp_goal = calculate_xp_for_level(self.level + 1)
        self.temp_inventory = []
        self.base_class = base_class
        self.assign_starter_skills()
        self.spells = get_starter_spells(initial_tier=1, base_class=self.base_class)

    async def gain_xp(self, xp: int):
        self.experience += xp
        while self.experience >= self.exp_goal:
            remaining_xp = self.experience - self.exp_goal
            await self.level_up()
            self.exp_goal = calculate_xp_for_level(self.level + 1)
            self.experience = remaining_xp

    async def level_up(self):
        self.level += 1
        # Store old stats for comparison
        old_stats = {
            "max_hp": self.stats.max_hp,
            "max_mp": self.stats.max_mp,
            "attack": self.stats.attack,
            "defense": self.stats.defense,
            "intelligence": self.stats.intelligence,
            "wisdom": self.stats.wisdom,
            "speed": self.stats.speed,
            "luck": self.stats.luck,
        }

        new_stats = generate_stats(self.stat_biases, self.level)
        for stat, value in new_stats.items():
            setattr(self.stats, stat, value)
        self.stats.hp = self.stats.max_hp
        self.stats.mp = self.stats.max_mp

        # Generate stat difference string
        stat_changes = []
        for stat, old_value in old_stats.items():
            new_value = getattr(self.stats, stat)
            diff = new_value - old_value
            if diff > 0:
                stat_changes.append(
                    f"{stat.replace('_', ' ').title()}: {old_value} → {new_value} (+{diff})"
                )

        level_up_text = (
            f"Level up! {self.name} ({self.job_class}) is now level {self.level}!\n"
            f"\nStat Changes:\n" + "\n".join(stat_changes)
        )

        if self.level == 20:
            self.skills.append(skill_map[self.base_class][1]())
        elif self.level == 40:
            self.skills.append(skill_map[self.base_class][2]())

        await print_event_text(
            "Level Up!",
            level_up_text,
            input_type="message",
            portrait_image_url=self.portrait,
        )

    def to_dict(self):
        char_dict = super().to_dict()
        char_dict.update(
            {
                "experience": self.experience,
                "exp_goal": self.exp_goal,
            }
        )
        return char_dict

    @classmethod
    def from_dict(cls, char_dict):
        character = super().from_dict(char_dict)
        character.experience = char_dict["experience"]
        character.exp_goal = char_dict["exp_goal"]
        return character

    def get_details_text(self):
        details = super().get_details_text()
        details += f"Experience: {self.experience}/{self.exp_goal}\n"
        return details

    def basic_info(self):
        return {
            "name": self.name,
            "description": self.description,
            "job_class": self.job_class,
            "level": self.level,
            "type": "player",
        }

    def assign_starter_skills(self):
        config = load_config()
        self.skills = [Inspect()]

        # Only add Requiem if cheat_mode is enabled
        if config.get("cheat_mode", False):
            self.skills.append(Requiem())

        self.skills.append(skill_map[self.base_class][0]())
        if self.level > 19:
            self.skills.append(skill_map[self.base_class][1]())
        if self.level > 39:
            self.skills.append(skill_map[self.base_class][2]())


async def equip_starter_gear(character, hometown, story_level=1):
    await character.equip(make_weapon(character.job_class, story_level, hometown))
    await character.equip(make_armor(character.job_class, story_level, hometown))
    await character.equip(make_accessory(character.job_class, story_level, hometown))
    character.stats.hp = character.stats.max_hp
    character.stats.mp = character.stats.max_mp


def get_starter_spells(initial_tier=1, base_class=None):
    spell_manager = SpellManager()
    starter_spells = []

    valid_categories = spell_map[base_class]

    # Retrieve all tier 1 spells
    tier_1_spells = spell_manager.get_spells_by_tier(initial_tier)

    for category in spell_manager.spell_categories.keys():
        # Filter spells by category and select a random one if available
        category_spells = [
            spell_name
            for spell_name in tier_1_spells
            if spell_manager.spell_lookup[spell_name]["spell_type"] == category
            and category in valid_categories
        ]
        if category_spells:
            starter_spells.append(
                spell_manager.deserialize_spell(random.choice(category_spells))
            )

    return starter_spells
