from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Any, Union, Tuple

from src.core.items import Item  # Import specific items instead of using *
import numpy as np
from src.utils.utils import create_unique_enemy_names
from src.core.character import PlayerCharacter, Character
from src.battle.effects import Defend
from src.api.llm import get_llm
from src.battle.battle_log import BattleLog
from src.battle.controllers import AIController, PlayerController, Controller

if TYPE_CHECKING:
    from typing import Dict, List, Any, Union, Tuple
    from src.core.player_party import PlayerParty
    from src.core.enemies import EnemyParty


class Battle:
    def __init__(
        self,
        party: PlayerParty,
        enemies: EnemyParty,
        context: str = "",
        background_image_url: str = None,
    ):
        self.party = party
        self.enemies = self._create_unique_enemy_party(enemies)
        self.context = context
        self.battle_log = BattleLog(background_image_url)
        self.ran = False
        self.time_units: Dict[Character, float] = {}
        self.background_image_url = background_image_url
        self.controllers: Dict[Character, Controller] = self._initialize_controllers()

    def _create_unique_enemy_party(self, enemies: EnemyParty) -> EnemyParty:
        unique_names = create_unique_enemy_names(
            [enemy.name for enemy in enemies.characters]
        )
        for enemy, name in zip(enemies.characters, unique_names):
            enemy.name = name
        return enemies

    def _initialize_controllers(self) -> Dict[Character, Controller]:
        controllers = {}
        for enemy in self.enemies.characters:
            controllers[enemy] = AIController(enemy)
        for character in self.party.characters:
            if isinstance(character, PlayerCharacter):
                controllers[character] = PlayerController(
                    character, self.background_image_url
                )
            else:
                controllers[character] = AIController(character)
        return controllers

    async def start(self, battle_type: str = "ambush") -> str:
        # Reset SP at battle start
        for char in self.party.characters + self.enemies.characters:
            char.reset_sp()
        await self.battle_log.print_start_text(
            battle_type, self.context, self.party.characters, self.enemies.characters
        )
        self._initialize_time_units()
        battle_over = False
        while not battle_over:
            battle_over, outcome = await self._take_turns()
        return outcome

    def _initialize_time_units(self) -> None:
        self.time_units = {
            char: 0 for char in self.party.characters + self.enemies.characters
        }

    async def _take_turns(self) -> tuple[bool, str]:
        self.predicted_order = self.predict_turn_order()
        active_character = self._get_next_active_character()
        if active_character is None:
            return await self._check_battle_over()

        self.time_units[active_character] = 0

        if active_character.can_act:
            await self._process_turn(active_character)
        else:
            await self._process_incapacitated_turn(active_character)

        return await self._check_battle_over()

    def _get_next_active_character(self) -> Union[Character, None]:
        alive_characters = {
            char: tu for char, tu in self.time_units.items() if char.stats.alive
        }
        if not alive_characters:
            return None

        for character in alive_characters:
            self.time_units[character] += np.log2(character.stats.speed + 1)

        return max(alive_characters, key=self.time_units.get)

    async def _process_turn(self, character: Character) -> None:
        character.active_turn = True
        await character.update_status_effects()

        controller = self.controllers[character]
        allies = self.party if character in self.party.characters else self.enemies
        enemies = self.enemies if character in self.party.characters else self.party

        action = await controller.decide_action(
            allies, enemies, turn_order=self.predicted_order
        )
        await self._execute_action(character, action)
        character.active_turn = False

    async def _process_incapacitated_turn(self, character: Character) -> None:
        character.active_turn = True
        await self.battle_log.print_cannot_act(character)
        character.active_turn = False

    async def _check_battle_over(self) -> tuple[bool, str]:
        # Reset SP when battle ends
        if self.ran or not self.enemies.check_alive() or not self.party.check_alive():
            for char in self.party.characters + self.enemies.characters:
                char.reset_sp()
        if self.ran:
            await self.battle_log.print_battle_result(
                "ran away from", self.party, self.enemies, 0, 0
            )
            return True, "party_ran"
        if not self.enemies.check_alive():
            total_currency, total_exp = self._calculate_exp_and_currency()
            await self.battle_log.print_battle_result(
                "defeated",
                self.party,
                self.enemies,
                total_currency,
                total_exp,
            )
            await self._award_experience_and_currency(total_currency, total_exp)
            return True, "party_victory"
        if not self.party.check_alive():
            await self.battle_log.print_battle_result(
                "were defeated by", self.party, self.enemies, 0, 0
            )
            return True, "party_defeated"
        return False, ""

    async def _execute_action(
        self, character: Character, action: Dict[str, Any]
    ) -> None:
        action_handlers = {
            "attack": self._handle_attack,
            "skill": self._handle_skill,
            "spell": self._handle_spell,
            "item": self._handle_item,
            "run": self._handle_run,
            "defend": self._handle_defend,
            "pass": self._handle_pass,
        }
        handler = action_handlers.get(action.get("action_type"))
        if handler:
            await handler(character, action)
        else:
            await self.battle_log.print_unknown_action(character, action)

    async def _handle_attack(
        self, character: Character, action: Dict[str, Any]
    ) -> None:
        target = self._get_target(action["target"])
        if target:
            await character.attack(target)
            character.stats.sp_change(1)  # Gain 1 SP for attacking
        else:
            await self.battle_log.print_invalid_target(character, action["target"])

    async def _handle_skill(self, character: Character, action: Dict[str, Any]) -> None:
        skill_name = action.get("skill_name")
        skill = next((s for s in character.skills if s.name == skill_name), None)
        if skill:
            if skill_name == "Double Cast":
                # Special handling for Double Cast
                spell_and_target = {
                    "spell_name": action.get("spell_name"),
                    "target": self._get_target(action["target"]),
                }
                await skill.use(spell_and_target, character)
            else:
                # Normal skill handling
                target = self._get_target(action["target"])
                if target:
                    await skill.use(target, character)
                else:
                    await self.battle_log.print_invalid_target(
                        character, action["target"]
                    )
        else:
            await self.battle_log.print_no_abilities(
                "skill", self.party, self.enemies, character
            )

    async def _handle_spell(self, character: Character, action: Dict[str, Any]) -> None:
        spell_name = action.get("spell_name")
        spell = next((s for s in character.spells if s.name == spell_name), None)
        if spell:
            if character.stats.mp >= spell.cost:
                target = self._get_target(action["target"])
                if target:
                    await spell.cast(target, character)
                    character.stats.sp_change(1)
                else:
                    await self.battle_log.print_invalid_target(
                        character, action["target"]
                    )
            else:
                await self.battle_log.print_not_enough_mp(character, spell)
        else:
            await self.battle_log.print_no_abilities(
                "spell", self.party, self.enemies, character
            )

    async def _handle_item(self, character: Character, action: Dict[str, Any]) -> None:
        item_name = action.get("item_name")
        item = next((i for i in self.party.inventory if i.name == item_name), None)
        if item:
            target = self._get_target(action["target"])
            if target:
                await item.use(target)
                self.party.inventory.remove(item)
                character.stats.sp_change(1)
            else:
                await self.battle_log.print_invalid_target(character, action["target"])
        else:
            await self.battle_log.print_item_not_found(character, item_name)

    async def _handle_run(self, character: Character, action: Dict[str, Any]) -> None:
        self.ran = True

    async def _handle_defend(
        self, character: Character, action: Dict[str, Any]
    ) -> None:
        await character.add_status_effect(Defend(duration=1, defense_bonus=10))
        character.stats.sp_change(1)  # Gain 1 SP for defending

    async def _handle_pass(self, character: Character, action: Dict[str, Any]) -> None:
        await self.battle_log.print_pass_action(character)

    def _get_target(
        self, target_info: Union[str, int, List[str]]
    ) -> Union[Character, List[Character], None]:
        all_targets = self.party.characters + self.enemies.characters

        if isinstance(target_info, list):
            return [char for char in all_targets if char.name in target_info]

        if isinstance(target_info, str):
            if target_info == "random_enemy":
                alive_enemies = [e for e in self.enemies.characters if e.stats.alive]
                return np.random.choice(alive_enemies) if alive_enemies else None
            return next((c for c in all_targets if c.name == target_info), None)

        if isinstance(target_info, int):
            if 0 <= target_info < len(all_targets):
                return all_targets[target_info]
            return None

        return None

    def _calculate_exp_and_currency(self):
        total_currency = sum(enemy.currency for enemy in self.enemies.characters)
        total_exp = sum(enemy.experience for enemy in self.enemies.characters)
        return total_currency, total_exp

    async def _award_experience_and_currency(self, total_currency, total_exp):
        self.party.currency += total_currency

        # Move any stolen items from temporary inventory to party inventory
        for character in self.party.characters:
            if hasattr(character, "temp_inventory"):
                for item in character.temp_inventory:
                    self.party.inventory.append(item)
                character.temp_inventory.clear()  # Clear the temporary inventory

        for character in self.party.characters:
            await character.gain_xp(total_exp)
        return total_currency, total_exp

    def predict_turn_order(self, num_turns: int = 10) -> List[Tuple[Character, float]]:
        predicted_order = []
        simulated_time_units = self.time_units.copy()

        for _ in range(num_turns):
            alive_characters = {
                char: tu
                for char, tu in simulated_time_units.items()
                if char.stats.alive
            }
            if not alive_characters:
                break

            for character in alive_characters:
                simulated_time_units[character] += np.log2(character.stats.speed + 1)

            next_character = max(alive_characters, key=simulated_time_units.get)
            predicted_order.append(next_character)
            simulated_time_units[next_character] = 0
        return predicted_order
