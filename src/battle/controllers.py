from src.core.character import Character
from src.core.party import Party
from typing import Dict, Any, List, Callable
from src.game.response_manager import (
    choose_battle_target,
    choose_option,
    print_event_text,
)
from src.game.response_manager import (
    print_battle_menu,
)
from src.api.llm import get_llm
import asyncio

import numpy as np
import json


class Controller:
    def __init__(self, character: Character):
        self.character = character
        self.previous_action = None

    def decide_action(
        self,
        allies: Party,
        enemies: Party,
        explain: bool = False,
        turn_order: List[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement decide_action")

    def _character_to_dict(self, character: Character) -> Dict[str, Any]:
        return {
            "name": character.name,
            "job_class": character.job_class,
            "level": self._json_serializable(character.level),
            "hp": self._json_serializable(character.stats.hp),
            "max_hp": self._json_serializable(character.stats.max_hp),
            "mp": self._json_serializable(character.stats.mp),
            "max_mp": self._json_serializable(character.stats.max_mp),
            "status_effects": [effect.name for effect in character.status_effects],
        }

    def _get_available_actions(self, allies: Party) -> Dict[str, List[str]]:
        return {
            "attack": ["Basic Attack"],
            "defend": ["Defend"],
            "skill": [skill.name for skill in self.character.skills],
            "spell": [
                f"{spell.name} (MP Cost: {spell.cost})"
                for spell in self.character.spells
                if self.character.stats.mp >= spell.cost
            ],
            "item": [item.name for item in allies.inventory],
        }

    @staticmethod
    def _json_serializable(obj):
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj


class AIController(Controller):
    def __init__(self, character: Character):
        super().__init__(character)
        self.llm = get_llm()

    async def decide_action(
        self,
        allies: Party,
        enemies: Party,
        explain: bool = False,
        turn_order: List[str] = None,
    ) -> Dict[str, Any]:
        prompt = self._generate_prompt(allies, enemies)
        response = self.llm.generate_battle_command(prompt)
        if explain:
            await print_event_text(response["explanation"])
        action = self._process_action(response, allies, enemies)
        self.previous_action = action
        return action

    def _generate_prompt(self, allies: Party, enemies: Party) -> str:
        context = {
            "character": self._character_to_dict(self.character),
            "allies": [self._character_to_dict(ally) for ally in allies.characters],
            "enemies": [self._character_to_dict(enemy) for enemy in enemies.characters],
            "available_actions": self._get_available_actions(allies),
            "previous_action": self.previous_action,
        }
        return json.dumps(context, default=self._json_serializable)

    def _process_action(
        self, response: Dict[str, Any], allies: Party, enemies: Party
    ) -> Dict[str, Any]:
        action = self._validate_action(response)
        return self._validate_target(action, allies, enemies)

    def _validate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        valid_action_types = {"attack", "skill", "spell", "item", "defend"}
        if action.get("action_type") not in valid_action_types:
            print(f"Invalid action type: {action.get('action_type')}")
            return {"action_type": "attack", "target": "random_enemy"}

        if action["action_type"] != "defend" and "target" not in action:
            print("No target specified in action")
            action["target"] = "random_enemy"

        required_fields = {
            "skill": "skill_name",
            "spell": "spell_name",
            "item": "item_name",
        }

        if field := required_fields.get(action["action_type"]):
            if field not in action:
                print(f"{action['action_type'].capitalize()} action without {field}")
                return {"action_type": "attack", "target": "random_enemy"}

        return action

    def _validate_target(
        self, action: Dict[str, Any], allies: Party, enemies: Party
    ) -> Dict[str, Any]:
        if action["action_type"] == "defend":
            return action

        all_characters = allies.characters + enemies.characters
        target_name = action.get("target")

        if not target_name or not any(
            char.name == target_name for char in all_characters
        ):
            print(f"Invalid target: {target_name}. Choosing a random enemy.")
            action["target"] = np.random.choice(enemies.characters).name

        return action


class PlayerController(Controller):
    def __init__(self, character: Character, background_image_url: str = None):
        super().__init__(character)
        self.background_image_url = background_image_url

    def get_battle_status(self, party, enemies):
        status_text = "Party\n"
        status_text += str(party)
        status_text += "\n\nEnemies\n"
        status_text += str(enemies)
        return status_text

    async def decide_action(
        self,
        allies: Party,
        enemies: Party,
        explain: bool = False,
        turn_order: List[str] = None,
    ) -> Dict[str, Any]:
        while True:
            actions = ["Attack", "Skill", "Spell", "Defend", "Item", "Run"]
            action = await print_battle_menu(
                allies, enemies, actions, self.background_image_url, turn_order
            )

            async def perform_attack():
                return await self._perform_attack(enemies)

            async def select_skill():
                return await self._select_and_use_ability(
                    self.character.skills, "skill", allies, enemies
                )

            async def select_spell():
                return await self._select_and_use_ability(
                    self.character.spells, "spell", allies, enemies
                )

            async def select_item():
                return await self._select_item(allies, enemies)

            async def defend():
                return {"action_type": "defend"}

            async def run():
                return {"action_type": "run"}

            action_map = {
                "Attack": perform_attack,
                "Skill": select_skill,
                "Spell": select_spell,
                "Defend": defend,
                "Item": select_item,
                "Run": run,
            }

            result = await action_map[action]()
            if result["action_type"] != "pass":
                return result
            # If action_type is "pass", the loop continues, effectively returning to the menu

    async def _perform_attack(self, enemies: Party) -> Dict[str, Any]:
        target = await choose_battle_target(
            enemies, "enemy_party", self.background_image_url
        )
        return (
            {"action_type": "attack", "target": target.name}
            if target
            else {"action_type": "pass", "target": "none"}
        )

    async def _select_and_use_ability(
        self, abilities: List, ability_type: str, allies: Party, enemies: Party
    ) -> Dict[str, Any]:
        if not abilities:
            print(f"No {ability_type}s available.")
            return {"action_type": "pass"}

        ability = await choose_option(
            choices=abilities,
            option_details=[ability.description for ability in abilities],
            formatter=lambda a: (
                f"{a.name} ({a.cost} MP)"
                if ability_type == "spell"
                else (
                    f"{a.name} (1 SP)"
                    if ability_type == "skill" and a.name != "Attack"
                    else a.name
                )
            ),
            allow_exit=True,
            exit_option="Cancel",
            prompt=f"Choose a {ability_type}...",
            background_image_url=self.background_image_url,
            portrait_image_url=self.character.portrait,
        )

        if ability is None:
            return {"action_type": "pass"}

        # Check MP for spells
        if ability_type == "spell" and self.character.stats.mp < ability.cost:
            await print_event_text(f"Not enough MP to cast {ability.name}.")
            return {"action_type": "pass"}

        # Check SP for skills (except Attack)
        if (
            ability_type == "skill"
            and ability.name != "Attack"
            and self.character.stats.sp < 1
        ):
            await print_event_text(f"Not enough SP to use {ability.name}.")
            return {"action_type": "pass"}

        # Special handling for Double Cast
        if ability.name == "Double Cast":
            # First select the spell to double cast
            spell = await choose_option(
                choices=self.character.spells,
                option_details=[spell.description for spell in self.character.spells],
                formatter=lambda s: f"{s.name} ({s.cost * 2} MP total)",
                allow_exit=True,
                exit_option="Cancel",
                prompt="Choose a spell to double cast...",
                background_image_url=self.background_image_url,
                portrait_image_url=self.character.portrait,
            )

            if spell is None:
                return {"action_type": "pass"}

            if self.character.stats.mp < spell.cost * 2:
                await print_event_text(f"Not enough MP to double cast {spell.name}.")
                return {"action_type": "pass"}

            target = await self._get_target_for_ability(spell, allies, enemies)
            if target[0] is None:
                return {"action_type": "pass"}

            return {
                "action_type": "skill",
                "skill_name": ability.name,
                "spell_name": spell.name,
                "target": [t.name for t in target],
            }

        target = await self._get_target_for_ability(ability, allies, enemies)
        if target[0] is None:
            return {"action_type": "pass"}
        return (
            {
                "action_type": ability_type,
                f"{ability_type}_name": ability.name,
                "target": [t.name for t in target],
            }
            if target
            else {"action_type": "pass"}
        )

    async def _get_target_for_ability(self, ability, allies: Party, enemies: Party):
        async def get_ally():
            return [
                await choose_battle_target(
                    allies, "player_party", self.background_image_url
                )
            ]

        async def get_enemy():
            return [
                await choose_battle_target(
                    enemies, "enemy_party", self.background_image_url
                )
            ]

        def get_enemies():
            return enemies.characters

        def get_allies():
            return allies.characters

        def get_self():
            return [self.character]

        target_map = {
            "ally": get_ally,
            "enemy": get_enemy,
            "enemies": get_enemies,
            "allies": get_allies,
            "self": get_self,
        }

        getter = target_map.get(ability.targets)
        if getter:
            result = getter()
            return await result if asyncio.iscoroutine(result) else result
        return None

    async def _select_item(self, allies: Party, enemies: Party) -> Dict[str, Any]:
        if not allies.inventory:
            print("No items available.")
            return {"action_type": "pass"}

        item = await choose_option(
            choices=allies.inventory,
            option_details=[item.description for item in allies.inventory],
            formatter=lambda item: item.name,
            allow_exit=True,
            exit_option="Cancel",
            background_image_url=self.background_image_url,
            option_portraits=[item.portrait for item in allies.inventory],
        )

        if item is None:
            return {"action_type": "pass"}

        target = (await self._get_target_for_ability(item, allies, enemies))[0]
        return (
            {
                "action_type": "item",
                "item_name": item.name,
                "target": target.name,
            }
            if target
            else {"action_type": "pass"}
        )
