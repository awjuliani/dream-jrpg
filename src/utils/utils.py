from __future__ import annotations
from collections import Counter
import random
import yaml
from pathlib import Path


def create_unique_enemy_names(enemy_names):
    # Count the occurrences of each name
    name_counts = Counter(enemy_names)

    # Dictionary to keep track of how many of each name we've seen so far
    seen_counts = {name: 0 for name in name_counts}

    # List to store the unique names
    unique_names = []

    # Alphabet for suffixes
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for name in enemy_names:
        seen_counts[name] += 1

        # If there's only one of this name in total, use the name as is
        if name_counts[name] == 1:
            unique_names.append(name)
        else:
            # Otherwise, add a suffix
            suffix = alphabet[
                seen_counts[name] - 1
            ]  # -1 because we want A for the first duplicate
            unique_names.append(f"{name} ({suffix})")
    return unique_names


def calculate_hit_outcome(
    attacker_luck: int,
    defender_luck: int,
    base_crit_chance: float = 0.05,
    base_miss_chance: float = 0.05,
):
    """
    Calculate the outcome of an attack based on the luck of the attacker and defender.

    :param attacker_luck: The luck stat of the attacker
    :param defender_luck: The luck stat of the defender
    :param base_crit_chance: The base chance of a critical hit (default 5%)
    :param base_miss_chance: The base chance of a miss (default 5%)
    :return: A tuple (hit, critical) where hit is a boolean indicating if the attack hit,
             and critical is a boolean indicating if it was a critical hit
    """
    luck_difference = attacker_luck - defender_luck

    # Adjust crit and miss chances based on luck difference
    crit_chance = base_crit_chance + (
        luck_difference * 0.005
    )  # 0.5% per point of luck difference
    miss_chance = base_miss_chance - (
        luck_difference * 0.005
    )  # 0.5% per point of luck difference

    # Ensure probabilities are within [0, 1]
    crit_chance = max(0, min(crit_chance, 1))
    miss_chance = max(0, min(miss_chance, 1))

    # Determine the outcome
    roll = random.random()
    if roll < miss_chance:
        return False, False  # Miss
    elif roll > (1 - crit_chance):
        return True, True  # Critical hit
    else:
        return True, False  # Normal hit


def load_config():
    """Load configuration from config.yaml file"""
    config_path = Path(".config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
