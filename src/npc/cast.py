from typing import Optional, List
from src.npc.npc import NPC
from src.npc.boss_npc import BossNPC
from src.npc.ally_npc import AllyNPC
from src.api.llm import get_llm


class NPCFactory:
    """
    Factory class for creating different types of NPCs.
    """

    @staticmethod
    def create_npc(npc_data: dict, current_location: dict, story_level: int) -> NPC:
        """
        Creates an NPC instance based on the NPC type specified in the data.

        Args:
            npc_data: Dictionary containing NPC data
            current_location: The location where the NPC should be placed

        Returns:
            An instance of the appropriate NPC class
        """
        npc_type = npc_data.get("type", "regular")

        if npc_type == "boss":
            return BossNPC(
                npc_data, current_location=current_location, story_level=story_level
            )
        elif npc_type == "ally":
            return AllyNPC(
                npc_data, current_location=current_location, story_level=story_level
            )
        else:
            return NPC(
                npc_data, current_location=current_location, story_level=story_level
            )


class CastManager:
    """
    Manages a collection of NPCs in the game.
    Implemented as a singleton to ensure only one cast exists.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CastManager, cls).__new__(cls)
            cls._instance._npcs = []
            cls._instance.npc_factory = NPCFactory()
        return cls._instance

    def __init__(self):
        # Initialize only if this is the first time
        if not hasattr(self, "_npcs"):
            self._npcs: List[NPC] = []

    def make_new_npc(
        self,
        npc_name,
        example_dialogue,
        location,
        location_description,
        npc_type="story",
    ):
        loc_info = {"name": location, "description": location_description}
        npc_data = get_llm().generate_npc_data(
            npc_name, example_dialogue, loc_info, 1, npc_type
        )["npc"]
        npc_data["type"] = npc_type
        npc = self.npc_factory.create_npc(npc_data, loc_info, 1)
        self.add_npc(npc)
        return npc

    def add_npc(self, npc: NPC) -> None:
        """
        Adds a new NPC to the cast.

        Args:
            npc: The NPC object to add
        """
        self._npcs.append(npc)

    def get_npc_by_name(self, name: str) -> Optional[NPC]:
        """
        Retrieves an NPC by their name. Matches either full name or first name.

        Args:
            name: The name or first name of the NPC to find

        Returns:
            The NPC if found, None otherwise
        """
        search_name = name.lower()
        for npc in self._npcs:
            npc_full_name = npc.name.lower()
            npc_first_name = npc_full_name.split()[0]
            if npc_full_name == search_name or npc_first_name == search_name:
                return npc
        return None

    def get_all_npcs(self) -> List[NPC]:
        """
        Returns all NPCs in the cast.

        Returns:
            A list of all NPCs
        """
        return self._npcs.copy()

    def remove_npc(self, name: str) -> bool:
        """
        Removes an NPC from the cast by name.

        Args:
            name: The name of the NPC to remove

        Returns:
            True if NPC was found and removed, False otherwise
        """
        npc = self.get_npc_by_name(name)
        if npc:
            self._npcs.remove(npc)
            return True
        return False

    def clear(self) -> None:
        """
        Removes all NPCs from the cast.
        Useful when starting a new game.
        """
        self._npcs.clear()

    def get_npcs_by_type(self, npc_type: str) -> List[NPC]:
        """
        Retrieves all NPCs of a specific type.

        Args:
            npc_type: The type of NPCs to find

        Returns:
            A list of NPCs matching the specified type
        """
        return [npc for npc in self._npcs if npc.type.lower() == npc_type.lower()]

    def get_npcs_by_location(self, location_name: str) -> List[NPC]:
        """
        Retrieves all NPCs in a specific location.

        Args:
            location_name: The name of the location to find NPCs in

        Returns:
            A list of NPCs in the specified location
        """
        return [
            npc
            for npc in self._npcs
            if npc.current_location["name"].lower() == location_name.lower()
        ]


def get_cast() -> CastManager:
    """
    Returns the singleton instance of CastManager.
    """
    return CastManager()
