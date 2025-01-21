from src.core.player_party import PlayerParty
from src.travel.menu_handler import MenuHandler
from src.travel.inn import make_inn
from src.travel.shop import make_item_shop, make_spell_shop, make_equipment_shop
from src.travel.base_location import Location
from typing import Dict
import random


class TownLocation(Location):
    def __init__(self, data: Dict, party: PlayerParty, story_level: int):
        super().__init__(data, party, story_level)
        self.type = "town"
        self._shops = {}
        self.menu_handler = MenuHandler(self)

    def _create_shop(self, shop_type):
        shop_data = self._data.get(shop_type)
        if not shop_data:
            return None
        if shop_type == "inn":
            return make_inn(
                shop_data,
                self.story_level,
                self._data,
                self.party.story_manager.currency_name,
            )
        elif shop_type == "item_shop":
            return make_item_shop(
                shop_data,
                self.story_level,
                self._data,
                self.party.story_manager.currency_name,
            )
        elif shop_type == "spell_shop":
            return make_spell_shop(
                shop_data,
                self.story_level,
                self._data,
                self.party.story_manager.currency_name,
            )
        elif shop_type in ["equipment_shop"]:
            return make_equipment_shop(
                shop_data,
                self.party,
                self.story_level,
                self._data,
                self.party.story_manager.currency_name,
            )
        return None

    def _get_shop(self, shop_type):
        if shop_type not in self._shops:
            self._shops[shop_type] = self._create_shop(shop_type)
        return self._shops.get(shop_type)

    def _setup_specific_nodes(self):
        """Add town-specific nodes to the grid"""
        if self.part == "A":
            coords = [(0, 0), (0, 2), (2, 0), (2, 2)]
            random.shuffle(coords)
            for shop_type in ["inn", "item_shop", "spell_shop", "equipment_shop"]:
                self._add_node(shop_type, self._data.get(shop_type), coords.pop(0))
