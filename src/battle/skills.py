from __future__ import annotations
import numpy as np
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from src.game.response_manager import print_event_text
from src.utils.utils import calculate_hit_outcome
from src.api.llm import get_llm
from src.battle.elements import calculate_elemental_damage, NONE
from src.battle.effects import (
    Sleep,
    Intimidated,
    Defend,
    HasteEffect,
    RegenEffect,
    StatModifier,
    Poison,
    SlowEffect,
    Silence,
)
from src.game.response_manager import print_character_info_async
import random

if TYPE_CHECKING:
    from src.core.character import Character


class Skill(ABC):
    def __init__(
        self, name: str = "", targets: str = "", description: str = "", cost: int = 0
    ):
        self.name = name
        self.targets = targets
        self.description = description
        self.cost = cost  # SP cost, default 0 for basic skills

    async def use(self, target, user):
        if self.cost > 0:
            user.stats.sp_change(-self.cost)
        await self._use_effect(target, user)

    @abstractmethod
    async def _use_effect(self, target, user):
        pass

    async def fancy_text(
        self, action_text: str, user: Character, target: Character = None
    ):
        fancy_action_text = get_llm().generate_action_text(action_text)
        # check if target is a list, if so, use the first element
        if isinstance(target, list):
            target = target[0]
        await print_event_text(
            f"{self.name} used!",
            fancy_action_text,
            input_type="battle_message",
            portrait_image_url=user.portrait,
            npc_portrait_url=target.portrait if target else None,
        )

    def calculate_base_damage(self, user: Character, target: Character) -> int:
        damage = user.stats.attack * (user.stats.attack / target.stats.defense)
        return int(np.random.uniform(0.75, 1.25) * damage)

    async def remove_sleep(self, target: Character):
        await target.remove_status_effect(Sleep(10))


class Attack(Skill):
    def __init__(self):
        super().__init__(
            name="Attack",
            targets="enemy",
            description="A basic attack dealing physical damage to a single enemy.",
            cost=0,
        )

    async def _use_effect(self, target: Character, user: Character):
        hit, crit = calculate_hit_outcome(user.stats.luck, target.stats.luck)
        if not hit:
            action_text = f"{user.name} attacks {target.name} but misses!"
            await self.fancy_text(action_text, user, target)
            return

        damage = self.calculate_base_damage(user, target)

        weapon = user.equipment.get("weapon")
        attack_element = (
            weapon.element if weapon and weapon.element != NONE else user.element
        )

        armor = target.equipment.get("armor")
        defense_element = (
            armor.element if armor and armor.element != NONE else target.element
        )

        damage, explanation = calculate_elemental_damage(
            damage, attack_element, defense_element
        )

        if crit:
            damage *= 2
            crit_text = "Critical hit!"
        else:
            crit_text = ""

        true_damage = target.stats.hp_change(-damage)
        action_text = f"{user.name} attacks {target.name} for {abs(true_damage)} damage\n{explanation}"
        if crit_text:
            action_text += f"\n{crit_text}"

        await self.remove_sleep(target)

        if target.stats.hp == 0:
            action_text += f"\n{target.name} has been defeated!"

        await self.fancy_text(action_text, user, target)


class EnemySpecial(Skill):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            targets="enemy",
            description=f"A special enemy skill named {name}.",
            cost=0,
        )

    async def _use_effect(self, target: Character, user: Character):
        damage = self.calculate_base_damage(user, target)
        true_damage = target.stats.hp_change(-damage)
        action_text = f"{user.name} uses {self.name} on {target.name} for {abs(true_damage)} damage"

        await self.remove_sleep(target)

        if target.stats.hp == 0:
            action_text += f"\n{target.name} has been defeated!"

        await self.fancy_text(action_text, user, target)


class Inspect(Skill):
    def __init__(self):
        super().__init__(
            name="Inspect",
            targets="enemy",
            description="Allows the user to inspect an enemy and view detailed information.",
            cost=1,
        )

    async def _use_effect(self, target: Character, user: Character):
        if isinstance(target, list):
            target = target[0]
        action_text = f"{user.name} inspects {target.name}..."
        await self.fancy_text(action_text, user, target)
        await print_character_info_async(target.to_dict())


