"""Save-game file utilities."""

import json
import os
from datetime import datetime


def get_saves_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")


# Creates the saves directory if it does not exist.
def ensure_saves_dir():
    saves_dir = get_saves_dir()
    os.makedirs(saves_dir, exist_ok=True)
    return saves_dir


# Lists JSON save files for the load-game screen.
def list_save_files():
    saves_dir = ensure_saves_dir()
    return sorted(
        file_name for file_name in os.listdir(saves_dir)
        if file_name.endswith(".json")
    )


# Serializes the current game state into a JSON save file.
def save_game_state(game_state):
    saves_dir = ensure_saves_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(
        character if character.isalnum() or character in ["-", "_"] else "_"
        for character in game_state.player.name
    )
    file_name = f"{safe_name}_turn_{game_state.turn}_{timestamp}.json"
    save_path = os.path.join(saves_dir, file_name)

    with open(save_path, "w", encoding="utf-8") as save_file:
        json.dump(game_state.to_dict(), save_file, ensure_ascii=False, indent=2)

    return file_name


# Reads a save file and rebuilds a GameState object.
def load_game_state(file_name):
    save_path = os.path.join(get_saves_dir(), file_name)

    with open(save_path, "r", encoding="utf-8") as save_file:
        data = json.load(save_file)

    from game_state import GameState

    return GameState.from_dict(data)


# Deletes one save file from the saves directory.
def delete_save_file(file_name):
    save_path = os.path.join(get_saves_dir(), file_name)
    if os.path.exists(save_path):
        os.remove(save_path)
