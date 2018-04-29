#!/home/keunwoo/Documents/Projects/chess-engine/venv/bin/python

import attr
import chess
import math
import time
import torch
from torch.autograd import Variable
import random
import os
import sys
root_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(root_path)
from yureka import chess_dataset    # noqa: E402
from yureka.board_data import get_board_data, get_reward    # noqa: E402
from yureka import models    # noqa: E402
from yureka.chess_engine import (    # noqa: E402
    print_flush,
    ChessEngine,
    UCIEngine,
)
from yureka.move_translator import (    # noqa: E402
    TOTAL_MOVES,
    translate_to_engine_move,
    get_engine_move_index,
)


RANDOM_POLICY = 'random'
DEFAULT_VALUE = 'Value.v0'
DEFAULT_VALUE_FILE = os.path.join(
    root_path,
    'saved_models',
    'Value',
    'Value_2018-01-31_14:20:50_4.model',
)
ZERO_VALUE = 'zero'
DEFAULT_POLICY = 'Policy.v0'
DEFAULT_POLICY_FILE = os.path.join(
    root_path,
    'saved_models',
    'SL_endgame',
    'Policy_2018-01-27_07:09:34_14.model',
)
DEFAULT_CONFIDENCE = 5


@attr.s
class Node():
    children = attr.ib(default=attr.Factory(dict))
    parent = attr.ib(default=None)
    prior = attr.ib(default=0)
    value = attr.ib(default=0)
    visit = attr.ib(default=0)
    board = attr.ib(default=chess.Board())

    def q(self):
        if self.visit == 0:
            return math.inf
        return self.value / self.visit

    def ucb(self, confidence, visit_sum):
        # alpha go version
        ucb = self.q()
        ucb += confidence * self.prior * math.sqrt(visit_sum)
        ucb /= (1 + self.visit)
        return ucb

    def add_child(self, move, **kwargs):
        b = chess.Board(fen=self.board.fen())
        b.push(move)
        self.children[move] = Node(
            parent=self,
            board=b,
            **kwargs
        )


@attr.s
class MCTSError(Exception):
    node = attr.ib()
    message = attr.ib()


@attr.s
class MCTS():
    root = attr.ib()
    value = attr.ib()
    policy = attr.ib()
    confidence = attr.ib(default=DEFAULT_CONFIDENCE)

    def select(self):
        node = self.root
        while node.children:
            child_nodes = node.children.values()
            visit_sum = sum([n.visit for n in child_nodes])
            node = max(
                child_nodes,
                key=lambda n: n.ucb(self.confidence, visit_sum)
            )
        return node

    def expand(self, node):
        if node.children:
            raise MCTSError(node, 'Cannot expand a non-leaf node')
        if node.board.legal_moves:
            priors = self.policy.get_probs(node.board).squeeze()
            for move in node.board.legal_moves:
                engine_move = translate_to_engine_move(move, node.board.turn)
                index = get_engine_move_index(engine_move)
                prior = priors.data[index]
                node.add_child(move, prior=prior)
            return random.choice(list(node.children.values()))
        else:
            # terminal state, just return itself
            return node

    def simulate(self, node):
        if node.children:
            raise MCTSError(node, 'cannot simulate from a non-leaf')
        board = chess.Board(fen=node.board.fen())
        if board.is_game_over(claim_draw=True):
            return get_reward(board.result(claim_draw=True), board.turn)
        return self.value.get_value(board)

    def backup(self, node, value):
        walker = node
        while walker:
            walker.visit += 1
            walker.value += value
            walker = walker.parent

    def search(self, duration):
        search_time = continue_search(duration)
        count = 0
        for t in search_time:
            if not t:
                print_flush(f'info string search iterations: {count}')
                break
            leaf = self.select()
            leaf = self.expand(leaf)
            value = self.simulate(leaf)
            self.backup(leaf, value)
            count += 1

    def get_move(self):
        # pick the move with the max visit from the root
        if not self.root.children:
            raise MCTSError(self.root, 'You should search before get_move')
        return max(
            self.root.children,
            key=lambda m: self.root.children[m].visit
        )

    def advance_root(self, move):
        child = self.root.children.get(move)
        if child:
            self.root = child
        else:
            self.root.add_child(move)
            self.root = self.root.children[move]
        self.root.parent = None


TC_WTIME = 'wtime'
TC_BTIME = 'btime'
TC_WINC = 'winc'
TC_BINC = 'binc'
TC_MOVESTOGO = 'movestogo'
TC_MOVETIME = 'movetime'
TC_KEYS = [
    TC_WTIME,
    TC_BTIME,
    TC_WINC,
    TC_BINC,
    TC_MOVESTOGO,
    TC_MOVETIME,
]


