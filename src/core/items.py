from src.core.character import Character
from src.core.spells import Spell
from src.api.llm import get_llm
from src.battle.effects import Poison, Sleep, Silence
from src.game.response_manager import print_event_text
from src.api.images import generate_item_portrait
from typing import Dict, Type, List


class Item:
    def __init__(self, name: str, description: str, portrait: str = None):
        self.name = name
        self.description = description
        self.portrait = portrait

    async def use(self, target: "Character"):
        pass

    async def fancy_action_text(self, action_text):
        fancy_text = get_llm().generate_action_text(action_text)
        await print_event_text(
            f"{self.name} used!", fancy_text, portrait_image_url=self.portrait
        )


class KeyItem(Item):
    def __init__(self, item_info, portrait: str = None):
        self.name = item_info["name"]
        self.description = item_info["description"]
        super().__init__(self.name, self.description, portrait)


class Consumable(Item):
    def __init__(self, name: str, description: str, tier: int, portrait: str = None):
        super().__init__(name, description, portrait)
        self.tier = tier
        self.targets = "ally"


class SpellBook(Consumable):
    def __init__(self, spell: "Spell", tier: int = 1, portrait: str = None):
        self.spell = spell
        name = f"Spellbook ({self.spell.name})"
        description = f"A spellbook containing instructions on how to cast the {self.spell.name} spell."
        portrait = generate_item_portrait(name, description)
        super().__init__(name, description, tier, portrait)

    async def use(self, target: "Character"):
        target.spells.append(self.spell)
        action_text = f"{target.name} ({target.job_class}) learns the {self.spell.name} ({self.spell.description}) spell"
        await self.fancy_action_text(action_text)


class HealingItem(Consumable):
    def __init__(self, name: str, description: str, tier: int, portrait: str = None):
        super().__init__(name, description, tier, portrait)
        self.heal_amount = int(50 * tier)

    async def use(self, target: "Character"):
        true_heal = target.stats.hp_change(self.heal_amount)
        action_text = f"{self.name} used! {target.name} ({target.job_class}) healed for {true_heal} HP"
        await self.fancy_action_text(action_text)


class MPRestoreItem(Consumable):
    def __init__(self, name: str, description: str, tier: int, portrait: str = None):
        super().__init__(name, description, tier, portrait)
        self.restore_amount = int(25 * tier)

    async def use(self, target: "Character"):
        true_restore = target.stats.mp_change(self.restore_amount)
        action_text = f"{self.name} used! {target.name} ({target.job_class}) restored {true_restore} MP"
        await self.fancy_action_text(action_text)


class StatusRecoveryItem(Consumable):
    def __init__(
        self,
        name: str,
        description: str,
        tier: int,
        status_to_cure: List[Type],
        portrait: str = None,
    ):
        super().__init__(name, description, tier, portrait)
        self.status_to_cure = status_to_cure

    async def use(self, target: "Character"):
        cured_statuses = []
        for effect in target.status_effects[:]:
            if type(effect) in self.status_to_cure:
                target.status_effects.remove(effect)
                cured_statuses.append(effect.name)

        if cured_statuses:
            action_text = f"{self.name} used! Removed {', '.join(cured_statuses)} from {target.name} ({target.job_class})"
        else:
            action_text = f"{self.name} used! {target.name} ({target.job_class}) had no relevant status effects to remove"

        await self.fancy_action_text(action_text)


class OffensiveItem(Consumable):
    def __init__(self, name: str, description: str, tier: int, portrait: str = None):
        super().__init__(name, description, tier, portrait)
        self.damage = int(50 * tier)
        self.targets = "enemy"

    async def use(self, target: "Character"):
        true_damage = target.stats.hp_change(-self.damage)
        action_text = f"{self.name} used! {target.name} ({target.job_class}) took {true_damage} damage"
        if not target.stats.alive:
            action_text += f" and was defeated!"
        await self.fancy_action_text(action_text)


class ReviveItem(Consumable):
    def __init__(self, name: str, description: str, tier: int, portrait: str = None):
        super().__init__(name, description, tier, portrait)

    async def use(self, target: "Character"):
        if target.stats.alive:
            action_text = (
                f"{self.name} used! {target.name} ({target.job_class}) is already alive"
            )
            await self.fancy_action_text(action_text)
            return
        target.stats.alive = True
        if target.tier == 1:
            target.stats.hp = int(target.stats.max_hp * 0.25)
        elif target.tier == 2:
            target.stats.hp = int(target.stats.max_hp * 0.5)
        elif target.tier == 3:
            target.stats.hp = int(target.stats.max_hp * 0.75)
        elif target.tier == 4:
            target.stats.hp = int(target.stats.max_hp * 1.0)
        action_text = f"{self.name} used! {target.name} ({target.job_class}) revived with {target.stats.hp} HP"
        await self.fancy_action_text(action_text)


class ItemManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ItemManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):  # Ensure __init__ is only called once
            self.item_set = {}
            self.item_lookup = {}
            self.initialized = True

    def initialize(self, item_set: Dict):
        self.item_set = item_set
        self.item_lookup = {}

        for tier, items in self.item_set.items():
            tier_num = int(tier.split("_")[1])
            for item_type, item_info in items.items():
                item_name = item_info["name"]
                item_description = item_info["description"]
                item_portrait = generate_item_portrait(item_name, item_description)
                item_all = {
                    "name": item_name,
                    "description": item_description,
                    "tier": tier_num,
                    "item_type": item_type,
                    "portrait": item_portrait,
                }
                self.item_lookup[item_name] = item_all

    def create_item_class(self, name, description, item_type, tier, portrait):
        if item_type == "healing":
            return HealingItem(name, description, tier, portrait)
        elif item_type == "mp_restore":
            return MPRestoreItem(name, description, tier, portrait)
        elif item_type == "status_recovery":
            status_effects = [Poison, Sleep, Silence]
            return StatusRecoveryItem(name, description, tier, status_effects, portrait)
        elif item_type == "offensive":
            return OffensiveItem(name, description, tier, portrait)
        elif item_type == "revive":
            return ReviveItem(name, description, tier, portrait)
        else:
            raise ValueError(f"Unknown item type: {item_type}")

    def deserialize_item(self, item_name: str):
        """Deserialize an item name into an Item instance."""
        item = self.item_lookup.get(item_name)
        if item:
            return self.create_item_class(
                item["name"],
                item["description"],
                item["item_type"],
                item["tier"],
                item["portrait"],
            )
        raise ValueError(f"Unknown item: {item_name}")

    @property
    def item_list(self):
        return list(self.item_lookup.keys())

    def get_item_description(self, item_name: str) -> str:
        item = self.item_lookup.get(item_name)
        if item:
            return item["description"]
        raise ValueError(f"Unknown item: {item_name}")

    def get_item_portrait(self, item_name: str) -> str:
        item = self.item_lookup.get(item_name)
        if item:
            return item["portrait"]
        raise ValueError(f"Unknown item: {item_name}")
