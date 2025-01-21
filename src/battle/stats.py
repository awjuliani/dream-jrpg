from dataclasses import dataclass
from src.api.llm import get_llm
from typing import Dict


@dataclass
class CharacterStats:
    max_hp: int = 50
    max_mp: int = 25
    attack: int = 10
    defense: int = 10
    intelligence: int = 10
    wisdom: int = 10
    speed: int = 10
    luck: int = 10
    alive: bool = True
    sp: int = 0
    max_sp: int = 3

    def __post_init__(self):
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.on_death = None  # Callback function to be set by the Character class

    def __str__(self) -> str:
        left_column = 15
        right_column = 15
        column_spacing = 5  # Number of spaces between columns
        hp_str = f"{self.hp}/{self.max_hp}"
        mp_str = f"{self.mp}/{self.max_mp}"
        space = " " * column_spacing
        return (
            f"{'HP:':<{left_column}} {hp_str:>{right_column}}{space}{'MP:':<{left_column}} {mp_str:>{right_column}}\n"
            f"{'Attack:':<{left_column}} {self.attack:>{right_column}}{space}{'Defense:':<{left_column}} {self.defense:>{right_column}}\n"
            f"{'Intelligence:':<{left_column}} {self.intelligence:>{right_column}}{space}{'Wisdom:':<{left_column}} {self.wisdom:>{right_column}}\n"
            f"{'Speed:':<{left_column}} {self.speed:>{right_column}}{space}{'Luck:':<{left_column}} {self.luck:>{right_column}}"
        )

    def to_dict(self):
        return {
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "max_mp": self.max_mp,
            "sp": self.sp,
            "max_sp": self.max_sp,
            "attack": self.attack,
            "defense": self.defense,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "speed": self.speed,
            "luck": self.luck,
            "alive": self.alive,
        }

    def hp_change(self, value: int):
        true_value = max(-self.hp, min(value, self.max_hp - self.hp))
        self.hp += true_value
        self.check_dead()
        return true_value

    def mp_change(self, value: int):
        true_value = max(-self.mp, min(value, self.max_mp - self.mp))
        self.mp += true_value
        return true_value

    def check_dead(self):
        if self.hp <= 0:
            self.alive = False
            self.hp = 0
            if self.on_death:
                self.on_death()

    def sp_change(self, amount: int) -> int:
        old_sp = self.sp
        self.sp = max(0, min(self.max_sp, self.sp + amount))
        return self.sp - old_sp

    @classmethod
    def from_dict(cls, data: Dict[str, int]):
        stats = cls(
            max_hp=data["max_hp"],
            max_mp=data["max_mp"],
            attack=data["attack"],
            defense=data["defense"],
            intelligence=data["intelligence"],
            wisdom=data["wisdom"],
            speed=data["speed"],
            luck=data["luck"],
            sp=data["sp"],
            max_sp=data["max_sp"],
        )
        stats.hp = data["hp"]
        stats.mp = data["mp"]
        stats.alive = data["alive"]
        return stats


BASE_STATS = {
    "max_hp": 100,
    "max_mp": 50,
    "attack": 10,
    "defense": 10,
    "intelligence": 10,
    "wisdom": 10,
    "speed": 10,
    "luck": 10,
}

BIAS_MULTIPLIERS = [0.5, 0.75, 1.0, 1.25, 1.5]


def calculate_stat(base: int, bias: int, level: int) -> int:
    bias_multiplier = BIAS_MULTIPLIERS[int(bias)]
    return int(base * bias_multiplier * (level / 2))


def generate_stats(biases: Dict[str, int], level: int) -> Dict[str, int]:
    return {
        stat: calculate_stat(BASE_STATS[stat], bias, level)
        for stat, bias in biases.items()
    }


def calculate_xp_for_level(level: int) -> int:
    return int(100 * (level**1.5))


def calculate_xp_gain(player_level: int, enemy_level: int) -> int:
    level_difference = enemy_level - player_level
    base_xp = 10 * enemy_level
    multiplier = 1 + (0.1 * level_difference)
    return max(1, int(base_xp * multiplier))


def stats_from_llm(level: int, job_class: str) -> CharacterStats:
    biases = get_llm().generate_stats(job_class=job_class)
    stat_values = generate_stats(biases, level)
    return CharacterStats(**stat_values)