class BigSwing(Skill):
    def __init__(self):
        super().__init__(
            name="Big Swing",
            targets="enemies",
            description="A powerful attack that hits all enemies at once, dealing significant damage.",
            cost=1,
        )

    async def _use_effect(self, targets: list[Character], user: Character):
        action_text = f"{user.name} uses {self.name} ({self.description})!"
        for target in targets:
            damage = self.calculate_base_damage(user, target) * 3
            true_damage = target.stats.hp_change(-damage)
            action_text += (
                f"{user.name} attacks {target.name} for {abs(true_damage)} damage\n"
            )
            await self.remove_sleep(target)
            if target.stats.hp == 0:
                action_text += f"{target.name} has been defeated!\n"

        await self.fancy_text(action_text, user, target)


class Prayer(Skill):
    def __init__(self):
        super().__init__(
            name="Prayer",
            targets="self",
            description="A healing skill that restores HP and MP to the user based on their wisdom.",
            cost=1,
        )

    async def _use_effect(self, target: Character, user: Character):
        # Base healing scaled by wisdom
        healing = int(user.stats.wisdom * random.uniform(1.0, 2.0))
        true_hp = user.stats.hp_change(healing)
        true_mp = user.stats.mp_change(healing // 2)  # MP restoration is half of HP
        action_text = (
            f"{user.name} prays to the gods and recovers {true_hp} HP and {true_mp} MP"
        )
        await self.fancy_text(action_text, user, target)


class Steal(Skill):
    def __init__(self):
        super().__init__(
            name="Steal",
            targets="enemy",
            description="Attempts to steal an item from the target enemy. Success rate is based on the user's luck stat.",
            cost=1,
        )

    async def _use_effect(self, target: Character, user: Character):
        if isinstance(target, list):
            target = target[0]
        luck_difference = user.stats.luck - target.stats.luck
        base_rate = 0.33
        luck_rate = 0.02
        success_rate = base_rate + (max(0, luck_difference) * luck_rate)
        success_rate = max(base_rate, min(0.99, success_rate))

        if random.random() < success_rate:
            # Successfully stole an item
            if target.loot and len(target.loot) > 0:
                stolen_item = random.choice(target.loot)
                target.loot.remove(stolen_item)
                user.temp_inventory.append(stolen_item)
                action_text = f"{user.name} successfully steals {stolen_item.name} from {target.name}!"
            else:
                action_text = f"{user.name} attempts to steal from {target.name}, but they have nothing to steal!"
        else:
            action_text = (
                f"{user.name} attempts to steal from {target.name}, but fails!"
            )

        await self.fancy_text(action_text, user, target)


class DoubleCast(Skill):
    def __init__(self):
        super().__init__(
            name="Double Cast",
            targets="spell",  # Special case - will actually use the spell's targets
            description="Cast the same spell twice in succession, consuming MP for each cast.",
            cost=1,
        )

    async def _use_effect(self, spell_and_target: dict, user: Character):
        spell_name = spell_and_target["spell_name"]
        target = spell_and_target["target"]

        spell = next((s for s in user.spells if s.name == spell_name), None)
        if not spell:
            action_text = f"{user.name} tries to double cast but doesn't know the spell {spell_name}!"
            await self.fancy_text(action_text, user)
            return

        # Check if user has enough MP for both casts
        if user.stats.mp < spell.cost * 2:
            action_text = f"{user.name} tries to double cast {spell_name} but doesn't have enough MP!"
            await self.fancy_text(action_text, user)
            return

        action_text = f"{user.name} prepares to cast {spell_name} twice!"
        await self.fancy_text(action_text, user, target)

        # Cast the spell twice
        for i in range(2):
            await spell.cast(target, user)


class DefensiveShout(Skill):
    def __init__(self):
        super().__init__(
            name="Defensive Shout",
            targets="enemy",
            description="A protective shout that intimidates enemies while steeling the user's resolve.",
            cost=1,
        )

    async def _use_effect(self, target: Character, user: Character):
        if isinstance(target, list):
            target = target[0]

        await target.add_status_effect(Intimidated(3))

        await user.add_status_effect(Defend(3, defense_bonus=5))

        action_text = f"{user.name} uses {self.name} on {target.name}, intimidating them while taking a defensive stance!"
        await self.fancy_text(action_text, user, target)


class Quickstep(Skill):
    def __init__(self):
        super().__init__(
            name="Quickstep",
            targets="allies",
            description="A swift martial dance that energizes allies with supernatural speed.",
            cost=1,
        )

    async def _use_effect(self, targets: list[Character], user: Character):
        action_text = f"{user.name} performs an elegant dance!\n"

        # Apply Haste to all allies
        for ally in targets:
            await ally.add_status_effect(HasteEffect(3))
            action_text += f"{ally.name} is energized by the dance!\n"

        await self.fancy_text(action_text, user, targets[0])


class RallyingCry(Skill):
    def __init__(self):
        super().__init__(
            name="Rallying Cry",
            targets="enemies",  # Will target one enemy but buff all allies
            description="Buffs party's attack power while dealing moderate damage to one enemy.",
            cost=2,
        )

    async def _use_effect(self, target: Character, user: Character):
        if isinstance(target, list):
            target = target[0]

        # Deal damage to target
        damage = self.calculate_base_damage(user, target) * 1.2
        true_damage = target.stats.hp_change(-damage)

        # Buff all allies' attack
        action_text = f"{user.name} lets out a rallying cry!\n"
        action_text += f"{target.name} takes {abs(true_damage)} damage!\n"

        # Apply attack buff to all allies
        for ally in user.allies:
            attack_boost = StatModifier(
                "Attack Boost",
                3,
                {"attack": int(ally.stats.attack * 0.2)},
                is_detrimental=False,
            )
            await ally.add_status_effect(attack_boost)
            action_text += f"{ally.name} has their attack boosted!\n"

        await self.fancy_text(action_text, user, target)


class LastStand(Skill):
    def __init__(self):
        super().__init__(
            name="Last Stand",
            targets="enemy",
            description="A desperate attack that deals more damage the lower the user's HP.",
            cost=2,
        )

    async def _use_effect(self, target: Character, user: Character):
        if isinstance(target, list):
            target = target[0]

        # Calculate damage multiplier based on remaining HP percentage
        hp_percent = user.stats.hp / user.stats.max_hp
        damage_multiplier = 2 + (1 - hp_percent) * 3  # 2x at full HP, 5x at 1 HP

        damage = self.calculate_base_damage(user, target) * damage_multiplier
        true_damage = target.stats.hp_change(-int(damage))

        action_text = f"{user.name} makes a desperate last stand!\n"
        action_text += f"{target.name} takes {abs(true_damage)} damage!"

        await self.fancy_text(action_text, user, target)


class Stalwart(Skill):
    def __init__(self):
        super().__init__(
            name="Stalwart",
            targets="self",
            description="Grants both defensive stance and regeneration to self.",
            cost=2,
        )

    async def _use_effect(self, target: Character, user: Character):
        await user.add_status_effect(Defend(3, defense_bonus=10))
        await user.add_status_effect(RegenEffect(3, heal_per_turn=user.stats.wisdom))

        action_text = (
            f"{user.name} takes a stalwart stance, gaining defense and regeneration!"
        )
        await self.fancy_text(action_text, user, user)


class UnityStand(Skill):
    def __init__(self):
        super().__init__(
            name="Unity Stand",
            targets="allies",
            description="Grants a defense bonus to all allies.",
            cost=2,
        )

    async def _use_effect(self, targets: list[Character], user: Character):
        action_text = f"{user.name} rallies allies in a unified defense!\n"

        for ally in targets:
            defense_boost = StatModifier(
                "Defense Boost",
                3,
                {"defense": int(ally.stats.defense * 0.3)},
                is_detrimental=False,
            )
            await ally.add_status_effect(defense_boost)
            action_text += f"{ally.name} has their defense boosted!\n"

        await self.fancy_text(action_text, user, targets[0])


class SpellEcho(Skill):
    def __init__(self):
        super().__init__(
            name="Spell Echo",
            targets="spell",  # Special case like DoubleCast
            description="30% chance to automatically cast the last spell used again without MP cost.",
            cost=2,
        )

    async def _use_effect(self, spell_and_target: dict, user: Character):
        spell_name = spell_and_target["spell_name"]
        target = spell_and_target["target"]

        spell = next((s for s in user.spells if s.name == spell_name), None)
        if not spell:
            action_text = (
                f"{user.name} tries to echo but doesn't know the spell {spell_name}!"
            )
            await self.fancy_text(action_text, user)
            return

        # Cast the initial spell
        await spell.cast(target, user)

        # 30% chance to echo
        if random.random() < 0.3:
            action_text = f"{user.name} has their spell echo!"
            await self.fancy_text(action_text, user, target)
            # Cast again without MP cost
            original_cost = spell.cost
            spell.cost = 0
            await spell.cast(target, user)
            spell.cost = original_cost
        else:
            action_text = f"{user.name} has their spell fail to echo."
            await self.fancy_text(action_text, user, target)


class SpellMastery(Skill):
    def __init__(self):
        super().__init__(
            name="Spell Mastery",
            targets="self",
            description="The next spell cast will cost no MP.",
            cost=1,
        )

    async def _use_effect(self, target: Character, user: Character):
        await user.add_status_effect(
            StatModifier("Spell Mastery", 1, {}, is_detrimental=False)
        )
        user.next_spell_free = True  # Add this flag to Character class
        action_text = f"{user.name} focuses their magical energy for the next spell!"
        await self.fancy_text(action_text, user, user)


class GroupHeal(Skill):
    def __init__(self):
        super().__init__(
            name="Group Heal",
            targets="allies",
            description="Heals all allies for a moderate amount based on wisdom.",
            cost=2,
        )

    async def _use_effect(self, targets: list[Character], user: Character):
        action_text = f"{user.name} channels healing energy to the group!\n"

        # Base healing scaled by wisdom
        base_healing = int(
            user.stats.wisdom * 0.8
        )  # Slightly less than Prayer since it hits multiple targets

        for ally in targets:
            healing = int(
                base_healing * random.uniform(0.9, 1.1)
            )  # Small random variation
            true_healing = ally.stats.hp_change(healing)
            action_text += f"{ally.name} recovers {abs(true_healing)} HP!\n"

        await self.fancy_text(action_text, user, targets[0])


class Purify(Skill):
    def __init__(self):
        super().__init__(
            name="Purify",
            targets="ally",
            description="Removes negative status effects from an ally.",
            cost=1,
        )

    async def _use_effect(self, target: Character, user: Character):
        if isinstance(target, list):
            target = target[0]

        action_text = f"{user.name} attempts to purify {target.name}!\n"

        # Remove all detrimental effects
        removed_effects = []
        for effect in target.status_effects[
            :
        ]:  # Create a copy of the list to modify safely
            if effect.is_detrimental:
                await target.remove_status_effect(effect)
                removed_effects.append(effect.name)

        if removed_effects:
            action_text += f"Removed status effects: {', '.join(removed_effects)}"
        else:
            action_text += "No negative status effects to remove!"

        await self.fancy_text(action_text, user, target)


class BattleDance(Skill):
    def __init__(self):
        super().__init__(
            name="Battle Dance",
            targets="ally",
            description="Applies both Haste and an attack boost to a single ally.",
            cost=2,
        )

    async def _use_effect(self, target: Character, user: Character):
        if isinstance(target, list):
            target = target[0]

        await target.add_status_effect(HasteEffect(3))
        attack_boost = StatModifier(
            "Dance Attack Boost",
            3,
            {"attack": int(target.stats.attack * 0.15)},
            is_detrimental=False,
        )
        await target.add_status_effect(attack_boost)

        action_text = f"{user.name} performs an energizing dance for {target.name}!\n"
        action_text += f"{target.name} has their speed and attack power increased!"

        await self.fancy_text(action_text, user, target)


class Whirlwind(Skill):
    def __init__(self):
        super().__init__(
            name="Whirlwind",
            targets="enemies",
            description="Hits random enemies multiple times with quick strikes.",
            cost=2,
        )

    async def _use_effect(self, targets: list[Character], user: Character):
        action_text = f"{user.name} becomes a whirlwind of attacks!\n"

        num_hits = random.randint(3, 5)  # 3-5 random hits
        for _ in range(num_hits):
            target = random.choice(targets)
            damage = int(
                self.calculate_base_damage(user, target) * 0.5
            )  # Each hit does 50% damage
            true_damage = target.stats.hp_change(-damage)
            action_text += f"{target.name} takes {abs(true_damage)} damage!\n"

            await self.remove_sleep(target)
            if target.stats.hp == 0:
                action_text += f"{target.name} has been defeated!\n"

        await self.fancy_text(action_text, user, targets[0])


class LuckyStrike(Skill):
    def __init__(self):
        super().__init__(
            name="Lucky Strike",
            targets="enemy",
            description="High crit chance attack that might apply a random status effect.",
            cost=2,
        )

    async def _use_effect(self, target: Character, user: Character):
        if isinstance(target, list):
            target = target[0]

        # Guaranteed crit
        damage = self.calculate_base_damage(user, target) * 2
        true_damage = target.stats.hp_change(-damage)

        action_text = f"{user.name} lands a lucky strike on {target.name} for {abs(true_damage)} damage!\n"

        # 40% chance to apply a random status effect
        if random.random() < 0.4:
            possible_effects = [
                Sleep(2),
                SlowEffect(2),
                Poison(2, damage_per_turn=int(user.stats.attack * 0.2)),
                Silence(2),
            ]
            effect = random.choice(possible_effects)
            await target.add_status_effect(effect)
            action_text += f"Lucky! {target.name} is afflicted with {effect.name}!"

        await self.fancy_text(action_text, user, target)


class FortunesFavor(Skill):
    def __init__(self):
        super().__init__(
            name="Fortune's Favor",
            targets="allies",
            description="Temporarily increases party's luck.",
            cost=2,
        )

    async def _use_effect(self, targets: list[Character], user: Character):
        action_text = f"{user.name} calls upon Lady Luck!\n"

        for ally in targets:
            luck_boost = StatModifier(
                "Luck Boost",
                3,
                {"luck": int(ally.stats.luck * 0.3)},  # 30% luck increase
                is_detrimental=False,
            )
            await ally.add_status_effect(luck_boost)
            action_text += f"{ally.name} has their luck increased!\n"

        await self.fancy_text(action_text, user, targets[0])


# Final skill_map update with all skills
skill_map = {
    "Brave (Strength)": [BigSwing, RallyingCry, LastStand],
    "Loyal (Defense)": [DefensiveShout, Stalwart, UnityStand],
    "Clever (Intelligence)": [DoubleCast, SpellEcho, SpellMastery],
    "Kind (Wisdom)": [Prayer, GroupHeal, Purify],
    "Energetic (Speed)": [Quickstep, BattleDance, Whirlwind],
    "Carefree (Luck)": [Steal, LuckyStrike, FortunesFavor],
}


class Requiem(Skill):
    def __init__(self):
        super().__init__(
            name="Requiem",
            targets="enemies",
            description="An ultimate skill that hits all enemies at once, dealing significant damage which none can survive.",
            cost=0,
        )

    async def _use_effect(self, targets: list[Character], user: Character):
        action_text = f"{user.name} uses {self.name} ({self.description})!"
        for target in targets:
            damage = self.calculate_base_damage(user, target) * 1000
            true_damage = target.stats.hp_change(-damage)
            action_text += (
                f"{user.name} attacks {target.name} for {abs(true_damage)} damage\n"
            )
            await self.remove_sleep(target)
            if target.stats.hp == 0:
                action_text += f"{target.name} has been defeated!\n"

        await self.fancy_text(action_text, user, target)
