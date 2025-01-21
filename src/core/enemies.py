from src.core.character import Character
from src.battle.elements import Element, deserialize_element, NONE, ELEMENT_LIST
from src.core.spells import SpellManager
from src.battle.skills import EnemySpecial
from src.api.llm import get_llm
from src.core.party import Party
from src.core.items import ItemManager
import random


class EnemyCharacter(Character):
    def __init__(
        self,
        name: str,
        description: str = None,
        level: int = 1,
        loot=None,
        job_class: str = None,
        enemy_type: str = None,
        element: Element = NONE,
        portrait: str = None,
    ):
        super().__init__(
            name, description, job_class, level, element, portrait=portrait
        )
        base_currency = 10 * level
        base_exp = 100 * level
        self.currency = random.randint(int(base_currency * 0.5), int(base_currency * 2))
        self.experience = random.randint(int(base_exp * 0.5), int(base_exp * 2))
        self.loot = loot
        self.enemy_type = enemy_type
        if self.enemy_type == "regular":
            self.stats.max_hp = int(self.stats.max_hp * 0.5)
            self.stats.hp = self.stats.max_hp
        else:
            self.experience *= 3

    def get_details_text(self):
        details = super().get_details_text()
        details += (
            f"Spell List: " + ", ".join([spell.name for spell in self.spells]) + "\n"
        )
        details += (
            f"Skill List: " + ", ".join([skill.name for skill in self.skills]) + "\n"
        )
        return details

    def to_dict(self):
        char_dict = super().to_dict()
        char_dict["loot"] = [item.name for item in self.loot]
        char_dict["enemy_type"] = self.enemy_type
        return char_dict


def make_enemy(location_dict, level=1, is_boss=False, enemy_info=None, portrait=None):
    enemy_type = "boss" if is_boss else "regular"
    spell_manager = SpellManager()
    generated_info = get_llm().generate_enemy(
        level=level,
        enemy_info=enemy_info,
        location=location_dict,
        spells=spell_manager.spell_list,
        elements=ELEMENT_LIST,
        enemy_type=enemy_type,
    )
    im = ItemManager()
    num_items = min(2, len(im.item_list))
    try:
        selected_items = random.sample(im.item_list, num_items)
        items = [im.deserialize_item(item) for item in selected_items]
    except ValueError as e:
        items = []

    enemy = EnemyCharacter(
        name=generated_info["name"],
        description=generated_info["description"],
        job_class=generated_info["job_class"],
        level=level,
        enemy_type=enemy_type,
        element=deserialize_element(generated_info["element"]),
        portrait=portrait,
        loot=items,
    )

    # Check if the generated spell names are valid
    valid_spells = [
        spell for spell in generated_info["spells"] if spell in spell_manager.spell_list
    ]
    enemy.spells.extend(
        [spell_manager.deserialize_spell(spell) for spell in valid_spells]
    )

    enemy.skills.append(EnemySpecial(generated_info["attack"]))
    return enemy


class EnemyParty(Party):
    def __init__(self, characters: list[Character]):
        self.characters = characters
        self.inventory = []
