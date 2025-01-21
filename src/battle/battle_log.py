from __future__ import annotations
from typing import TYPE_CHECKING
from src.core.items import *
from src.battle.effects import Sleep
from src.game.response_manager import ResponseManager, print_event_text

if TYPE_CHECKING:
    from src.core.character import Character


class BattleLog:
    def __init__(self, background_image_url):
        self.llm = get_llm()
        self.rm = ResponseManager()
        self.background_image_url = background_image_url

    async def print_start_text(self, battle_type, context, party, enemies):
        battle_json = {
            "event_type": "battle_start",
            "battle_type": battle_type,
            "context": context,
            "party": [f"{char.name} ({char.description})" for char in party],
            "enemies": [f"{char.name} ({char.description})" for char in enemies],
        }
        battle_str = str(battle_json)
        battle_text = self.llm.generate_action_text(battle_str)

        await print_event_text("Battle Start!", battle_text, self.background_image_url)

    async def print_battle_result(
        self, result, party, enemies, total_currency, total_exp
    ):
        battle_text = f"Your party {[f'{char.name} ({char.description})' for char in party.characters]} {result} the {len(enemies.characters)} enemie(s) {[f'{char.name} ({char.description})' for char in enemies.characters]}!"
        battle_text = self.llm.generate_action_text(battle_text)
        if result == "defeated":
            currency_text = f"\n\nParty earned {total_currency} {party.story_manager.currency_name}!\n\n"
            for character in party.characters:
                currency_text += f"{character.name} earned {total_exp} experience!\n"
            battle_text += currency_text
        await print_event_text(
            f"You {result} the enemies!",
            battle_text,
            self.background_image_url,
            input_type="message",
        )

    def get_battle_status(self, party, enemies):
        status_text = "Party\n"
        status_text += str(party)
        status_text += "\n\nEnemies\n"
        status_text += str(enemies)
        return status_text

    async def print_status(self, party, enemies):
        status_text = self.get_battle_status(party, enemies)
        await print_event_text("Battle Status", status_text, self.background_image_url)

    async def print_no_abilities(self, ability_type, party, enemies, character):
        await print_event_text(
            f"No {ability_type}s to use",
            f"{character.name} does not have any {ability_type}s to use",
            self.background_image_url,
            input_type="message",
            portrait_image_url=character.portrait,
        )

    async def print_cannot_act(self, character: Character):
        for status_effect in character.status_effects:
            if isinstance(status_effect, Sleep):
                action = (
                    f"{character.name} ({character.job_class}) is asleep and cannot act"
                )
                fancy_text = self.llm.generate_action_text(action)
                await print_event_text(
                    f"{character.name} cannot act",
                    fancy_text,
                    self.background_image_url,
                )
                return

        await print_event_text(
            f"{character.name} cannot act",
            "",
            self.background_image_url,
            input_type="message_mini",
        )

    async def print_not_enough_mp(self, character, ability):
        await print_event_text(
            f"{character.name} does not have enough MP to cast {ability.name}",
            "",
            self.background_image_url,
            input_type="message_mini",
        )

    async def print_silenced(self, character):
        await print_event_text(
            f"{character.name} is silenced and cannot cast spells",
            "",
            self.background_image_url,
            input_type="message_mini",
        )

    async def print_run_attempt(self, character):
        await print_event_text(
            "You attempt to run away...",
            "",
            self.background_image_url,
            input_type="message_mini",
            portrait_image_url=character.portrait,
        )

    async def print_defend_action(self, character):
        await print_event_text(
            f"{character.name} defends",
            "",
            self.background_image_url,
            input_type="message_mini",
            portrait_image_url=character.portrait,
        )

    async def print_pass_action(self, character):
        await print_event_text(
            f"{character.name} passes",
            "",
            self.background_image_url,
            input_type="message_mini",
            portrait_image_url=character.portrait,
        )
