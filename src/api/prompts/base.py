from typing import Dict
import json


class Prompt:
    def __init__(self, template: str, output_template: Dict = None, **kwargs):
        self.template = template
        self.output_template = output_template
        self.kwargs = kwargs

    def format(self, **kwargs) -> str:
        formatted_prompt = self.template.format(**{**self.kwargs, **kwargs}).strip()
        if self.output_template:
            template_str = json.dumps(self.output_template, indent=2)
            formatted_prompt += f"\n\nPlease provide your response in the following JSON format:\n{template_str}"
        return formatted_prompt


class GeneralPrompts:
    SYSTEM_MESSAGE = Prompt(
        """
        You help power the game engine of a JRPG and are used to procedurally generate elements of the game. 
        You are designed to output JSON objects and adhere to this format strictly.
        Output ONLY the JSON object and ensure it is valid and perfectly formatted according to the provided template.
        For all narration, avoid empty and overly flowery or poetic language. 
        Focus instead on real and concrete events, thoughts, action, and emotions.
        """
    )

    GENERATE_ACTION_TEXT = Prompt(
        """
        I will provide you with a short action description.
        Please generate a slightly longer description which is more descriptive and interesting (50 words max). 
        Avoid the use of excessive adjectives or superficially flowerly language.
        It should retain all the important information from the original text. Put it into a variable called 'detailed_text'.
        ACTION: {action_text}
        """,
        output_template={"detailed_text": "string"},
    )
