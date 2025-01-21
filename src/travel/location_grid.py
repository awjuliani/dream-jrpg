from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class GridNode:
    name: str
    description: str
    node_type: str  # 'entrance', 'exit', 'shop', 'npc', 'boss', 'treasure'
    data: Optional[Dict] = None
    is_visited: bool = False
    background_image_url: str = None


class LocationGrid:
    def __init__(self, size: Tuple[int, int] = (3, 3)):
        self.rows, self.cols = size
        self.grid = np.array(
            [
                [
                    GridNode(name="", description="", node_type="empty")
                    for _ in range(self.cols)
                ]
                for _ in range(self.rows)
            ]
        )
        self.player_pos = (0, 0)

    def add_node(self, pos: Tuple[int, int], node: GridNode):
        if 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols:
            self.grid[pos] = node

    def remove_node(self, pos: Tuple[int, int]):
        if 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols:
            self.grid[pos] = GridNode(name="", description="", node_type="empty")

    def get_current_node(self) -> Optional[GridNode]:
        return self.grid[self.player_pos]

    def get_available_moves(self) -> List[str]:
        moves = []
        row, col = self.player_pos

        if row > 0:  # Can move north if not at top edge
            moves.append("North")
        if row < self.rows - 1:  # Can move south if not at bottom edge
            moves.append("South")
        if col > 0:  # Can move west if not at left edge
            moves.append("West")
        if col < self.cols - 1:  # Can move east if not at right edge
            moves.append("East")

        return moves

    def get_all_moves(self) -> List[str]:
        return ["North", "South", "East", "West"]

    def move(self, direction: str) -> bool:
        row, col = self.player_pos
        new_pos = {
            "North": (row - 1, col),
            "South": (row + 1, col),
            "West": (row, col - 1),
            "East": (row, col + 1),
        }.get(direction)

        if new_pos and 0 <= new_pos[0] < self.rows and 0 <= new_pos[1] < self.cols:
            self.player_pos = new_pos
            return True
        return False

    def relative_position(self, position: Tuple[int, int]) -> dict:
        """
        Calculate the relative direction from the player's position to the target position.
        Also returns how far (Euclidean distance) the position is from the player's position.

        :param position: A tuple of (row, col) for the target position.
        :return: A dictionary containing:
            {
                "direction": str,  # e.g. "north", "south-east", or "here"
                "distance": float,  # Euclidean distance between current position and target
            }
        """
        row_diff = position[0] - self.player_pos[0]
        col_diff = position[1] - self.player_pos[1]

        if row_diff == 0 and col_diff == 0:
            return {"direction": "here", "distance": 0.0}

        directions = {
            (-1, -1): "north-west",
            (-1, 0): "north",
            (-1, 1): "north-east",
            (0, -1): "west",
            (0, 1): "east",
            (1, -1): "south-west",
            (1, 0): "south",
            (1, 1): "south-east",
        }

        # Convert differences to direction indicators (-1, 0, or 1)
        key = (
            -1 if row_diff < 0 else 1 if row_diff > 0 else 0,
            -1 if col_diff < 0 else 1 if col_diff > 0 else 0,
        )
        direction = directions[key]

        # Calculate Euclidean distance
        distance = (row_diff**2 + col_diff**2) ** 0.5

        return {"direction": direction, "distance": distance}

    def get_available_coordinates(self) -> List[Tuple[int, int]]:
        """Get all available (empty) coordinates in the grid."""
        # Get all possible coordinates
        all_coords = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        # Filter to only open nodes (those without a name)
        return [(r, c) for r, c in all_coords if self.grid[r, c].name == ""]

    def get_all_positions(self) -> List[Tuple[int, int]]:
        """Get positions of all non-empty nodes in the grid."""
        return [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if self.grid[r, c].name != ""
        ]
