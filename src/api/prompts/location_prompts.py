from src.api.prompts.base import Prompt


class LocationPrompts:
    GENERATE_TOWN_DETAILS = Prompt(
        """
        Generate detailed information for a town or city in a JRPG. Use the following information:
        World Description: {world_description}
        Town/City Name: {town_name}
        Short Town/City Description: {town_description}
        Story Level: {story_level} (1-100)

        Generate:
        1. An expanded description of the town or city (~50 words).
            - Include details about the appearance of the town or city, including the colors of the buildings and the overall feel of the town or city
            - Describe the weather and time of day, including the color of the sky
        2. The town or city will be divided into two parts. Each part should be visually distinct in some way.
            - Part A will be in the first half of the town that the player visits.
            - Part B will be in the second half of the town that the player visits.
        3. Key town or city elements with coordinates and sub-location assignments:
            - Inn
            - Item Shop
            - Spell Shop
            - Equipment Shop
        3. Border messages for each cardinal direction
            - It should briefly describe what the party can see in that direction and that they are on the border of the town or city

        For each element, ensure that the description reflects the town or city's theme and atmosphere.

        Ensure all elements create a cohesive, navigable town or city layout.
        """,
        output_template={
            "name": "string",
            "description": "string",
            "part_a_description": "string",
            "part_b_description": "string",
            "border_messages": {
                "north": "string",
                "south": "string",
                "east": "string",
                "west": "string",
            },
            "inn": {
                "name": "string",
                "description": "string",
                "goodbye_text": "string",
                "shopkeeper_name": "string",
            },
            "item_shop": {
                "name": "string",
                "description": "string",
                "goodbye_text": "string",
                "shopkeeper_name": "string",
            },
            "spell_shop": {
                "name": "string",
                "description": "string",
                "goodbye_text": "string",
                "shopkeeper_name": "string",
            },
            "equipment_shop": {
                "name": "string",
                "description": "string",
                "goodbye_text": "string",
                "shopkeeper_name": "string",
            },
        },
    )

    GENERATE_FIELD_DETAILS = Prompt(
        """
        Generate detailed information for a field location in a JRPG. Use the following information:
        World Description: {world_description}
        Field Name: {field_name}
        Short Field Description: {field_description}
        Story Level: {story_level} (1-100)

        Generate:
        1. An expanded description (~50 words).
            - Include details about the appearance of the field, including the colors of the terrain and the overall feel of the field
            - Describe the weather and time of day, including the color of the sky
        2. The field will be divided into two parts. Each part should be visually distinct in some way.
            - Part A will be in the first half of the field that the player visits.
            - Part B will be in the second half of the field that the player visits.
        3. 3 enemy types appropriate for the area and story level (i.e. weak enemies for level 1, strong enemies for level 100)
        4. Border messages for each cardinal direction
            - It should briefly describe what the party can see in that direction and that they are on the border of the field

        Ensure the layout creates an interesting exploration experience while maintaining a clear path forward.
        """,
        output_template={
            "name": "string",
            "description": "string",
            "part_a_description": "string",
            "part_b_description": "string",
            "border_messages": {
                "north": "string",
                "south": "string",
                "east": "string",
                "west": "string",
            },
            "enemy_types": [{"name": "string", "description": "string"}] * 3,
        },
    )

    GENERATE_DUNGEON_DETAILS = Prompt(
        """
        Generate detailed information for a dungeon location in a JRPG. Use the following information:
        World Description: {world_description}
        Dungeon Name: {dungeon_name}
        Short Dungeon Description: {dungeon_description}
        Story Level: {story_level} (1-100)

        Generate:
        1. An expanded description (~50 words).
            - Include details about the appearance of the dungeon, including the colors of the walls and the overall feel of the dungeon
        2. The dungeon will be divided into two parts. Each part should be visually distinct in some way.
            - Part A will be in the first half of the dungeon that the player visits.
            - Part B will be in the second half of the dungeon that the player visits.
            - The boss of the dungeon will always be in Part B.
        3. 5 enemy types appropriate for the dungeon and story level (i.e. weak enemies for level 1, strong enemies for level 100)
        4. Border messages for each cardinal direction
            - It should briefly describe what the party can see in that direction and that they are on the border of the dungeon

        Ensure the layout creates a challenging and rewarding dungeon crawl experience.
        """,
        output_template={
            "name": "string",
            "description": "string",
            "part_a_description": "string",
            "part_b_description": "string",
            "enemy_types": [{"name": "string", "description": "string"}] * 3,
            "border_messages": {
                "north": "string",
                "south": "string",
                "east": "string",
                "west": "string",
            },
        },
    )

    GENERATE_NAVIGATION_TEXT = Prompt(
        """
        Generate navigation text for a location in a JRPG.
        Location Name: {location_name}
        Location Description: {location_description}
        Party Members: {party_members}
        Current Position: {current_position}
        Points of Interest: {points_of_interest}
        Move Directions: {move_directions}
        Look Directions: {look_directions}
        Border Messages: {border_messages}

        Guidelines:
        1. Provide a brief (~30 words) description of the current situation and surroundings.
           - Be sure to mention if a point of interest is 'here' at your current position
        2. For each move direction, provide a short movement text for the party to move in that direction (e.g. "Walk west towards the forest")
           - The text should be only a few words (~5 - 10 words)
           - If there is a point of interest nearby in that direction, mention it
           - Each text should mention the cardinal direction that it represents
           - It should focus on nearby points of interest
        3. For each look direction, provide a short look text for the party to look in that direction (e.g. "Look west towards the forest")
           - The text should be only a few words (~5 - 10 words)
           - Base the text on the border message for that direction
        4. Maintain the atmospheric and descriptive style typical of JRPGs. Use only natural descriptive language.
           - Do not mention the party's coordinates or position explicitly

        Ensure the descriptions are engaging and help players understand their surroundings.
        """,
        output_template={
            "current_situation": "string",
            "directions": {
                "North": "string",
                "South": "string",
                "East": "string",
                "West": "string",
            },
        },
    )
