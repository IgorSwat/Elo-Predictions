from . import pgn
from . import reader

import chess
import matplotlib.pyplot as plt

from collections import defaultdict


# -----------------------
# Game info visualization
# -----------------------

# Prints some basic info from game headers:
# - Players, ratings, time control, result
def game_info(game: pgn.Game) -> None:
    print(f"---------- Game {game.id()} ----------")
    print(f"Time control: {game.tempo()}, {game.time_control().base_m} min + {game.time_control().increment_s} s")
    print(f"Players: {game.player(chess.WHITE).name} {game.data.header("Result")} {game.player(chess.BLACK).name}")


# -------------------------
# Time control distribution
# -------------------------

# Plots the histogram of time control distribution among given batch of games
# - Number of analyzed games is determined by one of GameReader's parameter
# - Helps to decide for what time control to collect data
def time_control_distribution(game_repo: reader.GameReader) -> None:
    time_controls = [
        ("blitz", pgn.TimeControl(3, 0)),
        ("blitz", pgn.TimeControl(3, 2)),
        ("blitz", pgn.TimeControl(5, 3)),
        ("rapid", pgn.TimeControl(10, 0)),
        ("rapid", pgn.TimeControl(10, 5)),
        ("rapid", pgn.TimeControl(15, 10)),
    ]

    games_found = defaultdict(lambda: 0)

    for game in game_repo:
        for time_control in time_controls:
            tempo, time = time_control

            if game.tempo() == tempo and game.time_control() == time:
                games_found[f"{tempo} {time[0]}+{time[1]}"] += 1
    
    labels = sorted(list(games_found.keys()))
    counts = [games_found[label] for label in labels]

    # Plot histogram
    plt.figure(figsize=(10, 6))
    plt.bar(labels, counts, color='skyblue')
    plt.xlabel('Time control')
    plt.ylabel('Number of games')
    plt.title('Distribution of chess game control times')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()