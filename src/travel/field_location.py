from src.core.player_party import PlayerParty
from src.travel.menu_handler import MenuHandler
from src.travel.base_location import Location

from typing import Dict


class FieldLocation(Location):
    def __init__(self, data: Dict, party: PlayerParty, story_level: int):
        self.type = "field"
        self.num_enemies = 3
        self.num_treasures = 1
        super().__init__(data, party, story_level)
        self.enemy_types = data["enemy_types"]
        self.menu_handler = MenuHandler(self)

    def _setup_specific_nodes(self):
        self._add_enemy_nodes(self.num_enemies)
        self._add_treasure_nodes(self.num_treasures)
