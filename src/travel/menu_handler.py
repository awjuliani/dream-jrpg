from __future__ import annotations
from typing import List, Any, Dict, TYPE_CHECKING
from dataclasses import dataclass
from src.game.response_manager import ResponseManager, print_event_text
from src.api.llm import get_llm

if TYPE_CHECKING:
    from src.travel.base_location import Location


@dataclass
class MenuItem:
    display_template: str
    action_template: str

    def format(self, **kwargs) -> "MenuItem":
        return MenuItem(
            display_template=self.display_template.format(**kwargs),
            action_template=self.action_template.format(**kwargs),
        )


class MenuItems:
    RETURN = MenuItem("Travel to {name}", "previous_location")
    PARTY_MENU = MenuItem("Party Menu", "party_menu")
    VISIT_SHOP = MenuItem("Visit {name}", "visit_{type}")
    TALK_TO_NPC = MenuItem("Talk to {name}", "talk_to_npc")
    GO_TO_SUBLOCATION = MenuItem("Go to {name}", "go_to_{name}")
    TRAVEL_TO_NEXT = MenuItem("Travel to {name}", "next_location")
    EXPLORE_AREA = MenuItem("Explore {name}", "explore")
    CONFRONT_BOSS = MenuItem("Confront {name}", "talk_to_npc")
    SAVE_AND_EXIT = MenuItem("Save and Exit", "save_and_exit")
    MOVE_DIRECTION = MenuItem("{direction}", "move_{direction}")
    LOOK_DIRECTION = MenuItem("{direction}", "look_{direction}")
    FIGHT_ENEMY = MenuItem("Fight Enemies", "fight_enemy")
    OPEN_TREASURE = MenuItem("Open Treasure Chest", "open_treasure")
    INSPECT_LANDMARK = MenuItem("Inspect {name}", "inspect_landmark")


class MenuHandler:
    def __init__(self, location: Location):
        self.location = location
        self.choices: List[MenuItem] = []

    def add_choice(self, menu_item: MenuItem, **kwargs):
        self.choices.append(menu_item.format(**kwargs))

    def get_choices(self) -> List[MenuItem]:
        self.choices = []
        current_node = self.location.grid.get_current_node()

        # Add standard menu options
        self.add_choice(MenuItems.PARTY_MENU)
        self.add_choice(MenuItems.SAVE_AND_EXIT)

        # Get current position
        row, col = self.location.grid.player_pos

        # Add movement options
        available_moves = self.location.grid.get_available_moves()
        for direction in self.location.grid.get_all_moves():
            entrance_side = self.location.entrance_side.capitalize()
            exit_side = self.location.exit_side.capitalize()

            # Check if we're at the entrance position
            is_at_entrance = (
                entrance_side in ["East", "West"]
                and row == 1
                and col == (2 if entrance_side == "East" else 0)
            ) or (
                entrance_side in ["North", "South"]
                and col == 1
                and row == (0 if entrance_side == "North" else 2)
            )

            # Check if we're at the exit position
            is_at_exit = (
                exit_side in ["East", "West"]
                and row == 1
                and col == (2 if exit_side == "East" else 0)
            ) or (
                exit_side in ["North", "South"]
                and col == 1
                and row == (0 if exit_side == "North" else 2)
            )

            # Handle travel options at edges
            if (
                direction == entrance_side
                and is_at_entrance
                and self.location.previous_location
            ):
                self.add_choice(MenuItems.RETURN, name=self.location.previous_location)
            elif direction == exit_side and is_at_exit and self.location.next_location:
                self.add_choice(
                    MenuItems.TRAVEL_TO_NEXT, name=self.location.next_location
                )
            # Handle regular movement
            elif direction in available_moves:
                self.add_choice(MenuItems.MOVE_DIRECTION, direction=direction)
            else:
                self.add_choice(MenuItems.LOOK_DIRECTION, direction=direction)

        # Add node-specific options
        self._add_node_specific_choices(current_node)

        return self.choices

    def _add_node_specific_choices(self, node):
        """Add menu choices based on the current node type"""
        # Shop nodes
        if node.node_type in ["inn", "item_shop", "spell_shop", "equipment_shop"]:
            self.add_choice(MenuItems.VISIT_SHOP, name=node.name, type=node.node_type)
        elif node.node_type == "npc":
            if node.data.get("type") == "boss":
                self.add_choice(MenuItems.CONFRONT_BOSS, name=node.name)
            else:
                self.add_choice(MenuItems.TALK_TO_NPC, name=node.name)
        elif node.node_type == "landmark":
            self.add_choice(MenuItems.INSPECT_LANDMARK, name=node.name)
        elif node.node_type == "enemy":
            self.add_choice(MenuItems.FIGHT_ENEMY, name=node.name)
        elif node.node_type == "treasure":
            self.add_choice(MenuItems.OPEN_TREASURE, name=node.name)
        elif node.node_type == "boss":
            self.add_choice(MenuItems.CONFRONT_BOSS, name=self.location.boss["name"])

    async def handle_choice(self, action: str) -> Any:
        """Handle all possible menu actions"""
        # Basic navigation actions
        if action == "previous_location":
            return self.location.previous_location
        elif action == "next_location":
            if self.location.unlock_exit:
                return self.location.next_location
            else:
                current_objective = (
                    self.location.party.story_manager.next_event.trigger_hint
                )
                text = f"I still have business to attend to here. I need to: {current_objective}"
                fancy_text = get_llm().generate_action_text(text)
                await print_event_text(
                    self.location.party.leader.name,
                    fancy_text,
                    input_type="dialogue",
                    portrait_image_url=self.location.party.leader.portrait,
                )
                return None
        elif action == "party_menu":
            await self.location.party.party_menu(self.location)
        elif action == "save_and_exit":
            return "save_and_exit"
        elif action.startswith("move_"):
            direction = action[5:]
            await self.location.move(direction)

        # Shop interactions
        elif action.startswith("visit_"):
            shop_type = action[6:]
            shop = self.location._get_shop(shop_type)
            if shop:
                await shop.interact(self.location.party)

        # Look direction
        elif action.startswith("look_"):
            direction = action[5:]
            await self.location.look_direction(direction)

        # NPC interactions
        elif action == "talk_to_npc":
            result = await self.location.talk_to_npc()
            if result:
                return result

        # Landmark interactions
        elif action == "inspect_landmark":
            await self.location.inspect_landmark()

        # Combat and treasure interactions
        elif action == "fight_enemy":
            result = await self.location.random_encounter()
            if result:
                return result
        elif action == "open_treasure":
            result = await self.location.open_treasure()
            if result:
                return result

        return None

    async def display_menu(
        self,
        main_text: str,
        sub_text: str,
        background_image_url: str,
        movement_text: Dict[str, str],
    ):
        choices = self.get_choices()
        choice_texts = [choice.display_template for choice in choices]
        # capitalize the keys of the movement_text
        movement_text = {
            key.capitalize(): value for key, value in movement_text.items()
        }
        rm = ResponseManager()
        rm.set_game_response(
            main_text=main_text,
            sub_text=sub_text,
            menu_options=choice_texts,
            background_image_url=background_image_url,
            input_type="travel",
            travel_position=list(self.location.grid.player_pos),
            movement_text=movement_text,
            portrait_image_url=self.location.party.leader.portrait,
        )
        rm.send_game_response()
        choice = await rm.get_player_response()
        action = choices[choice_texts.index(choice)].action_template
        return await self.handle_choice(action)
