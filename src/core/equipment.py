from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, TYPE_CHECKING
from src.battle.effects import StatusEffect
from src.battle.elements import Element, NONE
from src.battle.elements import ELEMENT_LIST, deserialize_element
from src.api.llm import get_llm
from src.api.images import generate_item_portrait
import math

if TYPE_CHECKING:
    from src.core.character import Character

BASE_EQUIPMENT_STATS = {
    "max_hp": 10,
    "max_mp": 5,
    "attack": 2,
    "defense": 2,
    "intelligence": 2,
    "wisdom": 2,
    "speed": 2,
    "luck": 2,
}

BIAS_MULTIPLIERS = [0.5, 0.75, 1.0, 1.25, 1.5]


def calculate_equipment_stat(base: int, bias: int, level: int) -> int:
    bias_multiplier = BIAS_MULTIPLIERS[bias]
    return int(base * bias_multiplier * math.sqrt(level))


def generate_equipment_stats(biases: Dict[str, int], level: int) -> Dict[str, int]:
    return {
        stat: calculate_equipment_stat(BASE_EQUIPMENT_STATS[stat], bias, level)
        for stat, bias in biases.items()
    }


@dataclass
class Equipment:
    name: str
    description: str
    stat_modifiers: dict
    status_effects: Optional[List[StatusEffect]] = None
    element: Element = NONE
    portrait: str = None

    async def apply(self, character: Character):
        for stat, value in self.stat_modifiers.items():
            current_value = getattr(character.stats, stat)
            setattr(character.stats, stat, current_value + value)

        if self.status_effects:
            for effect in self.status_effects:
                await character.add_status_effect(effect)

    async def remove(self, character: Character):
        for stat, value in self.stat_modifiers.items():
            current_value = getattr(character.stats, stat)
            setattr(character.stats, stat, current_value - value)

        if self.status_effects:
            for effect in self.status_effects:
                await character.remove_status_effect(effect)


class Weapon(Equipment):
    pass


class Armor(Equipment):
    pass


class Accessory(Equipment):
    pass


def make_equipment(equipment_type: str, job_class: str, level: int, location=None):
    equipment_info = get_llm().generate_equipment(
        equipment_type=equipment_type,
        level=level,
        job_class=job_class,
        elements=ELEMENT_LIST,
        location=location,
    )

    stat_biases = equipment_info["stat_biases"]
    stat_modifiers = generate_equipment_stats(stat_biases, level)

    equipment_class = {"weapon": Weapon, "armor": Armor, "accessory": Accessory}[
        equipment_type.lower()
    ]

    return equipment_class(
        name=equipment_info["name"],
        description=equipment_info["description"],
        stat_modifiers=stat_modifiers,
        element=deserialize_element(equipment_info["element"]),
        portrait=generate_item_portrait(
            equipment_info["name"], equipment_info["description"]
        ),
    )


def make_weapon(job_class, level, location=None):
    return make_equipment("weapon", job_class, level, location)


def make_armor(job_class, level, location=None):
    return make_equipment("armor", job_class, level, location)


def make_accessory(job_class, level, location=None):
    return make_equipment("accessory", job_class, level, location)
