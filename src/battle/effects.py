from __future__ import annotations
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.character import Character


class StatusEffect:
    def __init__(self, name: str, duration: int, is_detrimental: bool = True):
        self.name = name
        self.duration = duration
        self.is_detrimental = is_detrimental

    async def apply(self, character: Character):
        pass

    async def remove(self, character: Character):
        pass

    async def update(self, character: Character):
        pass


class StatModifier(StatusEffect):
    def __init__(
        self,
        name: str,
        duration: int,
        stat_modifiers: Dict[str, int],
        is_detrimental: bool = True,
    ):
        super().__init__(name, duration, is_detrimental)
        self.stat_modifiers = stat_modifiers

    async def apply(self, character: Character):
        for stat, modifier in self.stat_modifiers.items():
            current_value = getattr(character.stats, stat)
            setattr(character.stats, stat, current_value + modifier)

    async def remove(self, character: Character):
        for stat, modifier in self.stat_modifiers.items():
            current_value = getattr(character.stats, stat)
            setattr(character.stats, stat, current_value - modifier)


class Poison(StatusEffect):
    def __init__(self, duration: int, damage_per_turn: int):
        super().__init__("Poison", duration, is_detrimental=True)
        self.damage_per_turn = damage_per_turn

    async def apply(self, character: Character):
        pass

    async def update(self, character: Character):
        character.stats.hp_change(-self.damage_per_turn)

    async def remove(self, character: Character):
        return await super().remove(character)


class Silence(StatusEffect):
    def __init__(self, duration: int):
        super().__init__("Silence", duration, is_detrimental=True)

    async def apply(self, character: Character):
        character.can_cast_spells = False

    async def remove(self, character: Character):
        character.can_cast_spells = True


class Defend(StatusEffect):
    def __init__(self, duration: int, defense_bonus: int):
        super().__init__("Defend", duration, is_detrimental=False)
        self.defense_bonus = defense_bonus

    async def apply(self, character: Character):
        character.stats.defense += self.defense_bonus

    async def remove(self, character: Character):
        character.stats.defense -= self.defense_bonus
        pass


class Sleep(StatusEffect):
    def __init__(self, duration: int):
        super().__init__("Sleep", duration, is_detrimental=True)

    async def apply(self, character: Character):
        character.can_act = False

    async def remove(self, character: Character):
        character.can_act = True
        return await super().remove(character)


class RegenEffect(StatusEffect):
    def __init__(self, duration: int, heal_per_turn: int):
        super().__init__("Regen", duration, is_detrimental=False)
        self.heal_per_turn = heal_per_turn

    async def apply(self, character: Character):
        pass

    async def update(self, character: Character):
        character.stats.hp_change(self.heal_per_turn)

    async def remove(self, character: Character):
        return await super().remove(character)


class SlowEffect(StatusEffect):
    def __init__(self, duration: int):
        super().__init__("Slow", duration, is_detrimental=True)
        self.speed_modifier = 0.5  # Reduce speed by 50%

    async def apply(self, character: Character):
        character.stats.speed *= self.speed_modifier

    async def remove(self, character: Character):
        character.stats.speed /= self.speed_modifier


class HasteEffect(StatusEffect):
    def __init__(self, duration: int):
        super().__init__("Haste", duration, is_detrimental=False)
        self.speed_modifier = 1.5  # Increase speed by 50%

    async def apply(self, character: Character):
        character.stats.speed = int(self.speed_modifier * character.stats.speed)

    async def remove(self, character: Character):
        character.stats.speed = int(character.stats.speed / self.speed_modifier)


class Intimidated(StatusEffect):
    def __init__(
        self, duration: int = 1
    ):  # Long duration since it should last the whole battle
        super().__init__("Intimidated", duration, is_detrimental=True)
        self.stat_reduction = 0.9  # Reduces stats to 90% of original

    async def apply(self, character: Character):
        # Reduce all stats by 10%
        character.stats.attack = int(character.stats.attack * self.stat_reduction)
        character.stats.defense = int(character.stats.defense * self.stat_reduction)
        character.stats.intelligence = int(
            character.stats.intelligence * self.stat_reduction
        )
        character.stats.wisdom = int(character.stats.wisdom * self.stat_reduction)
        character.stats.speed = int(character.stats.speed * self.stat_reduction)
        character.stats.luck = int(character.stats.luck * self.stat_reduction)

    async def remove(self, character: Character):
        # Restore stats to original values
        character.stats.attack = int(character.stats.attack / self.stat_reduction)
        character.stats.defense = int(character.stats.defense / self.stat_reduction)
        character.stats.intelligence = int(
            character.stats.intelligence / self.stat_reduction
        )
        character.stats.wisdom = int(character.stats.wisdom / self.stat_reduction)
        character.stats.speed = int(character.stats.speed / self.stat_reduction)
        character.stats.luck = int(character.stats.luck / self.stat_reduction)
