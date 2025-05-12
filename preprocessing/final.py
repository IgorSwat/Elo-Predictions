from . import pgn
from . import reader

import chess
import chess.polyglot
import chess.engine
import pandas as pd

from collections import defaultdict
from dataclasses import dataclass
from math import exp
from typing import Dict


# Some constants
MATE_SCORE = 10000
MAX_CP = 1000


# ---------------------
# Player data structure
# ---------------------

# This structure contains all information calculated during analysis of player's games
@dataclass
class PlayerData:
    name: str = ""
    elo: int = 0

    no_games: int = 0
    no_wins: int = 0
    no_loss: int = 0
    no_moves: int = 0

    cp_loss: int = 0
    no_innacuracies: int = 0
    no_mistakes: int = 0
    no_blunders: int = 0

    time_usage_win: int = 0                 # [s]
    time_usage_loss: int = 0                # [s]
    time_usage_good_move: int = 0           # [s]
    time_usage_innacuracy_mistake: int = 0  # [s]
    time_usage_blunder: int = 0             # [s]

    no_nonterminal_results: int = 0         # Either draws by agreement or resignations
    material_imbalance: int = 0
    no_book_moves: int = 0


# ----------------
# Helper functions
# ----------------

# A sigmoid function to transfer score in CP to (0, 1) probability
def logistic(score: int) -> float:
    scaled = score * 400 / (64 * 255)
    
    return 1.0 / (1.0 + exp(-scaled))

# Helper function to get heuristic material value for a side
def get_material_value(board: chess.Board, color: chess.Color) -> int:
    value = 0

    value += len(board.pieces(chess.PAWN, color)) * 1
    value += len(board.pieces(chess.KNIGHT, color)) * 3
    value += len(board.pieces(chess.BISHOP, color)) * 3
    value += len(board.pieces(chess.ROOK, color)) * 5
    value += len(board.pieces(chess.QUEEN, color)) * 9

    return value


# ----------------------
# Player data processing
# ----------------------

# Calculates all fields of PlayerData structure for each player, based on given games
def create_dataset(game_repo: reader.StandardSlowReader,
                   engine_filepath: str,
                   book_filepath: str,      # .epd format
                   engine_max_depth: int = 10,
                   gpp: int = 10,
                   verbose: bool = False,
                   logging_frequency: int = 1000) -> dict[str, PlayerData]:
    # We store all the calculated properties here (player_name - PlayerData)
    players = defaultdict(PlayerData)

    # Initialize required components - engine & opening book
    engine = None
    book = set()

    if engine_filepath:
        try:
            engine = chess.engine.SimpleEngine.popen_uci(engine_filepath)
        except Exception as e:
            print(f"[ ERROR: Could not initialize chess engine: {e} ]")
            return
    
    if book_filepath:
        book = chess.polyglot.open_reader(book_filepath)
        print(f"[ Succesfully loaded opening book from {book_filepath} ]")

    # Iterate over all games
    for id, game in enumerate(game_repo):
        try:
            p1, p2 = game.players()
        except AttributeError as e:
            break

        # Step 1- update game counter, player name and elo (but only at the last analyzed game for most recent results!)
        for player in [p1, p2]:
            players[player.name].no_games += 1

            if players[player.name].no_games == gpp:
                players[player.name].name = player.name
                players[player.name].elo = player.rating
        
        # Step 2 -update game result counters
        result = game.result()          # 1 for white's win, -1 for black's win, 0 for a draw
        if result == 1:
            players[p1.name].no_wins += 1
            players[p2.name].no_loss += 1
        elif result == -1:
            players[p1.name].no_loss += 1
            players[p2.name].no_wins += 1

        # Step 3 - initialize helper variables to keep track of changing position and clock situation
        board = game.data.board()       # Position

        initial_time_s, increment_s = game.time_control()[0] * 60, game.time_control()[1]
        player_clocks = {chess.WHITE: initial_time_s, chess.BLACK: initial_time_s}          # Clock states

        still_in_book = True if book else False

        # A starting evaluation, assuming we always begin in starting chess position
        # - NOTE: all engine evals are relative!
        last_eval = 20   # [cp]

        # Iterate over all moves from game main line
        for n_move, node in enumerate(game.data.mainline()):
            # Special case - starting position
            # - We can skip starting position from move-specyfic analysis
            if node.parent is None:
                continue

            move = node.move
            assert move is not None, "Node in mainline should have a move"

            mp = p1 if board.turn == chess.WHITE else p2

            # Step 4 - update move counter
            players[mp.name].no_moves += 1

            # Step 5 - calculate time spent on the move
            node_clock_s = node.clock()     # Time remaining for player who just moved (after this move)
            time_spent_on_move = 0

            if node_clock_s is not None:
                time_before_move = player_clocks[board.turn]
                time_spent_on_move = time_before_move + increment_s - node_clock_s

                # Update time counters from players dict
                if result == 1 and board.turn == chess.WHITE:
                    players[p1.name].time_usage_win += time_spent_on_move
                elif result == 1:
                    players[p2.name].time_usage_loss += time_spent_on_move
                elif result == -1 and board.turn == chess.BLACK:
                    players[p2.name].time_usage_win += time_spent_on_move
                elif result == -1:
                    players[p1.name].time_usage_loss += time_spent_on_move
                
                player_clocks[board.turn] = node_clock_s
            
            # Step 6 - opening book checkout
            if n_move <= 30:
                entries = list(book.find_all(board))
                if move in [entry.move for entry in entries]:
                    players[mp.name].no_book_moves += 1
            
            # Step 7 - engine analysis for ACL and move classification
            move_classification = "good"
            try:
                current_eval = node.eval()

                if current_eval is not None:
                    current_eval = current_eval.relative.score(mate_score=MATE_SCORE)
                    board.push(move)
                else:
                    # If we don't have eval in PGN notation, we need to run engine to obtain one
                    board.push(move)

                    if engine_filepath is None:
                        current_eval = last_eval
                    else:
                        analysis_after = engine.analyse(board, chess.engine.Limit(depth=engine_max_depth), info=chess.engine.INFO_SCORE)
                        current_eval = analysis_after['score'].pov(board.turn).score(mate_score=MATE_SCORE)
                
                cp_loss = min(MAX_CP, max(0, current_eval + last_eval))      # current_eval - (-last_eval)
                norm_diff = max(0, logistic(current_eval) - logistic(-last_eval))

                # Classify the move based on CPL and probability change
                if norm_diff > 0.45 and cp_loss > 100:
                    move_classification = "blunder"
                elif norm_diff > 0.3 or cp_loss > 400:
                    move_classification = "mistake"
                elif norm_diff > 0.2 or cp_loss > 200:
                    move_classification = "innacuracy"

                # Now, update the game quality fields for player on move
                players[mp.name].cp_loss += cp_loss
                if move_classification == "blunder":
                    players[mp.name].no_blunders += 1
                    players[mp.name].time_usage_blunder += time_spent_on_move
                elif move_classification == "mistake":
                    players[mp.name].no_mistakes += 1
                    players[mp.name].time_usage_innacuracy_mistake += time_spent_on_move
                elif move_classification == "innacuracy":
                    players[mp.name].no_innacuracies += 1
                    players[mp.name].time_usage_innacuracy_mistake += time_spent_on_move
                else:
                    players[mp.name].time_usage_good_move += time_spent_on_move
                
                # Update dynamic eval variable
                last_eval = current_eval

            except (chess.engine.EngineError, chess.engine.EngineTerminatedError, AttributeError) as e:
                print(f"Engine analysis error in game: {e}")
                # Ensure board is advanced if error occurs mid-analysis
                if board.peek() != move: # If move wasn't pushed due to error path
                    board.push(move)
            except Exception as e: # Catch any other analysis error
                print(f"Unexpected error during engine analysis: {e}")
                if board.peek() != move:
                    board.push(move)
            
            # NOTE: After above section, it is guaranteed that board is "after" last move

            # Step 8 - calculate remaining properties which require board to be in "after" state
            # - Some properties like material imbalance apply to both players
            material_imbalance = abs(get_material_value(board, chess.WHITE) - get_material_value(board, chess.BLACK))
            players[p1.name].material_imbalance += material_imbalance
            players[p2.name].material_imbalance += material_imbalance

        # After processing all the moves, determine the game result
        # - NOTE: there are no games ended up by time forfeit in the dataset
        if not board.is_checkmate() and not board.is_stalemate():
            players[p1.name].no_nonterminal_results += 1
            players[p2.name].no_nonterminal_results += 1
        
        if (id + 1) % logging_frequency == 0:
            print(f"[ Processed {id + 1} games... ]")

    if engine:
        engine.quit()

    if book:
        book.close()

    # Select only players with >= gpp games
    return {name: data for name, data in players.items() if data.no_games >= gpp}


