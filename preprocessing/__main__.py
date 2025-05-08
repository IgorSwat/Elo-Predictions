from . import pgn
from . import reader
from . import search
from . import visual

import yaml

from collections import defaultdict


# ---------------
# Main processing
# ---------------

if __name__ == "__main__":
    # First of all, load config file
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    with reader.GameReader(config["paths"]["data_raw"], max_games=10) as game_repo:
        for game in game_repo:
            print(game.data, end="\n\n")
        # players = search.find_players(
        #     game_repo, 
        #     game_criterion=lambda game: game.tempo() == "rapid" and game.time_control().base_m == 10,
        #     k_players=50,
        #     min_games=5,
        #     verbose=True
        # )

        # print("Players that meet the criterion:")
        # print(players)