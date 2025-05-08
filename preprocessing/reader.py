import io
import chess.pgn
import zstandard as zstd

from . import pgn


# -----------
# Game reader
# -----------

# Game reader provides a generator-like interface for reading and parsing games from PGN notation
# - Uses zstandard library to open .zst package
class GameReader:
    def __init__(self, input_file: str, max_games: int = 10):
        self.input_file = input_file
        self.max_games = max_games

        # Those variables will be initialized at entering `with` clause
        self.file = None
        self.dctx = None
        self.reader = None
        self.text_reader = None
    
    # Context menager interface - enter
    # - Allows to use reader inside the 'with' closure
    def __enter__(self):
        # Initialize key variables
        self.file = open(self.input_file, "rb")                             # Binary format by default
        self.dctx = zstd.ZstdDecompressor()
        self.reader = self.dctx.stream_reader(self.file, read_size=1 << 20) # 1 mb
        self.text_reader = io.TextIOWrapper(self.reader, encoding='utf-8')  # Python-chess library requires TextIO input

        print(f"Reading {self.input_file} started...")

        return self

    # Generator interface - yielding next game (as pgn.Game adapter class)
    def __iter__(self):
        for _ in range(self.max_games):
            game = chess.pgn.read_game(self.text_reader)

            # Indicates end of file or some critical error
            # - In both cases, we want to end the reading
            if not game:
                print(f"Reading {self.input_file} finished...")
                break

            yield pgn.Game(game)
    
    # Context menager interface - exit
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.text_reader:
            self.text_reader.close()
        if self.reader:
            self.reader.close()
        if self.file:
            self.file.close()