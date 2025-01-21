from src.core.character import Character
from src.core import items
from typing import List


class Party:
    def __init__(self, characters: list[Character], inventory: List[items.Item] = []):
        self.characters = characters
        self.inventory: List[items.Item] = inventory

    def to_dict(self):
        return {
            "characters": self.characters_to_dict(),
            "inventory": [item.name for item in self.inventory],
        }

    def characters_to_dict(self):
        return [character.to_dict() for character in self.characters]

    def check_alive(self):
        return any(character.stats.alive for character in self.characters)

    def __str__(self):
        return "\n".join(str(character) for character in self.characters)

    @property
    def list_names(self):
        return [character.name for character in self.characters]

    @property
    def avg_level(self):
        return sum([character.level for character in self.characters]) / len(
            self.characters
        )