# Creates a final DataFrame objects with everything ready for further statistical analysis
def create_dataframe(data: Dict[str, PlayerData]) -> pd.DataFrame:
    rows = []

    for player_name, p in data.items():
        ng = p.no_games
        nw = p.no_wins
        nl = p.no_loss
        nm = p.no_moves
        ni = p.no_innacuracies
        nmst = p.no_mistakes
        nb = p.no_blunders

        def avg_time(total_sec, count, alt_total, alt_count):
            if count > 0:
                return min(1, total_sec / (600 * count))
            elif alt_count > 0:
                return min(1, alt_total / (600 * alt_count))
            else:
                return 0.0

        avg_t_win  = avg_time(p.time_usage_win,
                              nw, p.time_usage_loss, nl)
        avg_t_loss = avg_time(p.time_usage_loss,
                              nl, p.time_usage_win, nw)

        den_good = nm - ni - nmst - nb
        den_inm  = ni + nmst

        row = {
            'name': player_name,
            'elo': p.elo,
            'games': ng,
            'avg_moves':          nm / ng if ng>0 else 0,
            'frac_nonterm':       p.no_nonterminal_results / ng if ng>0 else 0,
            'avg_cp_loss':        p.cp_loss / nm if nm>0 else 0,
            'avg_inacc':          ni / ng if ng>0 else 0,
            'avg_mist':           nmst / ng if ng>0 else 0,
            'avg_blund':          nb / ng if ng>0 else 0,
            'frac_time_win':       avg_t_win,
            'frac_time_loss':      avg_t_loss,
            'avg_time_good':      p.time_usage_good_move / den_good if den_good  >0 else 0,
            'avg_time_inaccm':    p.time_usage_innacuracy_mistake / den_inm if den_inm >0 else 0,
            'avg_time_blund':     p.time_usage_blunder / nb if nb>0 else 0,
            'avg_mat_imb_per_mv': p.material_imbalance / nm if nm>0 else 0,
            'avg_book_moves':     p.no_book_moves / ng if ng>0 else 0,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    cols = [
        'name', 'elo', 'games', 'avg_moves', 'frac_nonterm', 'avg_cp_loss',
        'avg_inacc', 'avg_mist', 'avg_blund',
        'frac_time_win', 'frac_time_loss',
        'avg_time_good', 'avg_time_inaccm', 'avg_time_blund',
        'avg_mat_imb_per_mv', 'avg_book_moves'
    ]

    return df[cols]