from typing import Dict, List, Optional
from src.travel.base_location import Location


class MetaLocation:
    def __init__(
        self,
        name: str,
        description: str,
        part_a: Location,
        part_b: Location,
        coming_from: str = None,
        going_to: str = None,
    ):
        self.name = name
        self.description = description
        self.part_a = part_a
        self.part_b = part_b
        self.current_part = part_a
        self.coming_from = coming_from
        self.going_to = going_to

        # Internal linking of parts
        self.part_a.next_location = self.part_b.name
        self.part_b.previous_location = self.part_a.name
