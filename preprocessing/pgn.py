import pyparser

import re

from collections import namedtuple
from datetime import datetime


# --------------
# Helper defines
# --------------

# Player related defines
Player = namedtuple("Player", ["name", "rating"])

# Game related defines
TimeControl = namedtuple("TimeControl", ["base_m", "increment_s"])
Opening = namedtuple("Opening", ["name", "eco"])


# ----------
# Game class
# ----------

# An adapter class Parser class
# - Customized specifically for processing lichess games
class Game():

    def __init__(self, game_data: pyparser.Parser):
        self.data = game_data

    # Returns an unique game ID from lichess site
    # - Allows to use lichess API to get more details about the game
    def id(self) -> str:
        match = re.search(r"https://lichess\.org/([a-zA-Z0-9]+)", self.data.header("Site"))
        return match.group(1)
    
    def timestamp(self) -> datetime:
        utc_date = self.data.header("UTCDate")
        utc_time = self.data.header("UTCTime")
        
        return datetime.strptime(f"{utc_date} {utc_time}", "%Y.%m.%d %H:%M:%S")

    # Returns the tempo of the game, that is 'bullet', 'blitz', 'rapid', etc.
    def tempo(self) -> str:
        parts = self.data.header("Event").split()
        return " ".join(parts[1:-1]).lower()
    
    # Returns exact time control of the game
    def time_control(self) -> TimeControl:
        parts = self.data.header("TimeControl").split('+')
        return TimeControl(int(parts[0]) // 60, int(parts[1]))
    
    # Returns an encoded opening variation (for example: 'B32' for Sicilian Defense: Accelerated Dragon)
    def opening(self) -> str:
        return Opening(self.data.header("Opening"), self.data.header("ECO"))
    
    # Returns 1 for a white win, -1 for a black win, and 0 for a draw
    def result(self) -> int:
        if self.data.header("Result") == "1-0":
            return 1
        elif self.data.header("Result") == "0-1":
            return -1
        else:
            return 0
    
    # Returns data for player playing with given side
    def player(self, white: bool = True) -> Player:
        player_nickname = self.data.header("White") if white else self.data.header("Black")
        player_rating = int(self.data.header("WhiteElo")) if white else int(self.data.header("BlackElo"))
        return Player(player_nickname, player_rating)
    
    # Returns a list of both players participating in a game
    def players(self) -> list[Player]:
        return [self.player(white=True), self.player(white=False)]