from __future__ import annotations
from src.core.character import (
    PlayerCharacter,
)
from src.core.equipment import (
    Equipment,
    Weapon,
)
from src.battle.skills import *
from src.core import items
from src.core.items import ItemManager
from src.game.response_manager import (
    choose_option,
    print_character_info_async,
    print_event_text,
)
from src.game.response_manager import (
    print_character_info_async,
)
from src.core.story import StoryManager, StoryEvent
from src.core.cutscene import cutscene
from src.core.party import Party
from typing import List, TYPE_CHECKING
import random
from src.utils.utils import load_config

if TYPE_CHECKING:
    from src.travel.base_location import Location


class PlayerParty(Party):
    def __init__(
        self,
        characters: list[PlayerCharacter],
        inventory: List[items.Item] = [],
        equipment_inventory: List[items.Item] = [],
        key_items: List[items.Item] = [],
        currency=0,
        thematic_style=None,
        currency_name="Gold",
        main_party_limit=3,
    ):
        super().__init__(characters[:main_party_limit], inventory)
        self.backup_characters = characters[main_party_limit:]
        self.equipment_inventory = equipment_inventory
        self.key_items = key_items
        self.currency = currency
        self.main_party_limit = main_party_limit
        self.story_manager = StoryManager(thematic_style, currency_name)

    def to_dict(self):
        return {
            "characters": self.characters_to_dict(),
            "inventory": [item.name for item in self.inventory],
            "equipment_inventory": [item.name for item in self.equipment_inventory],
            "key_items": [item.name for item in self.key_items],
            "currency": self.currency,
        }

    @property
    def leader(self):
        return self.characters[0]

    async def party_menu(self, location: Location):
        options = [
            "Check inventory",
            "Party member status",
            "Party conversation",
            "Story so far",
        ]
        if len(self.characters) > self.main_party_limit:
            options.append("Manage party composition")
        sub_text = f"Your party currently consists of: {', '.join(self.list_names)}. \n\nYou have {self.currency} {self.story_manager.currency_name}."
        while True:
            choice = await choose_option(
                options,
                prompt="Party Menu",
                sub_text=sub_text,
            )

            if choice == "Check inventory":
                await self.check_inventory()
            elif choice == "Party member status":
                await self.show_party_status()
            elif choice == "Manage party composition":
                await self.manage_party_composition()
            elif choice == "Party conversation":
                await self.party_conversation(location)
            elif choice == "Story so far":
                await self.story_manager.get_story_so_far()
            elif choice is None:
                break

    async def manage_party_composition(self):
        options = ["Move to main party", "Move to backup"]
        choice = await choose_option(
            options,
            prompt="Manage Party Composition",
            sub_text=self._get_party_composition_text(),
        )

        if choice == "Move to main party":
            await self.move_to_main_party()
        elif choice == "Move to backup":
            await self.move_to_backup()

    def _get_party_composition_text(self):
        text = f"Main Party ({len(self.characters)}/{self.main_party_limit}):\n"
        text += "\n".join(
            [f"{i+1}. {character.name}" for i, character in enumerate(self.characters)]
        )
        text += "\n\nBackup Characters:\n"
        if len(self.backup_characters) == 0:
            text += "No backup characters available"
        else:
            text += "\n".join(
                [
                    f"{i+1}. {character.name}"
                    for i, character in enumerate(self.backup_characters)
                ]
            )
        return text

    async def move_to_main_party(self):
        if not self.backup_characters:
            await print_event_text("No backup characters available", "")
            return

        # Choose character from backup to add
        character = await self.choose_target(
            self.backup_characters,
            prompt="Choose a character to move to the main party...",
            portraits=[char.portrait for char in self.backup_characters],
        )
        if not character:
            return

        # If party is full, ask to replace someone
        if len(self.characters) >= self.main_party_limit:
            await print_event_text(
                f"Main party is full (Limit: {self.main_party_limit}). Choose a character to replace:",
                "",
            )
            replace_char = await self.choose_target(
                self.characters,
                prompt="Choose a character to move to backup...",
                portraits=[char.portrait for char in self.characters],
            )
            if not replace_char:
                return

            self.characters.remove(replace_char)
            self.backup_characters.append(replace_char)
            await print_event_text(f"{replace_char.name} moved to backup", "")

        # Add the new character to main party
        self.backup_characters.remove(character)
        self.characters.append(character)
        await print_event_text(f"{character.name} moved to the main party", "")

    async def move_to_backup(self):
        if len(self.characters) <= 1:
            await print_event_text(
                "Cannot remove the last character from the main party", ""
            )
            return

        character = await self.choose_target(
            self.characters,
            prompt="Choose a character to move to backup...",
            portraits=[char.portrait for char in self.characters],
        )
        if character:
            self.characters.remove(character)
            self.backup_characters.append(character)
            await print_event_text(f"{character.name} moved to backup", "")

    async def show_party_status(self):
        all_characters = self.characters + self.backup_characters
        options = [character.name for character in all_characters]
        option_details = [character.description for character in all_characters]

        while True:
            choice = await choose_option(
                options,
                option_details=option_details,
                prompt="Party Status",
                sub_text="Choose a character to view their details...",
                option_portraits=[character.portrait for character in all_characters],
            )

            if choice is None:
                break

            selected_character = next(
                char for char in all_characters if char.name == choice
            )

            # Show character info and equipment options
            while True:
                equipment_text = "\n\nCurrent Equipment:\n"
                for slot, item in selected_character.equipment.items():
                    equipment_text += (
                        f"{slot.capitalize()}: {item.name if item else 'Empty'}\n"
                    )

                char_options = ["View Stats", "Equip Item", "Unequip Item"]
                char_choice = await choose_option(
                    char_options,
                    prompt=f"{selected_character.name}'s Status",
                    sub_text=selected_character.description,
                    portrait_image_url=selected_character.portrait,
                )

                if char_choice == "View Stats":
                    await print_character_info_async(selected_character.to_dict())
                elif char_choice == "Equip Item":
                    await self._equip_item_for_character(selected_character)
                elif char_choice == "Unequip Item":
                    await self._unequip_item_for_character(selected_character)
                elif char_choice is None:
                    break

    async def _equip_item_for_character(self, character):
        if not self.equipment_inventory:
            await print_event_text("No equipment available to equip.", "")
            return

        options = [
            f"{item.name} ({type(item).__name__})" for item in self.equipment_inventory
        ]
        item_choice = await choose_option(
            options,
            prompt=f"Choose an item to equip to {character.name}...",
            allow_exit=True,
            option_portraits=[item.portrait for item in self.equipment_inventory],
            option_details=[item.description for item in self.equipment_inventory],
        )

        if item_choice is None:
            return

        item = next(
            item
            for item in self.equipment_inventory
            if f"{item.name} ({type(item).__name__})" == item_choice
        )

        character.equip(item)
        self.equipment_inventory.remove(item)
        await print_event_text(f"Equipped {item.name} to {character.name}", "")

    async def _unequip_item_for_character(self, character):
        options = [
            f"{slot.capitalize()}: {item.name}"
            for slot, item in character.equipment.items()
            if item is not None
        ]
        option_portraits = [
            character.equipment[slot].portrait
            for slot, item in character.equipment.items()
            if item is not None
        ]
        option_details = [
            f"{item.description}"
            for slot, item in character.equipment.items()
            if item is not None
        ]

        if not options:
            await print_event_text("No equipment to unequip.", "")
            return

        choice = await choose_option(
            options,
            prompt=f"Unequip from {character.name}...",
            allow_exit=True,
            option_portraits=option_portraits,
            option_details=option_details,
        )

        if choice is not None:
            slot = choice.split(":")[0].lower()
            item = character.equipment[slot]
            character.unequip(slot)
            self.equipment_inventory.append(item)
            await print_event_text(f"Unequipped {item.name} from {character.name}", "")

    async def check_inventory(self):
        while True:
            options = ["Consumables", "Equipment", "Key Items"]
            choice = await choose_option(options, prompt="Inventory Management")

            if choice == "Consumables":
                await self._use_item()
            elif choice == "Equipment":
                await self.view_equipment_inventory()
            elif choice == "Key Items":
                await self.view_key_items()
            elif choice is None:
                break

    async def _use_item(self):
        if len(self.inventory) == 0:
            await print_event_text("No items to use", "")
            return None

        options = [item.name for item in self.inventory]
        option_details = [item.description for item in self.inventory]
        item_name = await choose_option(
            options,
            option_details=option_details,
            prompt="Choose an item...",
            allow_exit=True,
            option_portraits=[item.portrait for item in self.inventory],
        )

        if item_name is None:
            return None

        item = next(item for item in self.inventory if item.name == item_name)

        if item.targets == "ally":
            target = await self.choose_target(self.characters)
        else:
            await print_event_text("No enemies to target...", "")
            return None

        if target:
            await item.use(target)
            self.inventory.remove(item)
        return item

    async def view_equipment_inventory(self):
        if not self.equipment_inventory:
            text = "No equipment in inventory."
        else:
            text = "Equipment Inventory:\n\n"
            for item in self.equipment_inventory:
                text += f"{item.name} ({type(item).__name__})\n"
                text += f"  Description: {item.description}\n"
                text += f"  Stat Modifiers: {item.stat_modifiers}\n"
                if isinstance(item, Weapon) and item.element:
                    text += f"  Element: {item.element.name}\n"
                text += "\n"

        await print_event_text("Equipment Inventory", text)

    async def view_key_items(self):
        if not self.key_items:
            text = "No key items in inventory."
        else:
            text = "Key Items:\n\n"
            for item in self.key_items:
                text += f"{item.name}\n"
                text += f"  Description: {item.description}\n\n"

        await print_event_text("Key Items", text)

    async def choose_target(self, targets, prompt="Choose a target...", portraits=None):
        options = [character.name for character in targets]
        choice = await choose_option(
            options,
            prompt=prompt,
            allow_exit=True,
            option_portraits=portraits if portraits else None,
            option_details=[character.description for character in targets],
        )

        if choice is None:
            return None
        return next(character for character in targets if character.name == choice)

    def add_character(self, new_character: PlayerCharacter):
        if len(self.characters) < self.main_party_limit:
            self.characters.append(new_character)
        else:
            self.backup_characters.append(new_character)

    async def add_equipment(self, equipment: Equipment):
        self.equipment_inventory.append(equipment)
        await print_event_text(
            f"Added {equipment.name} to the equipment inventory.", ""
        )

    async def party_conversation(self, location: Location):
        """Allow party members to have a casual conversation with each other"""
        # Get names of all party members
        scene_npcs = [f"{char.name} ({char.description})" for char in self.characters]

        # Generate and display a casual conversation between party members
        await cutscene(
            StoryEvent(
                location=location.name,
                event_text=f"The party members take a moment to chat with each other. They discuss the current objective, which is {self.story_manager.next_event.trigger_hint}",
                trigger={"type": "none", "value": "none"},
                completed=True,
            ),
            location.name,
            "A quiet moment for conversation",
            scene_npcs,
            past_events=self.story_manager.past_events,
            thematic_style=self.story_manager.thematic_style,
            conversation_length="short",
        )


