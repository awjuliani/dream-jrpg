from src.api.prompts.base import Prompt


class BattlePrompts:
    GENERATE_BATTLE_COMMAND = Prompt(
        """
        Given the following battle context, reason through the best action for the character to take:
        {battle_context}

        Ensure that the chosen action is valid based on the character's available actions and current status.
        Consider the battle situation, including ally and enemy health, status effects, and potential strategies.
        Select 'attack' as the default action. Only select other actions if there is a good reason to do so.
        Avoid simply repeating the previous action unless there is a good reason to do so.
        Ensure that the target is selected based on the list of valid allies and enemies.
        Provide a short explanation of the chosen action and why it is the best course of action.
        """,
        output_template={
            "explanation": "string",
            "action_type": "string",
            "target": "string",
            "skill_name": "string",
            "spell_name": "string",
            "item_name": "string",
        },
    )
