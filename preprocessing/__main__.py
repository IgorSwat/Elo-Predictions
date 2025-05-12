from . import final
from . import pgn
from . import reader
from . import search
from . import visual

import pyparser

import yaml
import sys

from collections import defaultdict


# ---------------
# Main processing
# ---------------

if __name__ == "__main__":
    # First of all, load config file
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Maximum number of games processed from raw input data file
    max_games = int(sys.argv[1]) if sys.argv[1] != "all" else 90000000

    input_filepath = config["paths"]["data_raw"] if "final" not in sys.argv else config["paths"]["data_games"]

    with (reader.ZstdQuickReader if "final" not in sys.argv else reader.StandardSlowReader)(input_filepath, max_games=max_games) as game_repo:
        if "data" in sys.argv:
            for id, game in enumerate(game_repo):
                if "final" not in sys.argv:
                    print(game.data.all_data())
                else:
                    print(game.data)
        elif "players" in sys.argv:
            rating_buckets = [
                (0, 1000, 1000),
                (1000, 1300, 1000),
                (1400, 1700, 1000),
                (1800, 2100, 1000),
                (2200, 2500, 500),
                (2500, 3000, 10)
            ]

            players = search.find_players(
                game_repo, 
                game_criterion=search.is_std_rapid_10_minutes_with_eval,
                k_players=config["target_size"],
                rating_buckets=rating_buckets,
                min_games=config["target_gpp"],
                verbose=True
            )

            players.sort()

            print(f"Found {len(players)}!\n")

            with open("players.txt", "w", encoding="utf-8") as f:
                for player_name in players:
                    f.write(player_name + "\n")
        elif "games" in sys.argv:
            # First, let's get all the players we want to find games for
            players = {}         # Player-game counters (But this time with fixed number of keys)

            with open(config["paths"]["data_players"], "r") as file:
                print(f"[ Reading {config["paths"]["data_players"]} started ]")

                for line in file:
                    player_name = line.strip()
                    players[player_name] = 0
            
            print(f"[ Reading {config["paths"]["data_players"]} finished ]")

            # Number of players with complete set of games found
            found = 0
            games_saved = 0

            # Now start reading games and simultaneously saving them into an output file
            with open("games.pgn", "w") as output:
                print(f"[ Searching for games started ]")
                
                for game in game_repo:
                    if not search.is_std_rapid_10_minutes_with_eval(game):
                        continue

                    saved = False

                    for player in game.players():
                        if player.name in players.keys():
                            players[player.name] += 1

                            if players[player.name] == config["target_gpp"]:
                                found += 1

                            if not saved and players[player.name] <= config["target_gpp"]:
                                output.write(game.data.all_data().strip() + "\n\n")
                                saved = True
                                games_saved += 1
                    
                    if found == len(players.keys()):
                        break
                    
                print(f"[ Searching for games finished ]")
            
            print(f"Saved {games_saved} games to games.pgn")
        elif "final" in sys.argv:
            dataset_raw = final.create_dataset(
                game_repo,
                engine_filepath=None,
                book_filepath=config["paths"]["opening_book"],
                engine_max_depth=10,
                gpp=config["target_gpp"],
                verbose=True,
                logging_frequency=1000
            )

            df = final.create_dataframe(dataset_raw)

            print(df.head(5))

            df.to_csv(config["paths"]["data_final"], index=False)
            print(f"Saved dataset to {config["paths"]["data_final"]}")