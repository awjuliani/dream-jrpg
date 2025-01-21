from functools import wraps
import json
import yaml
from pathlib import Path
from src.api.prompts import Prompts
from src.utils.utils import load_config


class LLM:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLM, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.cache_file = Path("data/llm_cache.json")
        self.ensure_data_folder()
        self.cache = self.load_cache()
        self.prompts = Prompts()

        # Use the shared config loader
        config = load_config()
        self.set_provider(
            config.get("provider", "openai"), config.get("model_size", "small")
        )
        self.use_cache = config.get("use_cache", False)

    def set_provider(self, provider: str, model_size: str = "small"):
        if provider.lower() == "openai":
            from src.api.providers import OpenAIProvider

            self.provider = OpenAIProvider(model_size=model_size)
        elif provider.lower() == "anthropic":
            from src.api.providers import AnthropicProvider

            self.provider = AnthropicProvider(model_size=model_size)
        elif provider.lower() == "gemini":
            from src.api.providers import GeminiProvider

            self.provider = GeminiProvider(model_size=model_size)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def ensure_data_folder(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def cache_result(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_key = f"{func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"

            if self.use_cache and cache_key in self.cache:
                return self.cache[cache_key]

            result = func(self, *args, **kwargs)
            self.cache[cache_key] = result
            self.save_cache()
            return result

        return wrapper

    def load_cache(self):
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)

    def generate(self, prompt):
        system_message = self.prompts.get_prompt("general.system_message")()
        return self.provider.generate(prompt, system_message)

    @cache_result
    def generate_enemy(
        self,
        level=1,
        enemy_type="regular",
        location=None,
        spells=None,
        elements=None,
        enemy_info=None,
    ):
        if enemy_info is None:
            enemy_info = {"name": "", "description": ""}
        prompt = self.prompts.get_prompt("character.generate_enemy")(
            level=level,
            enemy_type=enemy_type,
            location_name=location["name"],
            location_description=location["description"],
            spells=spells,
            elements=elements,
            base_name=enemy_info["name"],
            base_description=enemy_info["description"],
        )
        return self.generate(prompt)

    @cache_result
    def generate_battle_command(self, battle_context: str) -> str:
        prompt = self.prompts.get_prompt("battle.generate_battle_command")(
            battle_context=battle_context,
        )
        return self.generate(prompt)

    @cache_result
    def generate_action_text(self, action_text):
        prompt = self.prompts.get_prompt("general.generate_action_text")(
            action_text=action_text
        )
        return self.generate(prompt)["detailed_text"]

    @cache_result
    def generate_npc_dialogue(
        self,
        npc_dict,
        event_context,
        convo_context,
        valid_outcomes,
        player_name,
        player_description,
        current_location=None,
    ):
        prompt = self.prompts.get_prompt("generate_npc_dialogue")(
            npc_name=npc_dict["name"],
            npc_description=npc_dict["description"],
            npc_type=npc_dict["type"],
            event_context=event_context,
            convo_context=convo_context,
            valid_outcomes=valid_outcomes,
            player_name=player_name,
            player_description=player_description,
            current_location=current_location,
        )
        return self.generate(prompt)

    @cache_result
    def generate_stats(self, job_class):
        prompt = self.prompts.get_prompt("generate_stats")(job_class=job_class)
        return self.generate(prompt)

    @cache_result
    def generate_equipment(self, equipment_type, level, job_class, elements, location):
        prompt = self.prompts.get_prompt("generate_equipment")(
            equipment_type=equipment_type,
            level=level,
            job_class=job_class,
            elements=elements,
            location_name=location["name"],
            location_description=location["description"],
        )
        return self.generate(prompt)

    @cache_result
    def generate_item_shop(self, shop_name, location, avg_level, valid_items):
        prompt = self.prompts.get_prompt("generate_item_shop")(
            location_name=location["name"],
            location_description=location["description"],
            avg_level=avg_level,
            valid_items=valid_items,
            shop_name=shop_name,
        )
        return self.generate(prompt)

    @cache_result
    def generate_spell_shop(self, shop_name, location, avg_level, valid_spells):
        prompt = self.prompts.get_prompt("generate_spell_shop")(
            location_name=location["name"],
            location_description=location["description"],
            avg_level=avg_level,
            valid_spells=valid_spells,
            shop_name=shop_name,
        )
        return self.generate(prompt)

    @cache_result
    def generate_chapter_setup(
        self,
        world_description: str,
        previous_locations: str,
        current_party: list,
        story_level: int,
        chapter_number: int,
        total_chapters: int,
        chapter_data: dict,
        thematic_style: str,
        previous_chapter_overview: str,
    ):
        prompt = self.prompts.get_prompt("story.generate_chapter_setup")(
            world_description=world_description,
            previous_locations=previous_locations,
            previous_chapter_overview=previous_chapter_overview,
            current_party=current_party,
            story_level=story_level,
            chapter_number=chapter_number,
            total_chapters=total_chapters,
            chapter_overview=chapter_data["overview"],
            chapter_title=chapter_data["title"],
            thematic_style=thematic_style,
            selected_class=chapter_data["ally_personality"],
            ally_name=chapter_data["ally_name"],
            boss_name=chapter_data["boss_name"],
        )
        return self.generate(prompt)

    @cache_result
    def generate_sub_chapter_events(
        self,
        chapter_title: str,
        chapter_overview: str,
        sub_chapter_overview: str,
        location: dict,
        available_npc: list,
        available_landmark: list,
        previous_events: list,
    ):
        prompt = self.prompts.get_prompt("story.generate_sub_chapter_events")(
            chapter_title=chapter_title,
            chapter_overview=chapter_overview,
            sub_chapter_overview=sub_chapter_overview,
            location=location,
            available_npc=available_npc,
            available_landmark=available_landmark,
            previous_events=previous_events,
        )
        return self.generate(prompt)

    @cache_result
    def generate_town_details(
        self,
        town_info: dict,
        level: int,
        world_description: str,
    ):
        prompt = self.prompts.get_prompt("generate_town_details")(
            world_description=world_description,
            town_name=town_info["name"],
            town_description=town_info["description"],
            story_level=level,
        )
        return self.generate(prompt)

    @cache_result
    def generate_field_details(
        self,
        field_info: dict,
        level: int,
        world_description: str,
    ):
        prompt = self.prompts.get_prompt("generate_field_details")(
            world_description=world_description,
            field_name=field_info["name"],
            field_description=field_info["description"],
            story_level=level,
        )
        return self.generate(prompt)

    @cache_result
    def generate_dungeon_details(
        self,
        dungeon_info: dict,
        level: int,
        world_description: str,
    ):
        prompt = self.prompts.get_prompt("generate_dungeon_details")(
            world_description=world_description,
            dungeon_name=dungeon_info["name"],
            dungeon_description=dungeon_info["description"],
            story_level=level,
        )
        return self.generate(prompt)

    def clear_cache(self):
        self.cache = {}
        self.save_cache()

    @cache_result
    def generate_spell_set(
        self,
        world_name: str,
        world_description: str,
        tier_number: int,
        previous_spell_names: list[str] = None,
    ):
        if previous_spell_names is None:
            previous_spell_names = []
        prompt = self.prompts.get_prompt("generate_spell_set")(
            world_name=world_name,
            world_description=world_description,
            tier_number=tier_number,
            previous_spell_names=previous_spell_names,
        )
        return self.generate(prompt)

    @cache_result
    def generate_item_set(
        self,
        world_name: str,
        world_description: str,
        tier_number: int,
        previous_item_names: list[str] = None,
    ):
        if previous_item_names is None:
            previous_item_names = []
        prompt = self.prompts.get_prompt("generate_item_set")(
            world_name=world_name,
            world_description=world_description,
            tier_number=tier_number,
            previous_item_names=previous_item_names,
        )
        return self.generate(prompt)

    @cache_result
    def generate_navigation_text(
        self,
        location_name: str,
        location_description: str,
        party_members: list,
        current_position: list,
        points_of_interest: list,
        move_directions: list,
        look_directions: list,
        border_messages: list,
    ):
        prompt = self.prompts.get_prompt("generate_navigation_text")(
            location_name=location_name,
            location_description=location_description,
            party_members=party_members,
            current_position=current_position,
            points_of_interest=points_of_interest,
            move_directions=move_directions,
            look_directions=look_directions,
            border_messages=border_messages,
        )
        return self.generate(prompt)

    @cache_result
    def generate_cutscene(
        self,
        event_description: str,
        characters: list,
        location_name: str,
        location_description: str,
        past_events: list,
        story_level: int,
        thematic_style: str,
        conversation_length: str,
        event_timing: str = "before_event",
    ):
        prompt = self.prompts.get_prompt("generate_cutscene")(
            event_description=event_description,
            characters=characters,
            location_name=location_name,
            location_description=location_description,
            past_events=past_events,
            story_level=story_level,
            thematic_style=thematic_style,
            conversation_length=conversation_length,
            event_timing=event_timing,
        )
        return self.generate(prompt)

    @cache_result
    def generate_story_so_far(self, past_events: list, thematic_style: str):
        prompt = self.prompts.get_prompt("generate_story_so_far")(
            past_events=past_events,
            thematic_style=thematic_style,
        )
        return self.generate(prompt)

    @cache_result
    def generate_setting(self, setting_seeds: dict):
        prompt = self.prompts.get_prompt("story.generate_setting")(
            setting_seeds=setting_seeds,
        )
        return self.generate(prompt)

    @cache_result
    def generate_protagonist(self, world_description: str, protagonist_seeds: dict):
        prompt = self.prompts.get_prompt("story.generate_protagonist")(
            world_description=world_description,
            protagonist_seeds=protagonist_seeds,
        )
        return self.generate(prompt)

    @cache_result
    def generate_story(
        self,
        world_description: str,
        protagonist_info: dict,
        story_seeds: dict,
        possible_personalities: list,
    ):
        prompt = self.prompts.get_prompt("story.generate_story")(
            world_description=world_description,
            protagonist_info=protagonist_info,
            story_seeds=story_seeds,
            possible_ally_personalities=possible_personalities,
        )
        return self.generate(prompt)

    @cache_result
    def generate_npc_data(
        self,
        npc_name: str,
        example_dialogue: str,
        location: dict,
        story_level: int,
        npc_type: str,
    ):
        prompt = self.prompts.get_prompt("generate_npc_data")(
            npc_name=npc_name,
            example_dialogue=example_dialogue,
            location_name=location["name"],
            location_description=location["description"],
            story_level=story_level,
            npc_type=npc_type,
        )
        return self.generate(prompt)


def get_llm():
    return LLM()
