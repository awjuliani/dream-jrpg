from abc import ABC, abstractmethod
from src.core.player_party import PlayerParty
from src.battle.battle import Battle
from src.core.enemies import make_enemy, EnemyParty
import numpy as np
import copy
from typing import Dict, Tuple, List, Optional, Any
from src.travel.menu_handler import MenuHandler
from src.api.images import generate_background_image, generate_landmark_image
from src.travel.location_grid import LocationGrid, GridNode
from src.api.llm import get_llm
from src.game.response_manager import print_event_text
import random
from src.core.items import ItemManager
from src.npc.cast import get_cast
from src.core.cutscene import cutscene
from src.core.story import StoryEvent


class Location(ABC):
    def __init__(self, data, party: PlayerParty, story_level: int):
        self._data = data
        self.name = data["name"]
        self.description = data["description"]
        self.previous_location = data["previous_location"]
        self._next_location = data["next_location"]
        self.landmark = data["landmark"]
        self.border_messages = data["border_messages"]
        self.entrance_side = data["entrance_side"]
        self.exit_side = data["exit_side"]
        self.part = data["part"]
        self.party: PlayerParty = party
        self.story_level = story_level
        self.enemy_types = []
        self.enemy_cache = {}  # New: cache for generated enemies
        self.menu_handler: Optional[MenuHandler] = None
        self.grid = LocationGrid()
        self.nav_text_cache = {}  # Cache for navigation text
        self.setup_grid()
        self.visited = False
        self.unlock_exit = False

        # Generate background images for main location and sub-locations
        self.background_image_url = generate_background_image(
            self.name, self.description
        )

    async def move(self, direction: str):
        """Handle movement and potential location transitions"""
        current_pos = self.grid.player_pos

        # Check for travel to previous location
        if direction.lower() == self.entrance_side.lower() and self.previous_location:
            # For east/west entrances, check middle row (1) and appropriate edge column
            if self.entrance_side.lower() in ["east", "west"]:
                if current_pos[0] == 1 and current_pos[1] == (
                    2 if self.entrance_side.lower() == "east" else 0
                ):
                    return self.previous_location
            # For north/south entrances, check middle column (1) and appropriate edge row
            elif self.entrance_side.lower() in ["north", "south"]:
                if current_pos[1] == 1 and current_pos[0] == (
                    0 if self.entrance_side.lower() == "north" else 2
                ):
                    return self.previous_location

        # Check for travel to next location
        if (
            direction.lower() == self.exit_side.lower()
            and self.next_location
            and self.unlock_exit
        ):
            # For east/west exits, check middle row (1) and appropriate edge column
            if self.exit_side.lower() in ["east", "west"]:
                if current_pos[0] == 1 and current_pos[1] == (
                    2 if self.exit_side.lower() == "east" else 0
                ):
                    return self.next_location
            # For north/south exits, check middle column (1) and appropriate edge row
            elif self.exit_side.lower() in ["north", "south"]:
                if current_pos[1] == 1 and current_pos[0] == (
                    0 if self.exit_side.lower() == "north" else 2
                ):
                    return self.next_location

        # If not traveling to a new location, perform normal movement
        self.grid.move(direction)

    async def open_treasure(self):
        item_manager = ItemManager()
        item_name = random.choice(item_manager.item_list)
        item = item_manager.deserialize_item(item_name)
        self.party.inventory.append(item)
        base_text = f"The party of {self.party.list_names} open a treasure chest. Inside they find: {item.name} ({item.description})"
        fancy_text = get_llm().generate_action_text(base_text)
        await print_event_text(
            "Treasure acquired!",
            fancy_text,
            portrait_image_url=item.portrait,
        )
        self.grid.remove_node(self.grid.player_pos)
        self._clear_nav_cache()

    def setup_grid(self):
        """Initialize the location's grid with common nodes"""
        # Set current player position based on entrance_side
        self.grid.player_pos = self.direction_to_node(self.entrance_side)

        # Let subclasses add their specific nodes
        self._setup_specific_nodes()

        # Add NPCs to the grid
        self._add_npc_nodes()

        # Add key objects to the grid
        self._add_landmark_nodes()

    def _get_coordinates(self, node_data: Dict) -> Tuple[int, int]:
        """Extract coordinates from node data"""
        return (node_data["coordinates"]["row"], node_data["coordinates"]["col"])

    def direction_to_node(self, direction: str) -> Tuple[int, int]:
        """Convert a direction to a node position"""
        if direction == "west":
            return (1, 0)
        elif direction == "east":
            return (1, 2)
        elif direction == "north":
            return (0, 1)
        elif direction == "south":
            return (2, 1)

    def _get_available_coordinates(self) -> List[Tuple[int, int]]:
        """Get all available (empty) coordinates in the grid."""
        return self.grid.get_available_coordinates()

    def _add_enemy_nodes(self, num_enemies: int):
        open_coords = self._get_available_coordinates()

        # Randomly select num_enemies coordinates
        if open_coords:
            selected_coords = random.sample(
                open_coords, min(num_enemies, len(open_coords))
            )

            # Add enemy nodes at selected coordinates
            for coords in selected_coords:
                self.grid.add_node(
                    pos=coords,
                    node=GridNode(
                        name="enemy",
                        description="",
                        node_type="enemy",
                    ),
                )

        # Clear cache when adding enemy nodes
        self._clear_nav_cache()

    def _add_node(self, node_type: str, node_data: Dict, coords: Tuple[int, int]):
        """Helper method to add a node to the grid"""
        if not node_data:
            return

        name = node_data.get("name", node_type.capitalize())
        description = node_data.get("description", f"")

        self.grid.add_node(
            coords, GridNode(name=name, description=description, node_type=node_type)
        )

        # Clear cache when adding nodes
        self._clear_nav_cache()

    @abstractmethod
    def _setup_specific_nodes(self):
        """Subclasses should implement this to add their specific nodes"""
        pass

    async def visit(self, party):
        if not self.visited:
            self.visited = True
        self.party = party

        # check if there are any events to trigger
        event_triggered = await self.party.story_manager.check_location_trigger(
            self.name, self.part
        )
        if event_triggered:
            await self.party.story_manager.trigger_event(
                self.party.story_manager.next_event,
                self.name,
                self.description,
                self.background_image_url,
                player_party=self.party,
            )

        # Reset enemy nodes if needed
        self._reset_enemy_nodes()

        while True:
            # check if exit should be unlocked
            if (
                party.story_manager.next_event.location["name"]
                == self.next_location.split(" (")[0]
            ):
                self.unlock_exit = True

            current_node = self.grid.get_current_node()
            node_key = (self.grid.player_pos, current_node.name)

            # Handle NPC interaction if current node is an NPC
            if current_node.node_type == "npc":
                npc = current_node.data.get("npc")
                if npc:
                    # You can add NPC interaction logic here
                    pass

            # Check if we need to generate new navigation text
            if node_key not in self.nav_text_cache:
                points_of_interest = self._get_points_of_interest()
                move_directions, look_directions = self._get_valid_directions()
                self.nav_text_cache[node_key] = get_llm().generate_navigation_text(
                    location_name=self.name,
                    location_description=self.description,
                    party_members=[
                        character.name for character in self.party.characters
                    ],
                    current_position=self.grid.player_pos,
                    points_of_interest=points_of_interest,
                    move_directions=move_directions,
                    look_directions=look_directions,
                    border_messages=self.border_messages,
                )

            # Use cached navigation text
            nav_text = self.nav_text_cache[node_key]

            result = await self.menu_handler.display_menu(
                main_text=f"{self.name}",
                sub_text=nav_text["current_situation"],
                movement_text=nav_text["directions"],
                background_image_url=self.background_image_url,
            )
            if result:
                return result

            # After handling an event, check if chapter is complete
            if not self.party.story_manager.future_events:
                if (
                    self.party.story_manager.current_sub_chapter
                    < len(
                        self.party.story_manager.chapter_overviews[
                            self.party.story_manager.current_chapter
                        ]["sub_chapters"]
                    )
                    - 1
                ):
                    self.party.story_manager.current_sub_chapter += 1
                    self.party.story_manager.generate_sub_chapter_events()
                else:
                    return "chapter_complete"

    def _reset_enemy_nodes(self):
        """Base implementation to reset enemy nodes"""
        # Clear existing enemy nodes
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                if self.grid.grid[r, c].node_type == "enemy":
                    self.grid.remove_node((r, c))

        # Add new enemy nodes - number determined by subclasses
        if hasattr(self, "num_enemies"):
            self._add_enemy_nodes(self.num_enemies)

    @property
    def basic_info(self):
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
        }

    def generate_enemy_info(self, enemy_type: Dict) -> Dict:
        if self.type == "field":
            enemy_lvl = random.randint(self.story_level - 4, self.story_level + 1)
        else:
            enemy_lvl = random.randint(self.story_level - 3, self.story_level + 2)
        return {
            "type": enemy_type,
            "level": enemy_lvl,
        }

    def get_enemy_key(self, enemy_type: Dict) -> frozenset:
        """Create a hashable key from the enemy type dictionary"""
        return frozenset(enemy_type.items())

    def get_or_create_enemy(self, enemy_type: Dict):
        enemy_key = self.get_enemy_key(enemy_type)
        if enemy_key not in self.enemy_cache:
            enemy_info = self.generate_enemy_info(enemy_type)
            self.enemy_cache[enemy_key] = make_enemy(
                self.basic_info, enemy_info["level"], False, enemy_type
            )
        return copy.deepcopy(self.enemy_cache[enemy_key])

    async def random_encounter(self):
        if self.type == "field":
            num_enemies = np.random.randint(1, 3)
        else:
            num_enemies = np.random.randint(1, 4)
        enemies = [
            self.get_or_create_enemy(np.random.choice(self.enemy_types))
            for _ in range(num_enemies)
        ]
        enemy_party = EnemyParty(enemies)
        context = f"Battle type: ambush; Location: {self.name} ({self.description})"
        result = await Battle(
            self.party,
            enemy_party,
            background_image_url=self.background_image_url,
            context=context,
        ).start()
        if result == "party_defeated":
            return "game_over"
        elif result == "party_victory":
            self.grid.remove_node(self.grid.player_pos)
            self._clear_nav_cache()
        else:
            pass

    def __getstate__(self):
        state = self.__dict__.copy()
        state["party"] = None  # Don't pickle the party reference
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # The party will need to be re-assigned after unpickling

    def _get_points_of_interest(self):
        """Get all points of interest in the grid"""
        return [
            {
                "position": self.grid.relative_position((r, c)),
                "name": node.name,
                "type": node.node_type,
                "description": node.description,
            }
            for r, c in self.grid.get_all_positions()
            if (node := self.grid.grid[r, c]).name
        ]

    # Add this method to clear cache when nodes change
    def _clear_nav_cache(self):
        """Clear the navigation text cache when the grid changes"""
        self.nav_text_cache.clear()

    def _add_treasure_nodes(self, num_nodes: int):
        open_coords = self._get_available_coordinates()

        if open_coords:
            selected_coords = random.sample(
                open_coords, min(num_nodes, len(open_coords))
            )

            for coords in selected_coords:
                self.grid.add_node(
                    pos=coords,
                    node=GridNode(
                        name="Treasure Chest",
                        description="A chest filled with treasure.",
                        node_type="treasure",
                    ),
                )

        self._clear_nav_cache()

    def _add_npc_nodes(self):
        """Add NPCs that belong in this location to random available nodes"""
        cast_manager = get_cast()
        location_npcs = cast_manager.get_npcs_by_location(self.name.split(" (")[0])
        open_coords = self._get_available_coordinates()
        if not location_npcs or not open_coords or self.part == "A":
            return

        for npc in location_npcs:
            # Place boss at exit (1, 0), others at random spots
            coords = (1, 0) if npc.type == "boss" else random.choice(open_coords)

            self.grid.add_node(
                pos=coords,
                node=GridNode(
                    name=npc.name,
                    description=f"{npc.name} is here.",
                    node_type="npc",
                    data={"npc": npc},
                ),
            )

            # Remove used coordinates from available spots
            if coords in open_coords:
                open_coords.remove(coords)

            if not open_coords:  # No more spots available
                break

        self._clear_nav_cache()

    def _clear_current_node(self):
        """Helper to remove current node and clear navigation cache"""
        self.grid.remove_node(self.grid.player_pos)
        self._clear_nav_cache()

    async def talk_to_npc(self):
        """Handle interaction with an NPC at the current position"""
        current_node = self.grid.get_current_node()
        if current_node.node_type != "npc" or "npc" not in current_node.data:
            return

        npc = current_node.data["npc"]
        trigger_event = await self.party.story_manager.check_npc_trigger(
            npc.name, npc.type, self.part
        )
        if trigger_event:
            # Trigger the story event which will handle conversations/battles through cutscene
            result = await self.party.story_manager.trigger_event(
                self.party.story_manager.next_event,
                self.name,
                self.description,
                self.background_image_url,
                player_party=self.party,
            )

            if result == "game_over":
                return "game_over"

            # Check if we need to clear the NPC from the location
            current_node = self.grid.get_current_node()
            if current_node and current_node.node_type == "npc":
                npc = current_node.data.get("npc")
                if npc and (npc.type == "ally" or npc.type == "boss"):
                    if (npc.type == "ally" and npc.recruited) or (
                        npc.type == "boss" and npc.defeated
                    ):
                        self._clear_current_node()
        else:
            # Handle casual conversation when no story trigger
            scene_npcs = [f"{npc.name} ({npc.description})"]  # The NPC we're talking to
            scene_npcs.extend(
                f"{char.name} ({char.description})" for char in self.party.characters
            )  # Add party members

            # Generate and display a casual conversation
            await cutscene(
                StoryEvent(
                    location=self.name,
                    event_text=f"A casual conversation with {npc.name}",
                    trigger={"type": "none", "value": "none"},
                    completed=True,
                ),
                self.name,
                self.description,
                scene_npcs,
                self.background_image_url,
                past_events=self.party.story_manager.past_events,
                thematic_style=self.party.story_manager.thematic_style,
                conversation_length="short",
            )

    def _add_landmark_nodes(self):
        """Add key objects to the middle of the grid"""
        if not self.landmark:
            return

        # Add landmark to center position (1,1)
        bg_image_url = generate_landmark_image(
            self.name,
            self.description,
            self.landmark["name"],
            self.landmark["description"],
        )
        self.grid.add_node(
            pos=(1, 1),
            node=GridNode(
                name=self.landmark["name"],
                description=self.landmark["description"],
                node_type="landmark",
                data={"landmark": self.landmark},
                background_image_url=bg_image_url,
            ),
        )

        # Clear navigation cache after adding landmark
        self._clear_nav_cache()

    async def inspect_landmark(self):
        """Handle interaction with a landmark at the current position"""
        current_node = self.grid.get_current_node()
        if current_node.node_type != "landmark" or "landmark" not in current_node.data:
            return

        landmark = current_node.data["landmark"]

        # Check if there are any story triggers from this inspection
        if await self.party.story_manager.check_landmark_trigger(landmark["name"]):
            await self.party.story_manager.trigger_event(
                self.party.story_manager.next_event,
                self.name,
                self.description,
                current_node.background_image_url,
                player_party=self.party,
            )
            self._clear_current_node()
        else:
            await print_event_text(
                f"Inspecting {landmark['name']}",
                landmark["description"],
                background_image_url=current_node.background_image_url,
            )

    @property
    def next_location(self) -> str:
        """Get the next location name"""
        return self._next_location

    @next_location.setter
    def next_location(self, value: str):
        """Set the next location name and update internal data"""
        self._next_location = value
        self._data["next_location"] = value

        # Update the exit node in the grid
        if hasattr(
            self, "grid"
        ):  # Check in case this is called before grid initialization
            # Update exit coordinates in _data to match current exit node
            exit_coords = None
            for r in range(self.grid.rows):
                for c in range(self.grid.cols):
                    node = self.grid.grid[r, c]
                    if node and node.node_type == "exit":
                        exit_coords = {"row": r, "col": c}
                        break

            if exit_coords:
                self._data["exit"] = {"coordinates": exit_coords}
                # Remove old exit node and add new one
                self._add_exit_node()

        # Clear navigation cache since available paths have changed
        self._clear_nav_cache()

    async def look_direction(self, direction: str):
        """Display the border message for the given direction"""
        direction = direction.lower()
        if direction in self.border_messages:
            await print_event_text(
                f"Looking {direction}...",
                self.border_messages[direction],
                background_image_url=self.background_image_url,
            )

    def _get_valid_directions(self) -> Tuple[List[str], List[str]]:
        """Get valid movement and look directions based on player position"""
        move_directions = []
        look_directions = []

        # Check each direction
        if self.grid.player_pos[0] > 0:
            move_directions.append("north")
        else:
            look_directions.append("north")

        if self.grid.player_pos[0] < self.grid.rows - 1:
            move_directions.append("south")
        else:
            look_directions.append("south")

        if self.grid.player_pos[1] > 0:
            move_directions.append("west")
        else:
            look_directions.append("west")

        if self.grid.player_pos[1] < self.grid.cols - 1:
            move_directions.append("east")
        else:
            look_directions.append("east")

        return move_directions, look_directions
