from src.game.response_manager import ResponseManager, choose_option
from src.api.llm import get_llm
from src.travel.world import World
from src.game.seeding import collect_seed_answers, PROTAGONIST_QUESTIONS
from src.core.spells import SpellManager
from src.core.items import ItemManager
from src.npc.cast import CastManager
from src.npc.npc import NPC
from src.core.player_party import initialize_party
from src.game.save_manager import SaveManager
from src.game.response_manager import print_event_text
from src.core.character import equip_starter_gear
from src.game.menu_manager import MenuManager

import random


class JRPG:
    def __init__(self):
        self.base_title = "One Trillion and One Nights"
        self.title = self.base_title
        self.use_seed = True
        self.party = None
        self.world = None
        self.spell_manager: SpellManager = SpellManager()
        self.item_manager: ItemManager = ItemManager()
        self.cast: CastManager = CastManager()
        self.response_manager: ResponseManager = ResponseManager()
        self.save_manager: SaveManager = SaveManager()
        self.menu_manager: MenuManager = MenuManager(self)
        self.title_screen_image = "./images/menu.png"

    async def run_game(self):
        await self.menu_manager.show_main_menu()

    async def new_game(self):
        self.cast.clear()
        game_data = await self._generate_game_data()
        await self._initialize_game_systems(game_data)
        await self._setup_first_chapter(game_data)
        self.save_game_state(self.save_manager.DREAM_DIR)

    async def _generate_game_data(self):
        seed_answers = await collect_seed_answers() if self.use_seed else None
        setting = get_llm().generate_setting(seed_answers.get("setting", {}))
        protagonist = get_llm().generate_protagonist(
            setting["world_description"], seed_answers.get("protagonist", {})
        )
        protagonist["chosen_class"] = seed_answers.get("protagonist", {}).get(
            "What is the protagonist's personality?"
        )
        possible_personalities = PROTAGONIST_QUESTIONS[1]["answers"]
        possible_personalities.remove(protagonist["chosen_class"])
        random.shuffle(possible_personalities)
        story = get_llm().generate_story(
            setting,
            protagonist,
            seed_answers.get("story", {}),
            possible_personalities,
        )

        return {"setting": setting, "protagonist": protagonist, "story": story}

    async def _initialize_game_systems(self, game_data):
        self.title = game_data["story"]["title"]
        self.brief_overview = game_data["story"]["brief_overview"]
        self.chapter_overviews = game_data["story"]["chapters"]

        self.world = World(
            game_data["setting"]["world_name"],
            game_data["setting"]["world_description"],
        )

        await choose_option(
            ["Start Dream"],
            self.title,
            input_type="title",
            allow_exit=False,
            background_image_url=self.world.title_screen_image,
        )

        self._initialize_spells_and_items()

        self.party = await initialize_party(
            game_data["protagonist"],
            initial_level=5,
            thematic_style=game_data["story"]["thematic_style"],
            currency_name=game_data["setting"]["currency_name"],
            initial_class=game_data["protagonist"]["chosen_class"],
            starting_currency=500,
        )

    def _initialize_spells_and_items(self):
        tier_1_spell_data = get_llm().generate_spell_set(
            self.world.name,
            self.world.description,
            1,
        )
        tier_1_item_data = get_llm().generate_item_set(
            self.world.name,
            self.world.description,
            1,
        )
        self.spell_manager.initialize({"tier_1": tier_1_spell_data})
        self.item_manager.initialize({"tier_1": tier_1_item_data})

    async def _setup_first_chapter(self, game_data):
        await self._setup_next_chapter()
        await equip_starter_gear(
            self.party.leader,
            self.world.possible_locations[0],
            story_level=1,
        )
        game_data["protagonist"]["name"] = self.party.leader.name
        game_data["protagonist"]["description"] = self.party.leader.description
        game_data["protagonist"]["type"] = "ally"
        self.cast.add_npc(
            NPC(
                game_data["protagonist"],
                {"name": "Party", "description": "wherever you are"},
                portrait=self.party.leader.portrait,
            )
        )
        self.world.update_current_location(self.party)

    async def start_game(self):
        while True:
            result = await self.world.visit_current_location(self.party)

            if result == "save_and_exit":
                self.save_game_state(self.save_manager.SAVE_DIR)
                await self.menu_manager.show_main_menu()
                break
            elif result == "game_over":
                await self.menu_manager.show_main_menu()
                break
            elif result == "chapter_complete":
                if (
                    self.party.story_manager.current_chapter
                    < len(self.chapter_overviews) - 1
                ):
                    await self.generate_next_chapter()
                else:
                    await self.complete_game()
                    break
            elif result == self.world.next_location:
                self.world.advance_location(self.party)
            elif result == self.world.previous_location:
                self.world.retreat_location(self.party)

    async def complete_game(self):
        await print_event_text(
            "Congratulations! You've completed the game!",
            "Thank you for playing One Trillion and One Nights!",
            background_image_url=self.title_screen_image,
        )
        await self.menu_manager.show_main_menu()

    async def generate_next_chapter(self):
        self.party.story_manager.advance_chapter()
        await self._generate_new_tier_content()
        await self._setup_next_chapter()
        self.save_game_state(self.save_manager.SAVE_DIR)

    async def _generate_new_tier_content(self):
        chapter_tier = self.party.story_manager.current_chapter + 1
        existing_spell_names = self.spell_manager.spell_list
        existing_item_names = self.item_manager.item_list

        new_spell_data = get_llm().generate_spell_set(
            self.world.name,
            self.world.description,
            chapter_tier,
            existing_spell_names,
        )

        new_item_data = get_llm().generate_item_set(
            self.world.name,
            self.world.description,
            chapter_tier,
            existing_item_names,
        )

        self.spell_manager.spell_set[f"tier_{chapter_tier}"] = new_spell_data
        self.item_manager.item_set[f"tier_{chapter_tier}"] = new_item_data

        self.spell_manager.initialize(self.spell_manager.spell_set)
        self.item_manager.initialize(self.item_manager.item_set)

    async def _setup_next_chapter(self):
        # Generate chapter data
        chapter_setup = await self._generate_chapter_setup()

        # Process locations and NPCs
        for sub_chapter in chapter_setup["sub_chapters"]:
            self._prepare_sub_chapter(sub_chapter, chapter_setup)

        # Update game state
        await self._update_game_state(chapter_setup)

    async def _generate_chapter_setup(self):
        prev_chapter_overview = (
            self.chapter_overviews[self.party.story_manager.current_chapter - 1][
                "overview"
            ]
            if self.party.story_manager.current_chapter > 0
            else "None. This is the first chapter."
        )

        return get_llm().generate_chapter_setup(
            self.world.description,
            self.world.list_locations,
            [char.basic_info() for char in self.party.characters],
            (self.party.story_manager.current_chapter + 1) * 5,
            self.party.story_manager.current_chapter + 1,
            self.party.story_manager.total_chapters,
            self.chapter_overviews[self.party.story_manager.current_chapter],
            self.party.story_manager.thematic_style,
            prev_chapter_overview,
        )

    def _prepare_sub_chapter(self, sub_chapter, chapter_setup):
        # Set basic sub-chapter info
        sub_chapter["chapter_title"] = chapter_setup["title"]
        sub_chapter["chapter_overview"] = chapter_setup["overview"]

        # Add NPCs if they belong in this location
        self._add_npc_if_present(sub_chapter, chapter_setup["ally_npc"], "ally")
        self._add_npc_if_present(sub_chapter, chapter_setup["story_npc"], "story")
        self._add_npc_if_present(sub_chapter, chapter_setup["boss_npc"], "boss")

        # Handle landmark
        if chapter_setup["landmark"]["location"] == sub_chapter["location"]["name"]:
            sub_chapter["landmark"] = chapter_setup["landmark"]
            sub_chapter["npc"] = {"name": "None", "description": "None"}
        else:
            sub_chapter["landmark"] = {"name": "None", "description": "None"}

    def _add_npc_if_present(self, sub_chapter, npc_data, npc_type):
        if npc_data["location"] == sub_chapter["location"]["name"]:
            if npc_type == "ally":
                npc_data["base_class"] = self.chapter_overviews[
                    self.party.story_manager.current_chapter
                ]["ally_personality"]
            npc_data["type"] = npc_type
            use_location = sub_chapter["location"].copy()
            npc = self.cast.npc_factory.create_npc(
                npc_data,
                current_location=use_location,
                story_level=5 * (self.party.story_manager.current_chapter + 1),
            )
            self.cast.add_npc(npc)
            sub_chapter["npc"] = npc_data

    async def _update_game_state(self, chapter_setup):
        await self.world.add_chapter_locations(chapter_setup)
        self.party.story_manager.add_chapter_overview(chapter_setup)
        self.party.story_manager.generate_sub_chapter_events()

    def save_game_state(self, directory):
        game_state = {
            "spell_manager": self.spell_manager,
            "item_manager": self.item_manager,
            "world": self.world,
            "party": self.party,
            "title": self.title,
            "cast": self.cast,
            "chapter_overviews": getattr(self, "chapter_overviews", None),
            "brief_overview": getattr(self, "brief_overview", None),
            "current_chapter": self.party.story_manager.current_chapter,
            "total_chapters": self.party.story_manager.total_chapters,
        }
        return self.save_manager.save_game_state(game_state, directory)

    def load_game_state(self, filepath):
        game_state = self.save_manager.load_game_state(filepath)

        required_keys = [
            "spell_manager",
            "item_manager",
            "world",
            "party",
            "title",
            "cast",
            "brief_overview",
            "current_chapter",
            "total_chapters",
        ]

        missing_keys = [key for key in required_keys if key not in game_state]
        if missing_keys:
            raise ValueError(f"Save file is missing required data: {missing_keys}")

        for key in required_keys:
            setattr(self, key, game_state[key])

        self.chapter_overviews = game_state.get("chapter_overviews")
