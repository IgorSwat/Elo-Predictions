import chess
import chess.pgn
import re

from collections import namedtuple


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

# An adapter class for chess.pgn.Game
# - Customized specifically for processing lichess games
class Game():

    def __init__(self, game: chess.pgn.Game):
        self.data = game

    # Returns an unique game ID from lichess site
    # - Allows to use lichess API to get more details about the game
    def id(self) -> str:
        if "GameId" in self.data.headers:
            return self.data.headers["GameId"]
        else:
            match = re.search(r"https://lichess\.org/([a-zA-Z0-9]+)", self.data.headers["Site"])
            return match.group(1)

    # Returns the tempo of the game, that is 'bullet', 'blitz', 'rapid', etc.
    def tempo(self) -> str:
        parts = self.data.headers["Event"].split()
        return " ".join(parts[1:-1]).lower()
    
    # Returns exact time control of the game
    def time_control(self) -> TimeControl:
        parts = self.data.headers["TimeControl"].split('+')
        return TimeControl(int(parts[0]) // 60, int(parts[1]))
    
    # Returns an encoded opening variation (for example: 'B32' for Sicilian Defense: Accelerated Dragon)
    def opening(self) -> str:
        return Opening(self.data.headers["Opening"], self.data.headers["ECO"])
    
    # Returns 1 for a white win, -1 for a black win, and 0 for a draw
    def result(self) -> int:
        if self.data.headers["Result"] == "1-0":
            return 1
        elif self.data.headers["Result"] == "0-1":
            return -1
        else:
            return 0
    
    # Returns data for player playing with given side
    def player(self, color: chess.Color = chess.WHITE) -> Player:
        player_nickname = self.data.headers["White"] if color == chess.WHITE else self.data.headers["Black"]
        player_rating = self.data.headers["WhiteElo"] if color == chess.WHITE else self.data.headers["BlackElo"]
        return Player(player_nickname, player_rating)
    
    # Returns a list of both players participating in a game
    def players(self) -> list[Player]:
        return [self.player(chess.WHITE), self.player(chess.BLACK)]