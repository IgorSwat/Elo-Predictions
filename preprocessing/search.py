from . import pgn
from . import reader

from collections import defaultdict
from datetime import datetime
from typing import Callable


# ------------------
# Search for players
# ------------------

# Attempts to find a given amount of players with appropriate number of games that meet some criterion
def find_players(game_repo: reader.GameReader, 
                 game_criterion: Callable[[pgn.Game], bool],
                 k_players: int = 1,
                 min_games: int = 1,
                 verbose: bool = False,
                 logging_frequency: int = 10000) -> list[pgn.Player]:
    print("[ Search for players started ]")

    # Start with a dict to count number of desired games for each player
    players = defaultdict(lambda: 0)

    # Keep the count of already found players
    count = 0

    for id, game in enumerate(game_repo):
        # Check if game meets required assumptions
        if game_criterion(game):
            for player in game.players():
                players[player.name] += 1

                if players[player.name] == min_games:
                    count += 1
        
        # If we found enough players, we can end the search here
        if count >= k_players:
            break

        # Some debugging info
        if verbose and (id + 1) % logging_frequency == 0:
            print(f"Processed {id + 1} games, found {count} players...")
    
    print("[ Search for players ended ]")
    
    # Now it's time to select only players with score >= min_games
    selected_players = [name for name, cnt in players.items() if cnt >= min_games]

    return selected_players
