class Element:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Element({self.name})"


# Define elemental instances
FIRE = Element("Fire")
WATER = Element("Water")
THUNDER = Element("Thunder")
ICE = Element("Ice")
EARTH = Element("Earth")
WIND = Element("Wind")
LIGHT = Element("Light")
DARK = Element("Dark")
NONE = Element("None")

ELEMENT_CLASSES = {
    "Fire": FIRE,
    "Water": WATER,
    "Thunder": THUNDER,
    "Ice": ICE,
    "Earth": EARTH,
    "Wind": WIND,
    "Light": LIGHT,
    "Dark": DARK,
    "None": NONE,
}

ELEMENT_LIST = list(ELEMENT_CLASSES.keys())

deserialize_element = lambda name: ELEMENT_CLASSES.get(name, NONE)

# Define elemental relationships
ELEMENTAL_WEAKNESSES = {
    FIRE: WATER,
    WATER: THUNDER,
    THUNDER: EARTH,
    ICE: FIRE,
    EARTH: WIND,
    WIND: ICE,
    LIGHT: DARK,
    DARK: LIGHT,
}

ELEMENTAL_RESISTANCES = {
    FIRE: ICE,
    WATER: FIRE,
    THUNDER: WIND,
    ICE: WATER,
    EARTH: THUNDER,
    WIND: EARTH,
}


def calculate_elemental_damage(base_damage, attacker_element, defender_element):
    """
    Calculate the elemental damage multiplier and provide an explanation.

    :param base_damage: The base damage of the attack
    :param attacker_element: The Element of the attacker or spell
    :param defender_element: The Element of the defender
    :return: A tuple of (damage value, explanation string)
    """
    # If either element is NONE, return base damage with explanation
    if attacker_element == NONE or defender_element == NONE:
        return base_damage, "No elemental interaction."

    if ELEMENTAL_WEAKNESSES.get(defender_element) == attacker_element:
        damage = int(base_damage * 2)
        explanation = f"{defender_element} is weak against {attacker_element}!"
    elif ELEMENTAL_RESISTANCES.get(defender_element) == attacker_element:
        damage = int(base_damage * 0.5)
        explanation = f"{defender_element} resists {attacker_element}!"
    elif (attacker_element == LIGHT and defender_element == DARK) or (
        attacker_element == DARK and defender_element == LIGHT
    ):
        damage = int(base_damage * 1.5)
        explanation = f"{attacker_element} is strong against {defender_element}!"
    else:
        damage = base_damage
        explanation = "Normal damage."

    return damage, explanation


def get_weakness(element):
    """Get the element that the given element is weak against."""
    return ELEMENTAL_WEAKNESSES.get(element)


def get_resistance(element):
    """Get the element that the given element is resistant to."""
    return ELEMENTAL_RESISTANCES.get(element)


def get_strong_against(element):
    """Get the elements that the given element is strong against."""
    return [e for e, w in ELEMENTAL_WEAKNESSES.items() if w == element]
