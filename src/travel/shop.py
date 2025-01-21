from abc import ABC, abstractmethod
from typing import List, Dict, Any
from copy import deepcopy
from src.core.player_party import PlayerParty
from src.core.items import SpellBook, ItemManager
from src.core.spells import SpellManager
from src.core.equipment import make_weapon, make_armor, make_accessory
from src.api.llm import get_llm
from src.game.response_manager import choose_option
from src.game.response_manager import print_event_text
from src.api.images import generate_item_portrait, generate_shop_image
import random
from src.npc.cast import get_cast
from src.npc.conversation import Conversation
from src.core.cutscene import cutscene


class Shop(ABC):
    def __init__(
        self,
        shop_info: Dict[str, Any],
        loc_info: Dict[str, Any],
        inventory: List[Dict[str, Any]],
        currency_name: str = "gold",
    ):
        self.name = shop_info["name"]
        self.description = shop_info["description"]
        self.npc = get_cast().make_new_npc(
            shop_info["shopkeeper_name"],
            shop_info["goodbye_text"],
            shop_info["name"],
            shop_info["description"],
            npc_type="shop",
        )
        self.background_image = generate_shop_image(
            loc_info["name"], loc_info["description"], self.name, self.description
        )
        self.inventory = inventory
        self.currency_name = currency_name
        self.goodbye_text = shop_info["goodbye_text"]
        self.loc_info = loc_info
        self.has_discount = False
        self.base_prices = {}

    def _apply_discount(self):
        """Apply 20% discount to all items"""
        if not self.base_prices:
            # Store original prices first time
            if isinstance(self.inventory, dict):
                # For equipment shop
                for category in self.inventory:
                    self.base_prices[category] = []
                    for item in self.inventory[category]:
                        self.base_prices[category].append(item["price"])
                        item["price"] = int(item["price"] * 0.8)
            else:
                # For item/spell shops
                self.base_prices = [item["price"] for item in self.inventory]
                for item in self.inventory:
                    item["price"] = int(item["price"] * 0.8)

    def _create_casual_shop_event(self):
        """Creates a casual conversation event for the shop"""
        return type(
            "StoryEvent",
            (),
            {
                "event_text": f"A friendly chat with {self.npc.name} at {self.name}",
                "trigger_hint": f"Having become friends with {self.npc.name}, you stop by for a casual conversation at {self.name}. "
                f"The shopkeeper has many interesting stories about the items they sell and the customers who visit.",
                "event_type": "social",
            },
        )()

    async def talk(self, party: PlayerParty):
        """Start a conversation with the shopkeeper"""
        if self.has_discount:
            casual_event = self._create_casual_shop_event()
            await cutscene(
                casual_event,
                self.loc_info["name"],
                self.loc_info["description"],
                party.list_names + [self.npc.name],
                background_image_url=self.background_image,
                conversation_length="short",
                past_events=party.story_manager.past_events,
                thematic_style=party.story_manager.thematic_style,
            )
            return

        conversation = Conversation(self.npc, party)
        outcome = await conversation.start()

        if outcome == "shop_discount" and not self.has_discount:
            self._apply_discount()
            self.has_discount = True
            await print_event_text(
                "Discount Received!",
                f"The shopkeeper seems to have taken a liking to you! They offer you a 20% discount on all items.",
                background_image_url=self.background_image,
                portrait_image_url=self.npc.portrait,
            )

    async def interact(self, party: PlayerParty):
        """Main interaction method for the shop"""
        while True:
            choice = await choose_option(
                choices=["Buy", "Talk"],
                prompt=self.name,
                sub_text=f"{self.description}\n\nWhat would you like to do?\nYour party has: {party.currency} {self.currency_name}",
                background_image_url=self.background_image,
                portrait_image_url=self.npc.portrait,
                allow_exit=True,
                exit_option="Leave",
            )

            if choice == "Buy":
                await self.buy(party)
            elif choice == "Talk":
                await self.talk(party)
            else:
                await print_event_text(
                    self.npc.name,
                    self.goodbye_text,
                    background_image_url=self.background_image,
                    portrait_image_url=self.npc.portrait,
                    input_type="dialogue",
                )
                break

    async def list_items(self, party_currency: int):
        return await choose_option(
            self.inventory,
            f"Welcome to {self.name}!",
            sub_text=self.description,
            option_details=[
                f"{item['name']}\n\n{item['description']}\n\nPrice: {item['price']} {self.currency_name}"
                for item in self.inventory
            ],
            formatter=lambda x: f"{x['name']}",
            allow_exit=True,
            exit_option="Back",
            portrait_image_url=self.npc.portrait,
            background_image_url=self.background_image,
            option_portraits=[item["portrait"] for item in self.inventory],
        )

    async def buy(self, party: PlayerParty):
        while True:
            selected_item = await self.list_items(party.currency)

            if selected_item is None:
                return

            if party.currency < selected_item["price"]:
                await print_event_text(
                    f"Not Enough {self.currency_name}",
                    f"You don't have enough {self.currency_name} for {selected_item['name']}. It costs {selected_item['price']} {self.currency_name}.",
                    background_image_url=self.background_image,
                    portrait_image_url=selected_item["portrait"],
                )
                continue

            confirm = await choose_option(
                ["Yes", "No"],
                "Confirm Purchase",
                sub_text=f"Do you want to buy {selected_item['name']} for {selected_item['price']} {self.currency_name}?",
                allow_exit=False,
                background_image_url=self.background_image,
                portrait_image_url=selected_item["portrait"],
            )

            if confirm == "Yes":
                party.currency -= selected_item["price"]
                await self.give_item(party, selected_item)
                await print_event_text(
                    "Purchase Complete",
                    f"You bought {selected_item['name']} for {selected_item['price']} {self.currency_name}.",
                    background_image_url=self.background_image,
                    portrait_image_url=selected_item["portrait"],
                )
            else:
                await print_event_text(
                    "Purchase Cancelled",
                    "",
                    background_image_url=self.background_image,
                )

    @abstractmethod
    async def give_item(self, party: PlayerParty, item: Dict[str, Any]):
        pass


