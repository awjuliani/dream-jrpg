from __future__ import annotations
from typing import List, Type, Dict, TYPE_CHECKING
from src.battle.effects import (
    Sleep,
    StatusEffect,
)
import numpy as np
from src.api.llm import get_llm
from src.battle.elements import calculate_elemental_damage
from src.game.response_manager import print_event_text

if TYPE_CHECKING:
    from src.core.character import Character


class Spell:
    def __init__(self, name: str, description: str, cost: int, targets: str):
        self.name = name
        self.description = description
        self.cost = cost
        self.targets = targets

    async def cast(self, target: Character | List[Character], caster: Character):
        if not caster.next_spell_free:
            caster.stats.mp_change(-self.cost)
        else:
            caster.next_spell_free = False

        await self._cast_effect(target, caster)

    async def _cast_effect(
        self, target: Character | List[Character], caster: Character
    ) -> str:
        raise NotImplementedError

    async def fancy_text(
        self, action_text, caster: Character, target: Character = None
    ):
        fancy_action_text = get_llm().generate_action_text(action_text)
        await print_event_text(
            f"{self.name} cast!",
            fancy_action_text,
            portrait_image_url=caster.portrait,
            npc_portrait_url=target.portrait,
            input_type="battle_message",
        )


class ElementalSpell(Spell):
    def __init__(
        self,
        name: str,
        description: str,
        cost: int,
        targets: str,
        element: str,
        base_damage: int,
    ):
        super().__init__(name, description, cost, targets)
        self.element = element
        self.base_damage = base_damage

    def calculate_damage(self, caster: Character, target: Character):
        damage = self.base_damage * (caster.stats.intelligence / target.stats.wisdom)
        damage = int(np.random.uniform(0.75, 1.25) * damage)
        damage, explanation = calculate_elemental_damage(
            damage, self.element, target.get_defense_element()
        )
        true_damage = target.stats.hp_change(-damage)
        return true_damage, explanation

    async def _cast_effect(
        self, target: Character | List[Character], caster: Character
    ) -> str:
        targets = [target] if not isinstance(target, list) else target
        action_text = f"{caster.name} cast {self.name} ({self.description})!"

        for target in targets:
            if target.stats.alive:
                true_damage, explanation = self.calculate_damage(caster, target)
                action_text += explanation
                action_text += f" {target.name} took {abs(true_damage)} ({self.element}) damage from {self.name}"
                await target.remove_status_effect(Sleep(1))
                if target.stats.hp == 0:
                    action_text += f" and was defeated!"
                action_text += "\n"

        await self.fancy_text(action_text.strip(), caster, target)


class HealingSpell(Spell):
    def __init__(
        self,
        name: str,
        description: str,
        cost: int,
        targets: str,
        heal_amount: int,
        revive: bool = False,
    ):
        super().__init__(name, description, cost, targets)
        self.heal_amount = heal_amount
        self.revive = revive

    async def _cast_effect(
        self, target: Character | List[Character], caster: Character
    ) -> str:
        targets = [target] if not isinstance(target, list) else target
        action_text = f"{caster.name} cast {self.name}!"

        for target in targets:
            if target.stats.hp == 0:
                if self.revive:
                    target.stats.hp = 1
                    action_text += f" {target.name} was revived with 1 HP."
                else:
                    action_text += f" {target.name} is dead and cannot be healed."
            else:
                true_heal = target.stats.hp_change(self.heal_amount)
                action_text += f" {target.name} healed for {abs(true_heal)} HP."

        await self.fancy_text(action_text.strip(), caster, target)


class StatusEffectSpell(Spell):
    def __init__(
        self,
        name: str,
        description: str,
        cost: int,
        status_effects: List[StatusEffect],
        targets: str = "enemy",
    ):
        super().__init__(name, description, cost, targets)
        self.status_effects = status_effects

    async def _cast_effect(
        self, target: Character | List[Character], caster: Character
    ) -> str:
        targets = [target] if not isinstance(target, list) else target
        action_text = f"{caster.name} cast {self.name}!"

        for target in targets:
            for effect in self.status_effects:
                await target.add_status_effect(effect)
                action_text += f" {target.name} is now affected by {effect.name}."

        await self.fancy_text(action_text.strip(), caster, target)


class SpellManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SpellManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.spell_set = None
            self.spell_lookup = {}
            self.initialized = True

    def initialize(self, spell_set: Dict):
        self.spell_set = spell_set
        self.spell_lookup = {}

        for tier, spells in self.spell_set.items():
            tier_num = int(tier.split("_")[1])
            for spell_type, spell_list in spells.items():
                for spell in spell_list:
                    spell_name = spell["name"]
                    spell_description = spell["description"]
                    spell_all = {
                        "name": spell_name,
                        "description": spell_description,
                        "tier": tier_num,
                        "spell_type": spell_type,
                        "element": spell.get("element"),
                        "effect": spell.get("effect"),
                    }
                    self.spell_lookup[spell_name] = spell_all

    def create_spell_class(
        self,
        name,
        description,
        spell_type,
        tier,
        element=None,
        effect=None,
        revives=False,
    ):
        base_damage = 50 * tier
        base_cost = 30 * tier

        # Determine targets based on tier and spell category
        is_offensive = spell_type in ("elemental", "status")
        targets = (
            "enemies"
            if tier > 2
            else "enemy" if is_offensive else "allies" if tier > 2 else "ally"
        )

        # Create spell based on type
        spell_factories = {
            "elemental": lambda: ElementalSpell(
                name, description, base_cost, targets, element, base_damage
            ),
            "status": lambda: StatusEffectSpell(
                name, description, base_cost, [StatusEffect(effect, 5)], targets
            ),
            "healing": lambda: HealingSpell(
                name, description, base_cost, targets, base_damage, revive=revives
            ),
            "buff": lambda: StatusEffectSpell(
                name, description, base_cost, [StatusEffect(effect, 5)], targets
            ),
        }

        if spell_type not in spell_factories:
            raise ValueError(f"Unknown spell type: {spell_type}")

        return spell_factories[spell_type]()

    def deserialize_spell(self, spell_name: str) -> Type[Spell]:
        """Deserialize a spell name into a Spell instance."""
        spell = self.spell_lookup.get(spell_name)
        if spell:
            return self.create_spell_class(
                spell["name"],
                spell["description"],
                spell["spell_type"],
                spell["tier"],
                element=spell.get("element"),
                effect=spell.get("effect"),
                revives=spell.get("revives"),
            )
        raise ValueError(f"Unknown spell: {spell_name}")

    @property
    def spell_list(self):
        return list(self.spell_lookup.keys())

    def get_spells_by_tier(self, tier: int):
        return [
            spell
            for spell in self.spell_list
            if self.spell_lookup[spell]["tier"] == tier
        ]

    @property
    def spell_categories(self):
        return {
            "elemental": ElementalSpell,
            "status": StatusEffectSpell,
            "healing": HealingSpell,
            "buff": StatusEffectSpell,
        }

    def get_spell_description(self, spell_name: str) -> str:
        spell = self.spell_lookup.get(spell_name)
        if spell:
            return spell["description"]
        raise ValueError(f"Unknown spell: {spell_name}")


spell_map = {
    "Brave (Strength)": ["elemental"],
    "Loyal (Defense)": ["healing"],
    "Clever (Intelligence)": ["elemental", "status"],
    "Kind (Wisdom)": ["healing", "buff"],
    "Energetic (Speed)": ["status"],
    "Carefree (Luck)": ["buff"],
}