async def initialize_party(
    hero,
    initial_level=1,
    initial_tier=1,
    thematic_style=None,
    currency_name="Gold",
    initial_class=None,
    starting_currency=500,
):
    config = load_config()
    cheat_mode = config.get("cheat_mode", False)
    if cheat_mode:
        initial_level = 99

    hero_character = PlayerCharacter(
        name=hero["full_name"],
        description=hero["short_description"],
        job_class=hero["job_class"],
        level=initial_level,
        appearance=hero["appearance"],
        base_class=initial_class,
    )
    party = PlayerParty(
        [hero_character],
        currency=starting_currency,
        thematic_style=thematic_style,
        currency_name=currency_name,
    )
    assign_starter_items(party, initial_tier)
    return party


def assign_starter_items(party, initial_tier=1):
    item_categories = ["healing", "mp_restore", "offensive"]
    starter_items = []
    item_manager = ItemManager()
    for category in item_categories:
        item = get_random_item(category, item_manager, initial_tier)
        if item:
            starter_items.append(item)
    party.inventory.extend(starter_items)


def get_random_item(category, item_manager: ItemManager, initial_tier=1):
    item_type = get_item_type(category)
    tier_1_items = [
        item_name
        for item_name in item_manager.item_list
        if item_manager.deserialize_item(item_name).tier == initial_tier
        and isinstance(item_manager.deserialize_item(item_name), item_type)
    ]
    return (
        item_manager.deserialize_item(random.choice(tier_1_items))
        if tier_1_items
        else None
    )


def get_item_type(category):
    if category == "healing":
        return items.HealingItem
    elif category == "mp_restore":
        return items.MPRestoreItem
    elif category == "offensive":
        return items.OffensiveItem
    else:
        return None
