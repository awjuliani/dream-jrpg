from typing import Dict, Callable
from src.api.prompts.base import Prompt, GeneralPrompts
from src.api.prompts.story_prompts import StoryPrompts
from src.api.prompts.battle_prompts import BattlePrompts
from src.api.prompts.character_prompts import CharacterPrompts
from src.api.prompts.location_prompts import LocationPrompts
from src.api.prompts.item_prompts import ItemPrompts
from src.api.prompts.dialogue_prompts import DialoguePrompts


class Prompts:
    def __init__(self):
        self.story = StoryPrompts()
        self.battle = BattlePrompts()
        self.character = CharacterPrompts()
        self.location = LocationPrompts()
        self.item = ItemPrompts()
        self.dialogue = DialoguePrompts()
        self.general = GeneralPrompts()

    def get_prompt(self, prompt_name: str) -> Callable:
        # First check if prompt_name contains a namespace (e.g. "story.system_message")
        if "." in prompt_name:
            namespace, name = prompt_name.split(".", 1)
            prompt_group = getattr(self, namespace.lower(), None)
            if prompt_group:
                return getattr(prompt_group, name.upper()).format

        # Try each namespace if no explicit namespace given
        for namespace in [
            "story",
            "battle",
            "character",
            "location",
            "item",
            "dialogue",
            "general",
        ]:
            prompt_group = getattr(self, namespace)
            prompt = getattr(prompt_group, prompt_name.upper(), None)
            if prompt:
                return prompt.format

        raise ValueError(f"Prompt '{prompt_name}' not found")

    def list_prompts(self) -> Dict[str, Prompt]:
        prompts = {}
        for namespace in [
            "story",
            "battle",
            "character",
            "location",
            "item",
            "dialogue",
            "general",
        ]:
            prompt_group = getattr(self, namespace)
            group_prompts = {
                f"{namespace}.{name}": value
                for name, value in vars(prompt_group).items()
                if isinstance(value, Prompt)
            }
            prompts.update(group_prompts)
        return prompts
