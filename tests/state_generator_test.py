import pandas as pd
import numpy as np
import chess
import chess.pgn
from state_generator import StateGenerator, pieces


def test_generate_correct_num_games():
    state_gen = StateGenerator("tests/test.pgn")
    assert len(list(state_gen.get_game())) == 2


def check_square(df, w_sq, b_sq, symbols_to_check, step):
    for p in pieces:
        expected_val = 0
        symbol = p.symbol()
        squares = w_sq if p.color == chess.WHITE else b_sq
        if symbol in symbols_to_check:
            expected_val = 1

        for sq in squares:
            assert df.loc[step, f'{sq}-{symbol}'] == expected_val


def test_generate_correct_sq_piece_data():
    state_gen = StateGenerator("tests/test.pgn")
    g = next(state_gen.get_game())
    df = pd.DataFrame(state_gen.get_square_piece_data(g))
    assert df.shape == (57, 8*8*(6+6))

    # make sure the initial board position is correct
    # Kings
    check_square(df, ('e1',), ('e8',), ('K', 'k'), 0)

    # Queens
    check_square(df, ('d1',), ('d8',), ('Q', 'q'), 0)

    # Rooks
    check_square(df, ('a1', 'h1'), ('a8', 'h8'), ('R', 'r'), 0)

    # Bishops
    check_square(df, ('a1', 'h1'), ('a8', 'h8'), ('R', 'r'), 0)

    # Knights
    check_square(df, ('b1', 'g1'), ('b8', 'g8'), ('N', 'n'), 0)

    # Pawns
    check_square(
        df,
        ('a2', 'b2', 'c2', 'd2', 'e2', 'f2', 'g2', 'h2'),
        ('a7', 'b7', 'c7', 'd7', 'e7', 'f7', 'g7', 'h7'),
        ('P', 'p'),
        0
    )

    # Board position after one move e2e4 (white pawn to e4)
    # Kings
    check_square(df, ('e1',), ('e8',), ('K', 'k'), 1)

    # Queens
    check_square(df, ('d1',), ('d8',), ('Q', 'q'), 1)

    # Rooks
    check_square(df, ('a1', 'h1'), ('a8', 'h8'), ('R', 'r'), 1)

    # Bishops
    check_square(df, ('a1', 'h1'), ('a8', 'h8'), ('R', 'r'), 1)

    # Knights
    check_square(df, ('b1', 'g1'), ('b8', 'g8'), ('N', 'n'), 1)

    # Pawns
    check_square(
        df,
        ('a2', 'b2', 'c2', 'd2', 'e4', 'f2', 'g2', 'h2'),
        ('a7', 'b7', 'c7', 'd7', 'e7', 'f7', 'g7', 'h7'),
        ('P', 'p'),
        1
    )


def test_repetition_data():
    b = chess.Board(fen='4k3/8/8/8/8/8/8/4K3 w - - 0 1')

    # Create transpositions
    def move(b):
        b.push(chess.Move.from_uci('e1e2'))
        b.push(chess.Move.from_uci('e8e7'))
        b.push(chess.Move.from_uci('e2e1'))
        b.push(chess.Move.from_uci('e7e8'))
    for i in range(3):
        move(b)

    game = chess.pgn.Game.from_board(b)
    state_gen = StateGenerator("tests/test.pgn")  # file not used

    for i, data in enumerate(state_gen.get_repetition_data(game)):
        if i < 4:
            # no transpositions yet
            assert np.array_equal(data, np.full((2, 8, 8), 0))
        elif i < 8:
            # twofold transpositions
            assert np.array_equal(data[0], np.full((8, 8), 1))
            assert np.array_equal(data[1], np.full((8, 8), 0))
        else:
            # threefold transpositions
            assert np.array_equal(data, np.full((2, 8, 8), 1))
