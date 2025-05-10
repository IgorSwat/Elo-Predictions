from . import pgn
from . import reader
from . import search
from . import visual

import pyparser

import yaml
import zstandard as zstd
import io

from collections import defaultdict


# ---------------
# Main processing
# ---------------

if __name__ == "__main__":
    # First of all, load config file
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    with reader.GameReader(config["paths"]["data_raw"], max_games=10000) as game_repo:
        # for id, game in enumerate(game_repo):
        #     print(game.data.all_data())

        players = search.find_players(
            game_repo, 
            game_criterion=lambda game: game.tempo() == "rapid" and game.time_control().base_m == 10,
            k_players=10,
            min_games=1,
            verbose=True
        )

        players.sort()

        print("Players that meet the criterion:")
        print(players)