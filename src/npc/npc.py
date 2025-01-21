from typing import List, Dict, Optional
from src.api.images import generate_npc_portrait


class NPC:
    NPC_TYPE_STORY = "story"
    NPC_TYPE_SHOP = "shop"
    NPC_TYPE_INN = "innkeeper"
    NPC_TYPE_ENEMY = "enemy"
    NPC_TYPE_ALLY = "ally"
    NPC_TYPE_BOSS = "boss"

    def __init__(
        self,
        npc_dict: Dict[str, any],
        current_location: Dict[str, any],
        story_level: int = 1,
        portrait: Optional[str] = None,
    ):
        self.name: str = npc_dict["name"]
        self.description: str = npc_dict["description"]
        self.type: str = npc_dict["type"]
        self.job_class: str = npc_dict["job_class"]
        self.backstory: str = npc_dict["backstory"]
        self.current_location: Optional[dict] = current_location
        self.story_level: int = story_level
        if portrait is None:
            self.portrait = generate_npc_portrait(
                self.name, self.description, self.job_class
            )
        else:
            self.portrait = portrait
        self.recruited: bool = False
        self.defeated: bool = False

    @property
    def basic_info(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
        }

    def get_valid_outcomes(self) -> List[str]:
        """Returns the list of valid outcomes based on NPC type."""
        base_outcomes = ["end"]
        type_outcomes = {
            self.NPC_TYPE_STORY: ["end", "info_obtained"],
            self.NPC_TYPE_SHOP: ["end", "shop_discount"],
            self.NPC_TYPE_INN: ["end", "rest_discount"],
            self.NPC_TYPE_ENEMY: ["battle", "battle_intimidated"],
            self.NPC_TYPE_BOSS: ["battle", "battle_intimidated"],
            self.NPC_TYPE_ALLY: ["recruit_failure", "recruit_success"],
        }
        return base_outcomes + type_outcomes.get(self.type, [])
