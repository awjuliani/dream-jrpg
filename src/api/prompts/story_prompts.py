from src.api.prompts.base import Prompt


class StoryPrompts:
    GENERATE_SETTING = Prompt(
        """
        Generate a rich setting for a JRPG based on these seed elements:
        Setting Seeds: {setting_seeds}

        Create a setting that includes:
        1. World Building
        - A rich, diverse world blending fantasy/sci-fi with cultural elements
        - Clear cultural and environmental distinctions between regions
        - Draw broadly from world history and mythology for inspiration

        2. Currency
        - Name of the world's currency (e.g., "Gold", "Zenny", "Gems", etc.)

        3. Visual Themes
        - Prominent visual themes that represent the world's atmosphere and themes
        - Visual themes should be provided in a list of three strings

        Guidelines:
        - Design settings that will support character development and dramatic stories
        - Create a world with clear rules and internal consistency
        - Include both magical/technological and cultural systems
        - Consider how the world's history shapes its present state
        - Be creative and imaginative, don't just rehash the same old fantasy settings
        """,
        output_template={
            "world_name": "string",
            "world_description": "string",
            "visual_themes": ["string"] * 3,
            "currency_name": "string",
        },
    )

    GENERATE_PROTAGONIST = Prompt(
        """
        Generate a protagonist for a JRPG based on:
        World Description: {world_description}
        Protagonist Seeds: {protagonist_seeds}
        
        Create a protagonist that includes:
        1. Character Details
        - A compelling personal history tied to the world
        - Clear motivations and personal struggles
        - Physical appearance and personality traits
        - A job class that fits their background (should be one to two words long)

        Guidelines:
        - Ensure the character fits naturally within the established world
        - Create relatable flaws and struggles
        - Design a character with room to grow through their journey
        - Balance personal motivations with broader responsibilities
        - Be creative and imaginative, don't just rehash the same old fantasy characters
        """,
        output_template={
            "full_name": "string",
            "short_name": "string",
            "appearance": "string",
            "job_class": "string",
            "backstory": "string",
            "short_description": "string",
        },
    )

    GENERATE_STORY = Prompt(
        """
        Generate a story outline for a JRPG based on:
        World Description: {world_description}
        Protagonist: {protagonist_info}
        Story Seeds: {story_seeds}
        Possible Ally Personalities: {possible_ally_personalities}

        The story should incorporate classic elements of a JRPG story, such as:
        - The Hero's Journey: A protagonist embarks on a transformative quest, starting as an ordinary or reluctant hero.
        - A Diverse Cast of Party Members: Allies with unique backgrounds, abilities, and struggles join the hero's journey.
        - A World in Peril: The story revolves around saving the world or overcoming a major existential threat.
        - A Complex Villain: The antagonist has a compelling backstory or ideology, adding depth to their role.
        - Twists and Revelations: Unexpected plot twists or shocking truths keep the story engaging and unpredictable.
        - Exploration of Themes: Universal themes like destiny, sacrifice, love, and hope are central to the narrative.
        - Rich Lore and Worldbuilding: A detailed world with its own history, cultures, and lore enhances immersion.
        - Interpersonal Relationships: Deep character dynamics and evolving bonds among allies drive emotional engagement.
        - A Personal Stake for the Hero: The protagonist has personal motivations that tie them deeply to the central conflict.
        - A Climactic Finale: The story concludes with a high-stakes confrontation that resolves major plot threads.
        
        Create a narrative that includes:

        0. Title
        - A short title for the game itself

        1. Overview of the story
        - A narrative that expands from personal to global stakes
        - Exploration of philosophical or theological themes
        - Elements of loss and resilience woven throughout
        - Balance moments of triumph with meaningful sacrifices

        2. Chapter Structure
        - Five chapters that form a complete arc
        - New characters introduced in each chapter
        - Clear progression of stakes and tension
        - Meaningful integration of the world and protagonist's journey

        Guidelines:
        - Ensure each chapter overview is extensive and detailed (200+ words)
        - For each chapter, introduce new characters that will be important to the story
        - Create meaningful connections between personal arcs and the main plot
        - The antagonist should have a tragic backstory which motivates their actions
        - The brief overview should be short and avoid any spoilers
        - Each chapter should have the protagonist teaming up with a new ally that has a unique personality
        - Assign each of the five possible ally personalities to a different chapter
        - Be creative and imaginative, don't just rehash the same old fantasy narratives
        - Be specific and detailed, using proper nouns wherever possible for characters and locations
        - The Ally and Boss names should be unique and not the same entity
        - Ensure the chosen ally personalities are listed verbatim in the output and are unique for each chapter
        """,
        output_template={
            "title": "string",
            "overview": "string",
            "thematic_style": "string",
            "brief_overview": "string",
            "chapters": [
                {
                    "title": "string",
                    "ally_name": "string",
                    "ally_personality": "string",
                    "boss_name": "string",
                    "overview": "string",
                }
            ]
            * 5,
        },
    )

    GENERATE_CHAPTER_SETUP = Prompt(
        """
        Generate the outline for a JRPG chapter based on:
        World Description: {world_description}
        Previous Locations: {previous_locations}
        Current Party Members: {current_party}
        Current Story Level: {story_level} (1-100)

        Previous Chapter Overview: {previous_chapter_overview}
        Current Chapter Title: {chapter_title}
        Current Chapter Overview: {chapter_overview}
        Current Chapter Number: {chapter_number} / {total_chapters}

        Thematic Style: {thematic_style}

        Create a chapter setup containing:
        1. Chapter Details:
           - Title: A memorable chapter name (don't include the chapter number)
           - Overview: Build on the provided overview above, adding more detail and context
           - Prologue Text: A short text that sets the scene for the upcoming events of the chapter (~50 words max)

        2. Sub-Chapters:
           Create 4 sub-chapters that form a complete narrative arc. For each sub-chapter provide:
           - Overview: A detailed description of the events and goals (~200 words)
           - Location:
             * Name of the location
             * Description (~50 words, convey appearance, layout, and atmosphere)
             * Type: Must be either "field", "town", or "dungeon"
             Note: Across all sub-chapters, include one town, two fields, and one dungeon
             Note: Only include the dungeon in the final sub-chapter
           - Contains: A string that is one of the following:
             * "ally_npc"
             * "story_npc"
             * "boss_npc"
             * "landmark"

        3. Key NPCs (provide all of these):
           a) Ally NPC:
              - Name: {ally_name}
              - Description: Physical appearance and personality
              - Type: "ally"
              - Job Class: Based on the following personality: {selected_class}
              - Backstory: (~50 words)
              - Location: Which sub-chapter location they appear in

           b) Story NPC (should be different from ally or boss NPC):
              - Name: A unique character name
              - Description: Physical appearance and role
              - Location: Which sub-chapter location they appear in
              - Type: "story"
              - Job Class: A job class that fits their role
              - Backstory: (~50 words)

           c) Boss NPC:
              - Name: {boss_name}
              - Description: Physical appearance and role
              - Location: Must be in the final sub-chapter location
              - Type: "boss"
              - Job Class: A job class that fits their role
              - Backstory: (~50 words)

        4. Landmark:
           - Name: A significant location or structure
           - Description: Its appearance and significance
           - Location: Which sub-chapter location it appears in

        Guidelines:
        - Maintain consistency with previous chapters while escalating stakes appropriately
        - Each sub-chapter should flow naturally into the next, creating a cohesive narrative
        - Each NPC and landmark should be in a unique location with no overlap between sub-chapters
        """,
        output_template={
            "title": "string",
            "overview": "string",
            "prologue_text": "string",
            "sub_chapters": [
                {
                    "overview": "string",
                    "location": {
                        "name": "string",
                        "description": "string",
                        "type": "string",
                    },
                    "contains": "string",
                }
            ]
            * 4,
            "ally_npc": {
                "name": "string",
                "description": "string",
                "type": "string",
                "backstory": "string",
                "job_class": "string",
                "location": "string",
            },
            "story_npc": {
                "name": "string",
                "description": "string",
                "type": "string",
                "backstory": "string",
                "job_class": "string",
                "location": "string",
            },
            "boss_npc": {
                "name": "string",
                "description": "string",
                "type": "string",
                "backstory": "string",
                "job_class": "string",
                "location": "string",
            },
            "landmark": {
                "name": "string",
                "description": "string",
                "location": "string",
            },
        },
    )

    GENERATE_SUB_CHAPTER_EVENTS = Prompt(
        """
        Generate a sequence of three events for a JRPG sub-chapter based on:
        Chapter Title: {chapter_title}
        Chapter Overview: {chapter_overview}
        Sub-Chapter Overview: {sub_chapter_overview}
        Location: {location}
        Available NPC: {available_npc}
        Available Landmark: {available_landmark}
        Previous Events: {previous_events}

        Create two sequential events that:
        - All occur within the given location
        - Follow naturally from previous events
        - Move the story forward according to the sub-chapter overview
        - Use the available NPCs and landmarks appropriately
           - If the NPC is of type "ally", then the final event must be "ally_recruited"
           - If the NPC is of type "boss", then the final event must be "boss_confronted"
        
        Event Requirements:
        1. First Event - Location Introduction:
           - Must use trigger type "location_entered"
           - Should establish the atmosphere and initial situation
           - The 'value' should be the verbatim name of the location provided above

        2. Second Event - In-Location Event:
           Must use one of these trigger types:
           - "story_exposition" - For story exposition or character development (use with "story" type NPCs)
           - "landmark_inspected" - For world building or plot advancement (use when there are no NPCs in the location)
           - "boss_confronted" - For major confrontations (use with "boss" type NPCs)
           - "ally_recruited" - For gaining new party members (use with "ally" type NPCs)
        
        For each event provide:
        - Trigger: The type and specific target (NPC, landmark, etc.)
        - Trigger Hint: Brief hint about what the player should do to trigger the event
        - Event Text: Story text or description (50 words max)

        Maintain consistency across events while building tension toward the climax.
        Each event should feel meaningful and contribute to the sub-chapter's narrative.
        """,
        output_template={
            "events": [
                {
                    "trigger": {
                        "type": "string",
                        "value": "string",
                    },
                    "trigger_hint": "string",
                    "event_text": "string",
                }
            ]
            * 2
        },
    )

    GENERATE_STORY_SO_FAR = Prompt(
        """
        Generate a concise but engaging summary of the story so far in a JRPG based on these previous events:
        {past_events}

        Use the following thematic style for the summary:
        {thematic_style}

        Guidelines:
        1. Write approximately 100 words that capture the key story beats
            - Only mention events that have already occurred
        2. Focus on:
           - Major plot developments
           - Character introductions and growth
           - Important locations visited
           - Significant battles or confrontations
           - Current story stakes
        3. Use a narrative style typical of JRPGs:
           - Dramatic but not overwrought
           - Personal and emotional elements balanced with larger plot
           - Clear sense of the journey so far
           - Avoid overly flowery or poetic language
           - Be concise and to the point with no fluff

        The summary should help players who are returning to the game remember where they are in the story.
        """,
        output_template={
            "summary": "string",
        },
    )
