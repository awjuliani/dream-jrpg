from __future__ import annotations
from typing import TYPE_CHECKING, List
from src.npc.npc import NPC
from src.core.character import (
    PlayerCharacter,
    equip_starter_gear,
)
from src.game.response_manager import print_event_text
from src.npc.conversation import Conversation

if TYPE_CHECKING:
    from src.core.player_party import PlayerParty


class AllyNPC(NPC):
    def __init__(self, ally_data, current_location, story_level):
        ally_data = ally_data.copy()
        ally_data["type"] = "ally"
        super().__init__(
            ally_data,
            current_location,
            story_level=story_level,
        )
        self.base_class = ally_data["base_class"]
        self.recruited = False

    async def recruit(self, party: PlayerParty, dialogue: List[str]):
        convo = Conversation(self, party)
        outcome = await convo.start()
        if outcome == "recruit_success":
            await self.recruit_success(party)
            return "recruit_success"
        else:
            await self.recruit_failure(party)
            return "recruit_failure"

    async def recruit_success(self, party: PlayerParty):
        new_character = PlayerCharacter(
            name=self.name,
            description=self.description,
            job_class=self.job_class,
            level=self.story_level,
            base_class=self.base_class,
            portrait=self.portrait,
        )
        await equip_starter_gear(
            new_character, self.current_location, story_level=self.story_level - 4
        )

        party.add_character(new_character)
        self.recruited = True

        await print_event_text(
            f"{self.name} has joined your party!",
            f"{self.description}",
            portrait_image_url=new_character.portrait,
        )
        event_info = {
            "location": self.current_location,
            "event_text": f"{self.name} has joined your party!",
            "trigger": {"type": "ally_recruited", "value": self.name},
        }
        party.story_manager.add_past_event(event_info)

    async def recruit_failure(self, party: PlayerParty):
        await print_event_text(
            "Recruitment failed!",
            f"{self.name} is not interested in joining your party.",
            portrait_image_url=self.portrait,
        )