@attr.s
class TimeManager():
    total_time = attr.ib(default=None)
    total_moves = attr.ib(default=None)

    def handle_movetime(self, data):
        return data[TC_MOVETIME]

    def handle_fischer(self, color, data):
        if color == chess.WHITE:
            time = data[TC_WTIME]
            otime = data[TC_BTIME]
            inc = data[TC_WINC]
        else:
            time = data[TC_BTIME]
            otime = data[TC_WTIME]
            inc = data[TC_BINC]

        ratio = max(otime/time, 1.0)
        # assume we have 16 moves to go
        moves = 16 * min(2.0, ratio)
        return time / moves + 3 / 4 * inc

    def handle_classic(self, color, data):
        if self.total_time is None and self.total_moves is None:
            # first time getting time control information
            # assume this is the start
            self.total_moves = data.get(TC_MOVESTOGO)
            if color == chess.WHITE:
                self.total_time = data[TC_WTIME]
            else:
                self.total_time = data[TC_BTIME]
        if color == chess.WHITE:
            time = data[TC_WTIME]
        else:
            time = data[TC_BTIME]
        moves = data.get(TC_MOVESTOGO, 20)
        tc = time / moves
        if self.total_moves:
            tc_cf = time + self.total_time
            tc_cf /= moves + self.total_moves
        else:
            tc_cf = math.inf
        return min(tc, tc_cf)

    def handle(self, color, args):
        data = parse_time_control(args)
        return self.calculate_duration(color, data)

    def calculate_duration(self, color, data):
        if TC_MOVETIME in data:
            duration = self.handle_movetime(data)
        elif TC_WINC in data and TC_BINC in data:
            duration = self.handle_fischer(color, data)
        else:
            duration = self.handle_classic(color, data)
        return duration / 1000


def continue_search(duration):
    # search for {duration} seconds
    remaining = duration
    while remaining >= 0:
        start = time.time()
        yield True
        end = time.time()
        remaining -= end - start
    yield False


def parse_time_control(args):
    data = {}
    args = args.split()
    for i in range(len(args)):
        token = args[i]
        if token in TC_KEYS:
            data[token] = float(args[i+1])
    return data


class ZeroValue():
    def get_value(self, board):
        return 0


class RandomPolicy():
    def get_move(self, board, sample=True):
        return random.choice(list(board.legal_moves))

    def get_probs(self, board):
        moves = list(board.legal_moves)
        prob = 1/len(moves)
        probs = Variable(torch.zeros(1, TOTAL_MOVES))
        indexes = []
        for move in moves:
            engine_move = translate_to_engine_move(move, board.turn)
            index = get_engine_move_index(engine_move)
            indexes.append(index)
        probs.index_fill_(1, Variable(torch.LongTensor(indexes)), prob)
        return probs


@attr.s
class ValueNetwork():
    value = attr.ib()
    cuda = attr.ib(default=True)
    cuda_device = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.value.eval()
        self.cuda = self.cuda and torch.cuda.is_available()
        if self.cuda:
            self.value.cuda(self.cuda_device)

    def get_value(self, board):
        board_data = get_board_data(board)
        tensor = chess_dataset.get_tensor_from_row(board_data)
        tensor = tensor.unsqueeze(0)
        value = self.value(Variable(tensor.cuda(), volatile=True))
        return value.squeeze().data[0]


@attr.s
class UCIMCTSEngine(UCIEngine):
    value_name = attr.ib(default=DEFAULT_VALUE)
    value_file = attr.ib(default=DEFAULT_VALUE_FILE)
    policy_name = attr.ib(default=DEFAULT_POLICY)
    policy_file = attr.ib(default=DEFAULT_POLICY_FILE)
    confidence = attr.ib(default=DEFAULT_CONFIDENCE)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.options = {
            'Value Name': {
                'type': 'string',
                'default': DEFAULT_VALUE,
                'attr_name': 'value_name',
                'py_type': str,
                'model': True,
            },
            'Value File': {
                'type': 'string',
                'default': DEFAULT_VALUE_FILE,
                'attr_name': 'value_file',
                'py_type': str,
                'model': True,
            },
            'Policy Name': {
                'type': 'string',
                'default': DEFAULT_POLICY,
                'attr_name': 'policy_name',
                'py_type': str,
                'model': True,
            },
            'Policy File': {
                'type': 'string',
                'default': DEFAULT_POLICY_FILE,
                'attr_name': 'policy_file',
                'py_type': str,
                'model': True,
            },
            'Confidence': {
                'type': 'string',
                'default': DEFAULT_CONFIDENCE,
                'attr_name': 'confidence',
                'py_type': float,
                'model': False,
            },
        }

    def init_model(self, name, path):
        model = models.create(name)
        model.load_state_dict(torch.load(os.path.expanduser(path)))
        return model

    def init_models(self):
        if self.value_name == ZERO_VALUE:
            self.value = ZeroValue()
        else:
            self.value = self.init_model(self.value_name, self.value_file)
            self.value = ValueNetwork(self.value)
        if self.policy_name == RANDOM_POLICY:
            self.policy = RandomPolicy()
        else:
            self.policy = self.init_model(self.policy_name, self.policy_file)
            self.policy = ChessEngine(self.policy, train=False)

    def init_engine(self, board=None):
        if board:
            root = Node(board=board)
        else:
            root = Node()
        self.engine = MCTS(
            root,
            self.value,
            self.policy,
            self.confidence,
        )
        self.time_manager = TimeManager()

    def new_position(self, fen, moves):
        board = chess.Board(fen=fen)
        for uci in moves:
            if board == self.engine.root.board:
                self.engine.advance_root(chess.Move.from_uci(uci))
            board.push_uci(uci)
        if board != self.engine.root.board:
            self.init_engine(board=board)

    def go(self, args):
        duration = self.time_manager.handle(self.engine.root.board.turn, args)
        if not duration:
            self.unknown_handler(args)
            return
        print_flush(f'info string search for {duration} seconds')
        self.engine.search(duration)
        move = self.engine.get_move()
        print_flush(f'bestmove {move.uci()}')


if __name__ == '__main__':
    print_flush('Yureka!')
    UCIMCTSEngine().listen()