class ItemShop(Shop):
    async def give_item(self, party: PlayerParty, item: Dict[str, Any]):
        item_manager = ItemManager()
        new_item = item_manager.deserialize_item(item["name"])()
        party.inventory.append(new_item)


class SpellShop(Shop):
    async def give_item(self, party: PlayerParty, item: Dict[str, Any]):
        spell_manager = SpellManager()
        spell = spell_manager.deserialize_spell(item["name"])
        spellbook = SpellBook(spell)
        party.inventory.append(spellbook)


class EquipmentShop(Shop):
    def __init__(
        self,
        shop_info: Dict[str, Any],
        loc_info: Dict[str, Any],
        inventory: Dict[str, List[Dict[str, Any]]],
        currency_name: str = "gold",
    ):
        super().__init__(
            shop_info,
            loc_info,
            inventory,
            currency_name,
        )

    async def list_categories(self):
        return await choose_option(
            ["Weapons", "Armor", "Accessories"],
            f"Welcome to {self.name}!",
            sub_text=f"{self.description}\n\nWhat type of equipment would you like to browse?",
            allow_exit=True,
            exit_option="Exit",
            background_image_url=self.background_image,
            portrait_image_url=self.npc.portrait,
        )

    async def list_items(self, category: str, party_currency: int):
        items_text = (
            f"{category} for sale:\n\n{self.currency_name}: {party_currency}\n\n"
        )
        items_text += "\n".join(
            [
                f"{item['name']:<20}: {item['price']:<4} {self.currency_name}"
                for item in self.inventory[category.lower()]
            ]
        )

        return await choose_option(
            self.inventory[category.lower()],
            f"{category} Inventory",
            sub_text=items_text,
            formatter=lambda x: x["name"],
            allow_exit=True,
            exit_option="Back",
            option_details=[
                f"{item['name']}\n\n{item['description']}\n\nPrice: {item['price']} {self.currency_name}"
                for item in self.inventory[category.lower()]
            ],
            option_portraits=[
                item["object"].portrait for item in self.inventory[category.lower()]
            ],
        )

    async def buy(self, party: PlayerParty):
        while True:
            category = await self.list_categories()
            if category is None:
                await print_event_text(
                    "Thank you for visiting!",
                    self.goodbye_text,
                    background_image_url=self.background_image,
                    portrait_image_url=self.npc.portrait,
                )
                return

            while True:
                selected_item = await self.list_items(category, party.currency)
                if selected_item is None:
                    break

                if party.currency < selected_item["price"]:
                    await print_event_text(
                        f"Not Enough {self.currency_name}",
                        f"You don't have enough {self.currency_name} for {selected_item['name']}. It costs {selected_item['price']} {self.currency_name}.",
                        background_image_url=self.background_image,
                        portrait_image_url=selected_item["portrait"],
                    )
                    continue

                confirm = await choose_option(
                    ["Yes", "No"],
                    "Confirm Purchase",
                    sub_text=f"Do you want to buy {selected_item['name']} for {selected_item['price']} {self.currency_name}?",
                    allow_exit=False,
                    portrait_image_url=selected_item["portrait"],
                )

                if confirm == "Yes":
                    party.currency -= selected_item["price"]
                    await self.give_item(party, selected_item)
                    await print_event_text(
                        "Purchase Complete",
                        f"You bought {selected_item['name']} for {selected_item['price']} {self.currency_name}.",
                        background_image_url=self.background_image,
                        portrait_image_url=selected_item["portrait"],
                    )
                else:
                    await print_event_text(
                        "Purchase Cancelled",
                        "",
                        background_image_url=self.background_image,
                    )

    async def give_item(self, party: PlayerParty, item: Dict[str, Any]):
        new_equipment = deepcopy(item["object"])
        await party.add_equipment(new_equipment)


