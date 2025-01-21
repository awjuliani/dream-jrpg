from typing import List, Dict
from src.game.response_manager import print_event_text
from src.api.llm import get_llm
from src.core.party import Party
from src.npc.npc import NPC
from src.game.response_manager import ResponseManager
import random


class Conversation:
    def __init__(self, npc: NPC, party: Party):
        self.npc = npc
        self.party = party
        self.conversation_history: List[Dict[str, str]] = []

    async def start(self) -> tuple[str, str]:
        """Start a conversation between the NPC and the party."""
        # Get the complete dialogue tree
        dialogue_tree = await self._generate_dialogue()

        # Display initial NPC message
        await print_event_text(
            self.npc.name,
            f'"{dialogue_tree["initial_message"]}"',
            portrait_image_url=self.npc.portrait,
            input_type="dialogue",
        )

        # Get first level response
        first_response = await self._get_player_response(
            dialogue_tree["initial_message"],
            dialogue_tree["responses"],
        )

        # Display NPC's intermediate reply
        await print_event_text(
            self.npc.name,
            f'"{first_response["npc_reply"]}"',
            portrait_image_url=self.npc.portrait,
            input_type="dialogue",
        )

        # Get second level response
        final_response = await self._get_player_response(
            first_response["npc_reply"],
            first_response["follow_up_responses"],
        )

        # Display final NPC message
        await print_event_text(
            self.npc.name,
            f'"{final_response["final_message"]}"',
            portrait_image_url=self.npc.portrait,
            input_type="dialogue",
        )

        return final_response["outcome"]

    async def _generate_dialogue(self) -> Dict[str, any]:
        return get_llm().generate_npc_dialogue(
            self.npc.basic_info,
            event_context=self.party.story_manager.next_event.trigger_hint,
            convo_context="initial_greeting",
            valid_outcomes=self.npc.get_valid_outcomes(),
            player_name=self.party.leader.name,
            player_description=self.party.leader.description,
            current_location=self.npc.current_location,
        )

    async def _get_player_response(
        self, npc_message: str, responses: List[Dict[str, any]]
    ) -> Dict[str, any]:
        rm = ResponseManager()
        # shuffle responses
        random.shuffle(responses)

        rm.set_game_response(
            input_type="conversation",
            main_text=f"{self.npc.name} says:",
            npc_text=f'"{npc_message}"',
            menu_options=[r["short_text"] for r in responses],
            option_details=[f'"{r["full_text"]}"' for r in responses],
            player_text="(Choose a response...)",
            npc_portrait_url=self.npc.portrait,
            player_portrait_url=self.party.leader.portrait,
        )
        rm.send_game_response()

        response_text = await rm.get_player_response()
        selected_response = next(
            r for r in responses if r["short_text"] == response_text
        )

        await print_event_text(
            f"{self.party.leader.name}",
            f'"{selected_response["full_text"]}"',
            portrait_image_url=self.party.leader.portrait,
            input_type="dialogue",
        )

        return selected_response
