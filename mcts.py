import attr
import chess
import math
import collections
from board_data import get_board_data
from move_translator import (
    translate_to_engine_move,
    get_engine_move_index,
)


@attr.s
class Node():
    children = attr.ib(default={})
    parent = attr.ib(default=None)
    prior = attr.ib(default=0)
    result = attr.ib(default=0)
    value = attr.ib(default=0)
    visit = attr.ib(default=0)
    board = attr.ib(default=chess.Board())
    transpositions = attr.ib(default=collections.Counter())
    lambda_c = attr.ib(default=0.5)
    confidence = attr.ib(default=1)

    def __attrs_post_init__(self):
        self.board_data = get_board_data(self.board, self.transpositions)

    @property
    def q(self):
        q = (1 - self.lambda_c) * self.value / self.visit
        q += self.lambda_c * self.result / self.visit
        return q

    def ucb(self, visit_sum):
        # alpha go version
        ucb = self.q
        ucb += self.confidence * math.sqrt(visit_sum) / (1 + self.visit)
        return ucb

    def add_child(self, move, **kwargs):
        b = chess.Board(fen=self.board.fen())
        b.push(move)
        self.children[move] = Node(
            parent=self,
            board=b,
            transpositions=self.transpositions,
            **kwargs
        )


@attr.s
class MCTS():
    root = attr.ib()
    rollout = attr.ib()
    value = attr.ib()
    policy = attr.ib()
    terminate_search = attr.ib()

    def expand(self, node):
        if not self.children:
            raise Exception(f'Cannot expand a non-leaf node: {self}')
        priors = self.policy.get_probs(node.board).squeeze()
        for move in node.board.legal_moves:
            engine_move = translate_to_engine_move(move)
            index = get_engine_move_index(engine_move)
            prior = priors.data[index]
            self.add_child(move, prior=prior)

    def search(self):
        while not self.terminate_search():
            leaf = self.select()
            self.expand(leaf)
            terminal = self.simulate(leaf)
            self.backup(terminal)

    def move(self):
        self.search()
        # pick according to the formula
