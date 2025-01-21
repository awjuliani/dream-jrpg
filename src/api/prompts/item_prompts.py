from src.api.prompts.base import Prompt


class ItemPrompts:
    GENERATE_EQUIPMENT = Prompt(
        """
        Generate attributes for a {equipment_type} in a JRPG for a {job_class} character.
        Power level: {level} (1-100, where 1 is weakest and 100 is strongest)
        Location: {location_name} - {location_description}
        Valid elements: {elements}

        Guidelines:
        1. Stat Biases:
        Provide a bias value for each stat, where:
        0 = Very Low, 1 = Low, 2 = Average, 3 = High, 4 = Very High

        Consider the typical characteristics of this equipment type and job class in JRPGs when assigning biases.
        Ensure that the biases are balanced - not all stats should be high or low.

        2. Equipment Type Considerations:
        - Weapons: Prioritize attack, may have elemental affinity
        - Armor: Prioritize defense, may have elemental resistance
        - Accessories: May boost multiple stats

        3. Element:
        - For weapons and armor, choose an element from the valid list or "None"
        - For accessories, always use "None"

        Provide a brief description of the equipment's appearance and properties.
        Ensure attributes are appropriate for the equipment type, job class, and power level.
        """,
        output_template={
            "name": "string",
            "description": "string",
            "stat_biases": {
                "max_hp": 0,
                "max_mp": 0,
                "attack": 0,
                "defense": 0,
                "intelligence": 0,
                "wisdom": 0,
                "speed": 0,
                "luck": 0,
            },
            "element": "string",  # For weapons and armor, "None" if not applicable
        },
    )

    GENERATE_ITEM_SHOP = Prompt(
        """
        Generate details for a JRPG item shop in {location_name}.
        Item Shop Name: {shop_name}
        Location description: {location_description}
        Average character level: {avg_level}

        Guidelines:
        1. Name: Reflect location's characteristics, culture, and item-selling nature
        2. Description: ~50 words, vivid details of appearance, atmosphere, unique features
        3. Items: Select 5-10 appropriate items from this list:
        {valid_items}
        4. For each item, determine a fair price based on:
        - Item's power
        - Shop's location (e.g., poor village cheaper, wealthy city more expensive)
        - Average character level (higher levels access to more powerful, expensive items)

        Create a shop that fits the location's theme and atmosphere. 
        Consider how the shop's features, items, and prices reflect the area's characteristics and the typical customer's level.
        Ensure selected items align with local culture or environment.
        """,
        output_template={
            "name": "string",
            "description": "string",
            "items": [{"name": "string", "price": 0}] * 5,  # Indicates at least 5 items
        },
    )

    GENERATE_SPELL_SHOP = Prompt(
        """
        Generate details for a JRPG spell shop in {location_name}.
        Spell Shop Name: {shop_name}
        Location description: {location_description}
        Average character level: {avg_level}

        Guidelines:
        1. Name: Reflect location's characteristics, culture, and spell-selling nature
        2. Description: ~50 words, vivid details of appearance, atmosphere, unique magical features
        3. Spells: Select 3-7 appropriate spells from this list: {valid_spells}
           - Only select spells from the provided list above as no other spell names will be valid!
        4. For each spell, determine a fair price based on:
        - Spell's power
        - Shop's location (e.g., modest village cheaper, grand magical city more expensive)
        - Average character level (higher levels access to more powerful, expensive spells)

        Create a shop that fits the location's magical theme and atmosphere. 
        Consider how the shop's features, spells, and prices reflect the area's magical traditions and the typical customer's level.
        Ensure selected spells align with local magical culture or environment.
        """,
        output_template={
            "name": "string",
            "description": "string",
            "spells": [{"name": "string", "price": 0}] * 3,
        },
    )

    GENERATE_SPELL_SET = Prompt(
        """
        Generate spells for tier {tier_number} of a JRPG set in the following world:
        World Name: {world_name}
        World Description: {world_description}
        Previous Spell Names: {previous_spell_names}

        Create spells for this tier, including:
        1. One spell for each element: Fire, Water, Thunder, Ice, Earth, Wind, Light, and Dark.
        2. One spell for each negative status effect: Poison, Silence, Sleep, Slow.
        3. Two healing spells. One should be a basic healing spell, the other should be a revive spell.
        4. One buff spell for each positive status effect: Haste, Defend, Regen.

        Guidelines:
        - Each spell should have a name and a short one-sentence description.
        - Spell names should be creative, fit the world's theme, and not duplicate previous spell names.
        - Descriptions should briefly explain the spell's effect.
        - All spells should involve the use of magic and not physical attacks.
        - Ensure spell effects are appropriate for their tier:
          * Tier 1: Weakest spells with basic effects
          * Tier 2: Enhanced spells with stronger effects
          * Tier 3: Stronger spells with more powerful effects
          * Tier 4: Powerful spells with complex or combined effects
          * Tier 5: Ultimate spells with the most powerful effects
        - Incorporate elements of the world's lore or unique features into spell names or descriptions where appropriate.
        - IMPORTANT: Do not reuse any of these previous spell names!
        """,
        output_template={
            "elemental": [
                {"name": "string", "description": "string", "element": "string"}
            ]
            * 8,
            "status": [{"name": "string", "description": "string", "effect": "string"}]
            * 4,
            "healing": [
                {"name": "string", "description": "string", "revives": "boolean"},
                {"name": "string", "description": "string", "revives": "boolean"},
            ],
            "buff": [{"name": "string", "description": "string", "effect": "string"}]
            * 3,
        },
    )

    GENERATE_ITEM_SET = Prompt(
        """
        Generate items for tier {tier_number} of a JRPG set in the following world:
        World Name: {world_name}
        World Description: {world_description}
        Previous Item Names: {previous_item_names}

        Create items for this tier, including:
        1. One healing item (e.g., Potion, Hi-Potion)
        2. One MP restoring item (e.g., Ether)
        3. One revive item (e.g., Phoenix Down)
        4. One status recovery item (e.g., Antidote, Echo Herb)
        5. One offensive item (e.g., Bomb, Shuriken)

        Guidelines:
        - Each item should have a name and a short one-sentence description.
        - Item names should be creative, fit the world's theme, and not duplicate previous item names.
        - Descriptions should briefly explain the item's effect.
        - Ensure item effects are appropriate for their tier:
          * Tier 1: Weakest items with basic effects
          * Tier 2: Enhanced versions of basic items
          * Tier 3: Stronger items with more powerful effects
          * Tier 4: Powerful items with complex or combined effects
          * Tier 5: Ultimate items with the most powerful effects
        - Incorporate elements of the world's lore or unique features into item names or descriptions where appropriate.
        - IMPORTANT: Do not reuse any of these previous item names!
        """,
        output_template={
            "healing": {"name": "string", "description": "string"},
            "mp_restore": {"name": "string", "description": "string"},
            "revive": {"name": "string", "description": "string"},
            "status_recovery": {
                "name": "string",
                "description": "string",
                "status_effects": ["string"],
            },
            "offensive": {"name": "string", "description": "string"},
        },
    )
