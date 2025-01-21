from src.game.response_manager import choose_option
from src.game.response_manager import print_event_text


class MenuManager:
    def __init__(self, game):
        self.game = game

    async def show_main_menu(self):
        options = ["Create a new dream"]
        titles, _ = self.game.save_manager.get_all_dream_titles()
        if titles:
            options.append("List dreams")

        choice = await choose_option(
            options,
            prompt=self.game.base_title,
            allow_exit=False,
            input_type="title",
            background_image_url=self.game.title_screen_image,
        )

        if choice == "Create a new dream":
            await self.game.new_game()
            await self.game.start_game()
        elif choice == "List dreams":
            await self.show_dream_list()

    async def show_dream_list(self):
        dream_titles, dream_descriptions = self.game.save_manager.get_all_dream_titles()

        if not dream_titles:
            await print_event_text(
                "No Dreams Found",
                "There are no saved dreams available. Create a new dream to begin your journey.",
            )
            await self.show_main_menu()
            return

        choice = await choose_option(
            dream_titles,
            prompt="Select a dream...",
            allow_exit=True,
            exit_option="Back",
            option_details=dream_descriptions,
            background_image_url=self.game.title_screen_image,
        )

        if choice in dream_titles:
            await self.show_dream_menu(choice)
        else:
            await self.show_main_menu()

    async def show_dream_menu(self, dream_title):
        saves = self.game.save_manager.get_saves_for_title(dream_title)
        title_image = self.game.save_manager.get_title_image(dream_title)

        options = []
        if saves["initial"]:
            options.append("Start Dream Anew")
        if saves["ongoing"]:
            options.append("Continue Dream")

        choice = await choose_option(
            options,
            prompt=dream_title,
            option_details=[],
            allow_exit=True,
            exit_option="Back",
            input_type="title",
            background_image_url=title_image,
        )

        if choice == "Start Dream Anew":
            self.game.load_game_state(saves["initial"]["filepath"])
            await self.game.start_game()
        elif choice == "Continue Dream":
            await self.select_save_file(saves["ongoing"])
        else:
            await self.show_dream_list()

    async def select_save_file(self, saves):
        options = [
            f"{self.game.save_manager.format_timestamp(save['timestamp'])}"
            for save in saves
        ]
        title_image = self.game.save_manager.get_title_image(saves[0]["title"])
        choice = await choose_option(
            options,
            prompt=f"Select a save file...",
            allow_exit=True,
            exit_option="Back",
            option_details=[
                f"Chapter: {save['current_chapter']+1}\nCurrent Objective: {save['current_objective']}"
                for save in saves
            ],
            background_image_url=title_image,
        )

        if choice in options:
            selected_save = saves[options.index(choice)]
            self.game.load_game_state(selected_save["filepath"])
            await self.game.start_game()
        else:
            await self.show_dream_menu(saves[0]["title"])
