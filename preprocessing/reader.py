from . import pgn

import pyparser

import io
import chess.pgn
import zstandard as zstd

from abc import ABC, abstractmethod
from typing import Any, override


# ---------------------
# Game reader interface
# ---------------------

# Game reader provides a generator-like interface for reading and parsing games from PGN notation
# - Abstract base class for other readers
class GameReader(ABC):
    def __init__(self, input_file: str, max_games: int = 10):
        self.input_file = input_file
        self.max_games = max_games
    
    # Context menager interface - enter
    # - Allows to use reader inside the 'with' closure
    def __enter__(self):
        # Initialize key variables
        self._initialize()

        print(f"Reading {self.input_file} started...")

        return self

    # Generator interface - yielding next game (as pgn.Game adapter class)
    def __iter__(self):
        for _ in range(self.max_games):
            game = self._next_game()

            # Indicates end of file or some critical error
            # - In both cases, we want to end the reading
            if game is None:
                print(f"Reading {self.input_file} finished...")
                break

            # WARNING - This is very dangerous to allow all games have shared memory in form of Parser object
            yield game

    # Abstract method 1 - initializing reader components
    @abstractmethod
    def _initialize(self) -> None:
        pass

    # Abstract method 2 - producing new game
    @abstractmethod
    def _next_game(self) -> pgn.Game | None:
        pass


# ------------------------------
# Standard game reader interface
# ------------------------------

# Allows to read games from standard PGN file
class StandardReader(GameReader):
    def __init__(self, input_file: str, max_games: int = 10):
        super().__init__(input_file, max_games)

        self.file = None
    
    @override
    def _initialize(self):
        self.file = open(self.input_file, "r")      # Standard text format
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()


# --------------------------
# Zstd game reader interface
# --------------------------

# Allows to read games from compressed .zstd file
class ZstdReader(GameReader):
    def __init__(self, input_file: str, max_games: int = 10):
        super().__init__(input_file, max_games)

        self.file = None
        self.dctx = None
        self.reader = None
    
    @override
    def _initialize(self):
        self.file = open(self.input_file, "rb")      # Binary format
        self.dctx = zstd.ZstdDecompressor()
        self.reader = self.dctx.stream_reader(self.file, read_size=1 << 16) # 16kB
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.reader:
            self.reader.close()
        if self.file:
            self.file.close()


# --------------------
# Standard slow reader
# --------------------

# Standard reader, using python-chess as PGN parsing mechanism
class StandardSlowReader(StandardReader):
    @override
    def _next_game(self):
        return pgn.Game(chess.pgn.read_game(self.file))


# -----------------
# Zstd quick reader
# -----------------

# zstd-based reader, using efficient custom PGN parser written in C++
class ZstdQuickReader(ZstdReader):
    def __init__(self, input_file, max_games = 10):
        super().__init__(input_file, max_games)

        self.parser = None
    
    @override
    def _initialize(self):
        super()._initialize()

        self.parser = pyparser.Parser(self.reader)
    
    @override
    def _next_game(self):
        success = self.parser.parse_next()

        return pgn.Game(self.parser) if success else None
