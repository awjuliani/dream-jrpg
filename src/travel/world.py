from typing import List, Dict, Optional
from src.travel.base_location import Location
from src.travel.town_location import TownLocation
from src.travel.dungeon_location import DungeonLocation
from src.travel.field_location import FieldLocation
from src.core.player_party import PlayerParty
from src.api.llm import get_llm
from src.api.images import generate_title_background
from src.travel.meta_location import MetaLocation
import random

exit_sides = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}


class LocationFactory:
    def __init__(self):
        self._location_types = {
            "town": TownLocation,
            "dungeon": DungeonLocation,
            "field": FieldLocation,
        }

    def create_location(
        self,
        loc_info: Dict,
        loc_level: int,
        world_description: str,
        party: PlayerParty,
        coming_from: str = None,
        going_to: str = None,
    ) -> MetaLocation:
        loc_type = loc_info["type"]
        if loc_type not in self._location_types:
            raise ValueError(f"Unknown location type: {loc_type}")

        llm = get_llm()
        generator = getattr(llm, f"generate_{loc_type}_details")
        location_class = self._location_types[loc_type]

        # Get the full location details from LLM
        llm_location_info = generator(
            {
                "name": loc_info["name"],
                "description": loc_info["description"],
            },
            loc_level,
            world_description=world_description,
        )

        # Create part A location info
        part_a_info = llm_location_info.copy()
        part_a_info["name"] = (
            f"{llm_location_info['name']} ({coming_from.capitalize()})"
        )
        part_a_info["description"] = llm_location_info["part_a_description"]
        if loc_info.get("previous_location", None):
            part_a_info["previous_location"] = (
                loc_info.get("previous_location")
                + f" ({exit_sides[coming_from].capitalize()})"
            )
        else:
            part_a_info["previous_location"] = None
        part_a_info["next_location"] = (
            f"{llm_location_info['name']} ({exit_sides[coming_from].capitalize()})"
        )
        part_a_info["landmark"] = {}
        part_a_info["entrance_side"] = coming_from
        part_a_info["exit_side"] = exit_sides[coming_from]
        part_a_info["part"] = "A"

        # Create part B location info
        part_b_info = llm_location_info.copy()
        part_b_info["name"] = (
            f"{llm_location_info['name']} ({exit_sides[coming_from].capitalize()})"
        )
        part_b_info["description"] = llm_location_info["part_b_description"]
        part_b_info["previous_location"] = (
            f"{llm_location_info['name']} ({coming_from.capitalize()})"
        )
        part_b_info["next_location"] = (
            loc_info["next_location"] + f" ({exit_sides[going_to].capitalize()})"
        )
        part_b_info["landmark"] = loc_info["landmark"]
        part_b_info["entrance_side"] = coming_from
        part_b_info["exit_side"] = going_to
        part_b_info["part"] = "B"

        # Create both location parts
        part_a = location_class(part_a_info, party, loc_level)
        part_b = location_class(part_b_info, party, loc_level)

        return MetaLocation(
            name=llm_location_info["name"],
            description=llm_location_info["description"],
            part_a=part_a,
            part_b=part_b,
            coming_from=coming_from,
            going_to=going_to,
        )


