from src.core.player_party import PlayerParty
from src.game.response_manager import choose_option
from src.game.response_manager import print_event_text
import random
from src.api.llm import get_llm
from src.api.images import generate_shop_image
from src.npc.cast import get_cast
from src.npc.conversation import Conversation
from src.core.cutscene import cutscene


class Inn:
    def __init__(
        self,
        inn_info: dict,
        loc_info: dict,
        rest_cost: int,
        currency_name: str = "gold",
    ):
        self.name = inn_info["name"]
        self.description = inn_info["description"]
        self.npc = get_cast().make_new_npc(
            inn_info["shopkeeper_name"],
            inn_info["goodbye_text"],
            inn_info["name"],
            inn_info["description"],
            npc_type="innkeeper",
        )
        self.background_image = generate_shop_image(
            loc_info["name"],
            loc_info["description"],
            self.name,
            self.description,
        )
        self.base_rest_cost = rest_cost
        self.rest_cost = rest_cost
        self.currency_name = currency_name
        self.goodbye_text = inn_info["goodbye_text"]
        self.loc_info = loc_info
        self.has_discount = False

    def _create_casual_inn_event(self):
        """Creates a casual conversation event for the inn"""
        return type(
            "StoryEvent",
            (),
            {
                "event_text": f"A friendly chat with {self.npc.name} at the {self.name}",
                "trigger_hint": f"Having become friends with {self.npc.name}, you stop by for a casual conversation at {self.name}. "
                f"The innkeeper has been running this establishment for years and always has interesting stories "
                f"to share about travelers and local happenings.",
                "event_type": "social",
            },
        )()

    async def talk(self, party: PlayerParty):
        """Start a conversation with the innkeeper"""
        if self.has_discount:
            casual_event = self._create_casual_inn_event()
            await cutscene(
                casual_event,
                self.loc_info["name"],
                self.loc_info["description"],
                party.list_names + [self.npc.name],
                background_image_url=self.background_image,
                past_events=party.story_manager.past_events,
                thematic_style=party.story_manager.thematic_style,
                conversation_length="short",
            )
            return

        conversation = Conversation(self.npc, party)
        outcome = await conversation.start()

        if outcome == "rest_discount" and not self.has_discount:
            self.rest_cost = int(self.base_rest_cost * 0.8)
            self.has_discount = True
            await print_event_text(
                "Discount Received!",
                f"The innkeeper seems to have taken a liking to you! They offer you a 20% discount on rooms. The rest cost is now {self.rest_cost} {self.currency_name}.",
                background_image_url=self.background_image,
                portrait_image_url=self.npc.portrait,
            )

    async def interact(self, party: PlayerParty):
        """Main interaction method for the inn"""
        while True:
            choice = await choose_option(
                choices=["Rest", "Talk", "Leave"],
                prompt=self.name,
                sub_text=f"{self.description}\n\nWhat would you like to do?\nRest cost: {self.rest_cost} {self.currency_name}\nYour party has: {party.currency} {self.currency_name}",
                background_image_url=self.background_image,
                portrait_image_url=self.npc.portrait,
            )

            if choice == "Rest":
                await self.rest(party)
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

    async def rest(self, party: PlayerParty):
        if party.currency < self.rest_cost:
            await print_event_text(
                f"Not Enough {self.currency_name}",
                f"You don't have enough {self.currency_name} to rest here. You need {self.rest_cost} {self.currency_name}.",
                background_image_url=self.background_image,
            )
            return

        confirm = await choose_option(
            choices=["Yes", "No"],
            prompt=self.name,
            sub_text=f"{self.description}\n\nDo you want to rest for {self.rest_cost} {self.currency_name}?\n\nYour party currently has {party.currency} {self.currency_name}.",
            allow_exit=False,
            background_image_url=self.background_image,
            portrait_image_url=self.npc.portrait,
        )

        if confirm == "Yes":
            party.currency -= self.rest_cost
            await self._restore_party(party)
        else:
            await print_event_text(
                "You decided not to rest.",
                self.goodbye_text,
                background_image_url=self.background_image,
                portrait_image_url=self.npc.portrait,
            )

    async def _restore_party(self, party: PlayerParty):
        for character in party.characters:
            character.stats.hp = character.stats.max_hp
            character.stats.mp = character.stats.max_mp
            character.remove_all_status_effects()

        rest_text = get_llm().generate_action_text(
            f"The party of {party.list_names} rests at the {self.name} ({self.description}) inn for the night. It restores their HP and MP to full and removes all status ailments. They feel refreshed and ready to continue their journey."
        )
        await print_event_text(
            "Party Restored",
            rest_text
            + f"\n\nYour party has {party.currency} {self.currency_name} remaining.",
            background_image_url=self.background_image,
        )


# The make_inn function remains unchanged
def make_inn(
    inn_info: dict,
    story_level: int,
    loc_info: dict,
    currency_name: str = "gold",
) -> Inn:
    base_cost = story_level * random.randint(15, 25)
    base_cost = base_cost - (base_cost % 5)
    return Inn(
        inn_info,
        loc_info,
        base_cost,
        currency_name,
    )
