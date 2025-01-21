from src.travel.menu_handler import MenuHandler
from src.travel.field_location import FieldLocation

from typing import Dict


class DungeonLocation(FieldLocation):
    def __init__(self, data: Dict, party, story_level: int):
        self.type = "dungeon"
        self.num_enemies = 5
        self.num_treasures = 1
        super().__init__(data, party, story_level)
        self.menu_handler = MenuHandler(self)

    def _setup_specific_nodes(self):
        self._add_enemy_nodes(self.num_enemies)
        self._add_treasure_nodes(self.num_treasures)