class World:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.actual_locations: List[Location] = []
        self.possible_locations: List[Dict] = []
        self._location_factory = LocationFactory()
        self.title_screen_image = generate_title_background(self.name, self.description)
        self.actual_meta_locations: Dict[str, MetaLocation] = {}
        self.current_meta_location: Optional[MetaLocation] = None
        self.last_placed_y = 0  # Track the y-coordinate of the last placed location

    async def visit_current_location(self, party: PlayerParty):
        if self.current_meta_location:
            return await self.current_meta_location.current_part.visit(party)
        else:
            return None

    async def add_location(self, location_data: Dict):
        """Add a single location to the possible locations list."""
        location_info = {
            "name": location_data["name"],
            "description": location_data["description"],
            "type": location_data["type"],
            "landmark": location_data.get("landmark", {}),
            "previous_location": None,  # Will be set when linking
            "next_location": None,  # Will be set when linking
        }
        self.possible_locations.append(location_info)

    async def add_chapter_locations(self, chapter_data: Dict):
        """Add all locations from a chapter to the world."""
        # Extract locations from sub-chapters
        for sub_chapter in chapter_data["sub_chapters"]:
            location_data = sub_chapter["location"]
            # Find the landmark for this location
            if chapter_data["landmark"]["location"] == location_data["name"]:
                location_data["landmark"] = chapter_data["landmark"]
            else:
                location_data["landmark"] = None
            await self.add_location(location_data)

        # Link all locations after they've been added
        self._link_locations()

    def _link_locations(self):
        """Link locations in sequence."""
        # only link locations that are not already in the actual locations list
        locations = [
            loc
            for loc in self.possible_locations
            if loc["name"] not in self.list_locations
        ]

        for idx, location in enumerate(locations):
            # Set previous location
            if idx > 0:
                location["previous_location"] = locations[idx - 1]["name"]
            else:
                location["previous_location"] = None

            # Set next location
            if idx < len(locations) - 1:
                location["next_location"] = locations[idx + 1]["name"]
            else:
                location["next_location"] = None

        # If there are existing actual locations, link the last one
        # to the first new location
        if self.actual_locations and locations:
            last_actual = self.actual_locations[-1]
            first_new = locations[0]
            last_actual.next_location = first_new["name"]

    def update_current_location(self, party: PlayerParty) -> Location:
        """Create and add a new location if needed."""
        current_name = (
            self.current_meta_location.name if self.current_meta_location else None
        )
        next_loc = next(
            (
                loc
                for loc in self.possible_locations
                if loc["name"] not in self.actual_meta_locations
            ),
            None,
        )

        if not next_loc:
            return

        # Get the coming_from direction from the previous meta-location
        if current_name:
            prev_meta = self.actual_meta_locations[current_name]
            coming_from = exit_sides[prev_meta.going_to]
        else:
            coming_from = "south"

        # Sample a random going_to direction to exclude the coming_from direction
        going_to = random.choice(["west", "east", "north", "south"])
        while going_to == coming_from:
            going_to = random.choice(["west", "east", "north", "south"])

        # Create new meta-location with directional parameters
        battle_locations = len(self.list_fields) + len(self.list_dungeons)
        loc_level = int(battle_locations * 1.5) + 5

        new_meta = self._location_factory.create_location(
            next_loc,
            loc_level,
            self.description,
            party,
            coming_from=coming_from,
            going_to=going_to,
        )

        # Link with previous meta-location if it exists
        if current_name:
            prev_meta = self.actual_meta_locations[current_name]
            prev_meta.part_b.next_location = new_meta.part_a.name
            new_meta.part_a.previous_location = prev_meta.part_b.name

        self.actual_meta_locations[new_meta.name] = new_meta
        self.current_meta_location = new_meta

    def advance_location(self, party: PlayerParty):
        """Handle advancement between locations and meta-locations"""
        current = self.current_meta_location.current_part

        if current == self.current_meta_location.part_a:
            # Moving to part B of current meta-location
            self.current_meta_location.current_part = self.current_meta_location.part_b
        else:
            # Moving to next meta-location
            next_name = current.next_location.split(" (")[0]
            if next_name not in self.actual_meta_locations:
                self.update_current_location(party)
            else:
                self.current_meta_location = self.actual_meta_locations[next_name]

    def retreat_location(self, party: PlayerParty):
        """Handle retreat between locations and meta-locations"""
        current = self.current_meta_location.current_part

        if current == self.current_meta_location.part_b:
            # Moving to part A of current meta-location
            self.current_meta_location.current_part = self.current_meta_location.part_a
        else:
            # Moving to previous meta-location
            prev_name = current.previous_location.split(" (")[0]
            self.current_meta_location = self.actual_meta_locations[prev_name]
            self.current_meta_location.current_part = self.current_meta_location.part_b

    def get_location_by_name(self, name: str) -> Location:
        for location in self.actual_locations:
            if location.name.lower() == name.lower():
                return location
        return None

    def get_locations_of_type(self, location_type: type) -> List[Location]:
        return [loc for loc in self.actual_locations if isinstance(loc, location_type)]

    def get_location_type(self, location: Location) -> str:
        return location.__class__.__name__.lower().replace("location", "")

    @property
    def list_locations(self):
        return [loc.name for loc in self.actual_locations]

    @property
    def list_towns(self):
        return [loc.name for loc in self.get_locations_of_type(TownLocation)]

    @property
    def list_fields(self):
        return [loc.name for loc in self.get_locations_of_type(FieldLocation)]

    @property
    def list_dungeons(self):
        return [loc.name for loc in self.get_locations_of_type(DungeonLocation)]

    @property
    def basic_info(self):
        return f"{self.name}: {self.description}"

    @property
    def current_location(self):
        return self.current_meta_location.current_part

    @property
    def next_location(self):
        return self.current_meta_location.current_part.next_location

    @property
    def previous_location(self):
        return self.current_meta_location.current_part.previous_location
