from src.api.prompts.base import Prompt


class DialoguePrompts:
    GENERATE_NPC_DIALOGUE = Prompt(
        """
        Generate a complete JRPG NPC dialogue tree.
        NPC: {npc_name}, {npc_description}, {npc_type}
        Player character: {player_name}, {player_description}
        Story context: {event_context}
        Current location: {current_location}

        Conversation context: {convo_context}
        Valid final outcomes: {valid_outcomes}

        Create a two-level dialogue tree with:
        1. Initial NPC message (~50 words)
        2. Four initial player responses (Level 1)
        3. Four follow-up responses for each initial response (Level 2)

        For each response include:
        - short_text: Brief response for selection (~10 words)
        - full_text: Detailed response (~50 words)
        - outcome: The final result (must be from valid_outcomes)
        - final_message: NPC's concluding message (~50 words)

        NPC type guidelines:
        - random: Casual dialogue, local info on current location
        - story: Plot-relevant dialogue about key items/locations
        - shop: Discuss items, services, prices
        - enemy: Create tension leading to conflict
        - ally: Focus on recruitment dialogue

        Outcome distribution guidelines:
        - continue: Continue the conversation (use this for all Level 1 outcomes)
        - shop_discount: For shop NPCs, (use this for 1-2 Level 2 outcomes)
        - recruit_success: For ally NPCs, (use this for 1-2 Level 2 outcomes)
        - recruit_failure: For ally NPCs, (use this for 1-2 Level 2 outcomes)
        - battle_intimidated: For enemy NPCs, (use this for 1-2 Level 2 outcomes)
        - battle: For enemy NPCs, (use this for 1-2 Level 2 outcomes)
        - end: Default outcome for unsuccessful attempts (use this for 1-2 Level 2 outcomes)
        - give_item: For story NPCs, (use this for 1-2 Level 2 outcomes)
        
        Ensure each path feels distinct and meaningful, with outcomes that make sense for the conversation flow.
        All paths must end in a final outcome (no loops or continuations).
        """,
        output_template={
            "initial_message": "string",
            "responses": [
                {
                    "short_text": "string",
                    "full_text": "string",
                    "npc_reply": "string",
                    "outcome": "string",
                    "follow_up_responses": [
                        {
                            "short_text": "string",
                            "full_text": "string",
                            "outcome": "string",
                            "final_message": "string",
                        }
                    ]
                    * 4,
                }
            ]
            * 4,
        },
    )

    GENERATE_CUTSCENE = Prompt(
        """
        Generate a cutscene for a JRPG scene based on:
        Event Description: {event_description}
        Characters Present: {characters}
        Location: {location_name} - {location_description}
        Previous Events: {past_events}
        Story Level: {story_level} (1-100)
        Thematic Style: {thematic_style}
        Conversation Length: {conversation_length}
        Is the dialogue before, during, or after the event: {event_timing}

        Guidelines:
        1. Create a natural flowing sequence of spoken dialogue and narrative description that advances the story and reveals character personalities
        2. Use the thematic style to guide the dialogue
        3. Include both dialogue and narrative description, each of which are different types of scene items
        4. Each dialogue line should include:
           - The speaking character's full name
           - The spoken text
           - Any associated emotion or action tags
           - Be only a few sentences, totaling no more than 30 words max
        5. Narrative descriptions should:
           - Set the scene
           - Describe character movements and reactions
           - Highlight important environmental details
           - Be clearly marked as narrative text
           - Be only a few sentences, totaling no more than 30 words max
        6. The scene should:
           - Have a clear beginning, middle, and end
           - Include at least one meaningful character interaction
           - Reference relevant previous events when appropriate
           - Maintain consistent character voices
           - Connect the current event to the next event objective
           - Include all of the characters present in the scene
        7. 'short' conversations should only include 1-5 scene items.
        8. 'long' conversations should only include 5-10 scene items.
        9. "before_event" dialogue should lead up to the event (a battle with a boss, a trying to recruit an ally, etc.)
           - For ally recruitment, the dialogue should end right before the player tries to recruit the ally
           - For boss battles, the dialogue should end right before the player fights the boss. Include the boss in the dialogue.
        10. "after_event" dialogue should discuss the aftermath of the event (the defeat of a boss, the successful recruitment of an ally, etc.)
           - For ally recruitment, the dialogue should begin right after the player has successfully recruited the ally
           - For boss battles, the dialogue should begin right after the player has defeated the boss
        11. "during_event" dialogue should convey all the action happening during the event.

        - valid types: dialogue, narration
        - speaker and emotion are only for dialogue.

        Ensure the dialogue feels natural while advancing the story and developing characters.
        """,
        output_template={
            "title": "string",
            "scene": [
                {
                    "type": "string",
                    "speaker": "string",
                    "text": "string",
                    "emotion": "string",
                }
            ],
        },
    )

    GENERATE_NPC_DATA = Prompt(
        """
        Generate NPC data for a JRPG based on:
        NPC name: {npc_name}
        Example dialogue: {example_dialogue}
        Location: {location_name} - {location_description}
        Story level: {story_level} (1-100)
        NPC type: {npc_type}

        Create an NPC profile that includes:
        1. Description
        - Physical appearance (age, notable features, clothing style)
        - Mannerisms and personality traits
        - Should be 2-3 sentences long (~50 words)

        2. Backstory
        - Personal history relevant to their current situation
        - Connection to the current location
        - Motivations and goals
        - Should be 3-4 sentences long (~75 words)

        3. Job Class
        - A role or profession that fits their character
        - Should be 1-2 words (e.g., "Merchant", "Village Elder", "Wandering Mage")
        - Should be appropriate for their location and the story level

        Guidelines:
        - Ensure the NPC feels grounded in the location
        - Create believable motivations and personalities
        - The NPC should be someone who would speak like the example dialogue
        """,
        output_template={
            "npc": {
                "name": "string",
                "description": "string",
                "backstory": "string",
                "job_class": "string",
            }
        },
    )
