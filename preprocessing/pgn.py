import pyparser

import chess.pgn
import re

from collections import namedtuple
from datetime import datetime
from typing import Any


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
# - Works with either custom implementation of PGN parser or python-chess objects
class Game():

    def __init__(self, game_data: pyparser.Parser | chess.pgn.Game):
        self.data = game_data

    # Returns an unique game ID from lichess site
    # - Allows to use lichess API to get more details about the game
    def id(self) -> str:
        match = re.search(r"https://lichess\.org/([a-zA-Z0-9]+)", self.__header("Site"))
        return match.group(1)
    
    def timestamp(self) -> datetime:
        utc_date = self.__header("UTCDate")
        utc_time = self.__header("UTCTime")
        
        return datetime.strptime(f"{utc_date} {utc_time}", "%Y.%m.%d %H:%M:%S")

    # Returns the tempo of the game, that is 'bullet', 'blitz', 'rapid', etc.
    def tempo(self) -> str:
        parts = self.__header("Event").split()
        return " ".join(parts[1:-1]).lower()
    
    # Returns exact time control of the game
    def time_control(self) -> TimeControl:
        parts = self.__header("TimeControl").split('+')
        return TimeControl(int(parts[0]) // 60, int(parts[1]))

    def termination(self) -> str:
        return self.__header("Termination")
    
    # Returns an encoded opening variation (for example: 'B32' for Sicilian Defense: Accelerated Dragon)
    def opening(self) -> str:
        return Opening(self.__header("Opening"), self.__header("ECO"))
    
    # Returns 1 for a white win, -1 for a black win, and 0 for a draw
    def result(self) -> int:
        if self.__header("Result") == "1-0":
            return 1
        elif self.__header("Result") == "0-1":
            return -1
        else:
            return 0
    
    # Returns data for player playing with given side
    def player(self, white: bool = True) -> Player:
        player_nickname = self.__header("White") if white else self.__header("Black")
        player_rating = int(self.__header("WhiteElo")) if white else int(self.__header("BlackElo"))
        return Player(player_nickname, player_rating)
    
    # Returns a list of both players participating in a game
    def players(self) -> list[Player]:
        return [self.player(white=True), self.player(white=False)]
    
    # A helper function to unify both cases of underlying game_data
    def __header(self, key: str) -> Any:
        if isinstance(self.data, chess.pgn.Game):
            return self.data.headers[key]
        else:
            return self.data.header(key)