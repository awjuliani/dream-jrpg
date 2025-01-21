from src.api.prompts.base import Prompt


class CharacterPrompts:
    GENERATE_ENEMY = Prompt(
        """
        Generate an enemy/boss character for a JRPG. Use the following information:
        Name: {base_name}
        Description: {base_description}
        Enemy Type: {enemy_type}
        Level: {level}
        Location: The enemy is located in {location_name}, which is described as: {location_description}.
        
        Valid possible spells: {spells}
        Valid possible elements: {elements}

        Based on the provided information, generate:
        1. A character class (variable: 'job_class')
        2. A unique attack name (variable: 'attack')
        3. One to three spell(s) from the possible spells list (list variable: 'spells')
        4. An element that best fits the enemy (variable: 'element')
        
        Guidelines:
        - If no name and description are provided, create them based on the enemy type and location.
        - Ensure the job class, attack, spells, and element are thematically consistent with the name and description.
        - For bosses, make the attack and abilities more powerful and unique.
        - Only select spells from the provided list. No other spells are valid!
        - If it's a boss, consider adding an extra ability or characteristic that makes it stand out.

        All variables should be at the top level of the JSON object.
        """,
        output_template={
            "name": "string",
            "description": "string",
            "job_class": "string",
            "attack": "string",
            "spells": ["string"],
            "element": "string",
        },
    )

    GENERATE_STATS = Prompt(
        """
        Generate stat biases for a character class in a JRPG. 
        The character class is: {job_class}

        Provide a bias value for each stat, where:
        0 = Very Low, 1 = Low, 2 = Average, 3 = High, 4 = Very High

        Consider the typical characteristics of this class in JRPGs when assigning biases.
        Ensure that the biases are balanced - not all stats should be high or low.

        The stats to consider are: HP, MP, Attack, Defense, Intelligence, Wisdom, Speed, and Luck.
        """,
        output_template={
            "max_hp": 0,
            "max_mp": 0,
            "attack": 0,
            "defense": 0,
            "intelligence": 0,
            "wisdom": 0,
            "speed": 0,
            "luck": 0,
        },
    )
