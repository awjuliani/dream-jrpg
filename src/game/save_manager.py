import os
import pickle
import glob
from datetime import datetime


class SaveManager:
    def __init__(self):
        self.SAVE_DIR = "data/ongoing_saves"
        self.DREAM_DIR = "data/initial_saves"

        # Ensure both directories exist
        for directory in [self.SAVE_DIR, self.DREAM_DIR]:
            os.makedirs(directory, exist_ok=True)

    def save_game_state(self, game_state, directory=None):
        """Save game state to specified directory"""
        if directory is None:
            directory = self.SAVE_DIR

        # Add version information
        game_state["save_version"] = "1.0"  # Update this when save format changes

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{game_state['title']}_{timestamp}.pkl"
        safe_filename = "".join(
            c for c in filename if c.isalnum() or c in ["_", "-", "."]
        ).lower()

        filepath = os.path.join(directory, safe_filename)

        # Backup existing file if it exists
        if os.path.exists(filepath):
            backup_path = filepath + ".backup"
            try:
                os.replace(filepath, backup_path)
            except OSError as e:
                print(f"Warning: Failed to create backup: {str(e)}")

        with open(filepath, "wb") as file:
            game_state["timestamp"] = timestamp
            pickle.dump(game_state, file)
        return filepath

    def load_game_state(self, filepath):
        """Load game state from file"""
        with open(filepath, "rb") as file:
            return pickle.load(file)

    def get_saved_games(self, directory):
        """Get list of available saved games from directory"""
        files = glob.glob(os.path.join(directory, "*.pkl"))
        saved_games = []
        for file in files:
            try:
                with open(file, "rb") as f:
                    data = pickle.load(f)
                    saved_games.append(
                        {
                            "title": data["title"],
                            "timestamp": data["timestamp"],
                            "filepath": file,
                            "brief_overview": data.get("brief_overview"),
                            "current_chapter": data.get("current_chapter", 0),
                            "current_objective": (
                                data["party"].story_manager.next_event.trigger_hint
                                if data["party"].story_manager.next_event
                                else None
                            ),
                            "title_screen_image": data["world"].title_screen_image,
                        }
                    )
            except (EOFError, pickle.UnpicklingError) as e:
                print(f"Warning: Failed to load save file {file}: {str(e)}")
                continue
            except KeyError as e:
                print(f"Warning: Save file {file} is missing required data: {str(e)}")
                continue
        return saved_games

    def format_timestamp(self, timestamp):
        """Convert a timestamp string to a human-readable format."""
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        return dt.strftime("%B %d, %Y %I:%M %p")

    def load_title_from_save(self, save_dir):
        """Load title and title screen image from most recent save file in directory"""
        saved_games = self.get_saved_games(save_dir)
        if saved_games:
            # Sort by timestamp to get most recent
            latest_save = sorted(
                saved_games, key=lambda x: x["timestamp"], reverse=True
            )[0]
            return latest_save["title"], latest_save.get(
                "title_screen_image", "./images/menu.png"
            )
        return None, "./images/menu.png"

    def _is_safe_path(self, directory, filename):
        """Validate that the resulting path is within the intended directory"""
        intended_path = os.path.abspath(os.path.join(directory, filename))
        directory_path = os.path.abspath(directory)
        return intended_path.startswith(directory_path)

    def get_all_dream_titles(self):
        """Get a list of unique dream titles that have saves"""
        all_saves = self.get_saved_games(self.SAVE_DIR)
        all_dreams = self.get_saved_games(self.DREAM_DIR)

        # Combine and get unique titles
        all_titles = list(set(game["title"] for game in all_saves + all_dreams))
        all_descriptions = list(game["brief_overview"] for game in all_dreams)
        return all_titles, all_descriptions

    def get_saves_for_title(self, title):
        """Get all saves (both initial and ongoing) for a specific title"""
        ongoing_saves = [
            save
            for save in self.get_saved_games(self.SAVE_DIR)
            if save["title"] == title
        ]
        # Sort ongoing saves by timestamp in descending order (newest first)
        ongoing_saves.sort(key=lambda x: x["timestamp"], reverse=True)

        initial_save = [
            save
            for save in self.get_saved_games(self.DREAM_DIR)
            if save["title"] == title
        ]
        return {
            "ongoing": ongoing_saves,
            "initial": initial_save[0] if initial_save else None,
        }

    def get_title_image(self, title):
        """Get the title image for a specific title"""
        initial_save = [
            save
            for save in self.get_saved_games(self.DREAM_DIR)
            if save["title"] == title
        ]
        return initial_save[0]["title_screen_image"] if initial_save else None
