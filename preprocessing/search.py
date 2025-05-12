from . import pgn
from . import reader

import random

from collections import defaultdict
from typing import Callable, List, Tuple


# -----------------------------------------
# Helper functions - search game predicates
# -----------------------------------------

def is_std_rapid_10_minutes_with_eval(game: pgn.Game) -> bool:
    return game.tempo() == "rapid" and game.time_control().base_m == 10 and "forfeit" not in game.termination() and game.data.has_evals()


# ------------------
# Search for players
# ------------------

# Attempts to find a given amount of players with appropriate number of games that meet some criterion
def find_players(game_repo: reader.GameReader, 
                 game_criterion: Callable[[pgn.Game], bool],
                 k_players: int = 1,
                 rating_buckets: List[Tuple[int, int, int]] = [],
                 min_games: int = 1,
                 verbose: bool = False,
                 logging_frequency: int = 10000) -> list[pgn.Player]:
    '''
    Parameters explanation:
    - game_repo: PGN game reader
    - game_criterion: a predicate function which selects only games that meet some criteria
    - k_players: expected number of players to find
    - rating_buckets: specifies minimum amount of players for given rating ranges (rating_min, rating_max, no_players)
    - min_games: minimum amount of games that meet given criteria, played by a player
    '''

    print("[ Search for players started ]")

    # Initialize player set and player-game counters
    players = defaultdict(lambda: 0)    # Player-game counters
    selected_players = set()            # Player set

    # Keep the count of total amount of found players, as well as separate counters for each rating bucket
    found = 0
    to_find = [cnt for _, _, cnt in rating_buckets]     # If a value goes to 0, then it means we found enough players for given bucket

    for id, game in enumerate(game_repo):
        # Check if game meets required assumptions
        if game_criterion(game):
            for player in game.players():
                # Only human players
                # - NOTE: This is a dubious heuristic, but should make the job
                if "bot" in player.name.lower():
                    continue

                # Update game counters
                players[player.name] += 1

                # If min_games has been found for the player, he become a candidate for selection
                # - NOTE: We compare player's rating only at the last game played, which should result in more representative estimation
                if players[player.name] == min_games:
                    found += 1

                    rbucket_idx = next((i for i, x in enumerate(rating_buckets) if x[0] <= player.rating <= x[1]), -1)

                    if rbucket_idx != -1:
                        to_find[rbucket_idx] -= 1
                        if to_find[rbucket_idx] >= 0:
                            selected_players.add(player.name)
        
        # If we found enough players, we can end the search here
        if found >= k_players and all(cnt <= 0 for cnt in to_find):
            break

        # Some debugging info
        if verbose and (id + 1) % logging_frequency == 0:
            print(f"Processed {id + 1} games, found {found} players...")
    
    print("[ Search for players ended ]")
    
    # We have already selected some players within rating buckets
    # Now it's time to select remaining players with at least min_games played
    # - Let's randomly permutate players first
    players = list(players.items())
    random.shuffle(players)

    for name, no_games in players:
        if no_games >= min_games:
            selected_players.add(name)
        
        if len(selected_players) == k_players:
            break

    return list(selected_players)