def make_item_shop(
    shop_info: Dict,
    level: int,
    loc_info: dict,
    currency_name: str = "gold",
) -> ItemShop:
    item_manager = ItemManager()
    llm_shop_info = get_llm().generate_item_shop(
        shop_info["name"],
        loc_info,
        level,
        item_manager.item_list,
    )
    inventory = [
        {
            "name": item["name"],
            "price": item["price"],
            "description": item_manager.get_item_description(item["name"]),
            "portrait": item_manager.get_item_portrait(item["name"]),
        }
        for item in llm_shop_info["items"]
    ]
    shop = ItemShop(
        shop_info,
        loc_info,
        inventory,
        currency_name,
    )
    return shop


def make_spell_shop(
    shop_info: Dict,
    level: int,
    loc_info: dict,
    currency_name: str = "gold",
) -> SpellShop:
    spell_manager = SpellManager()
    llm_shop_info = get_llm().generate_spell_shop(
        shop_info["name"],
        loc_info,
        level,
        spell_manager.spell_list,
    )
    inventory = [
        {
            "name": spell["name"],
            "price": spell["price"],
            "description": f"A spellbook which teaches {spell['name']}. \n\n{spell_manager.get_spell_description(spell['name'])}",
            "portrait": generate_item_portrait(
                spell["name"],
                f"A magical spell book which teaches the spell: {spell['name']}.",
            ),
        }
        for spell in llm_shop_info["spells"]
    ]
    shop = SpellShop(
        shop_info,
        loc_info,
        inventory,
        currency_name,
    )
    return shop


def make_equipment_shop(
    shop_info: Dict,
    party: PlayerParty,
    level: int,
    loc_info: dict,
    currency_name: str = "gold",
) -> EquipmentShop:
    job_classes = [char.job_class for char in party.characters]
    inventory = {"weapons": [], "armor": [], "accessories": []}

    for job_class in job_classes:
        weapon = make_weapon(job_class, level, loc_info)
        armor = make_armor(job_class, level, loc_info)
        accessory = make_accessory(job_class, level, loc_info)

        base_price = level * 50
        inventory["weapons"].append(
            {
                "name": f"{weapon.name} ({job_class})",
                "price": base_price + random.randint(-20, 20),
                "object": weapon,
                "description": weapon.description,
                "portrait": weapon.portrait,
            }
        )
        inventory["armor"].append(
            {
                "name": f"{armor.name} ({job_class})",
                "price": base_price + random.randint(-20, 20),
                "object": armor,
                "description": armor.description,
                "portrait": armor.portrait,
            }
        )
        inventory["accessories"].append(
            {
                "name": f"{accessory.name} ({job_class})",
                "price": base_price + random.randint(-20, 20),
                "object": accessory,
                "description": accessory.description,
                "portrait": accessory.portrait,
            }
        )

    shop = EquipmentShop(
        shop_info,
        loc_info,
        inventory,
        currency_name,
    )
    return shop
