import copy
import numpy as np

BLACK_NUM = 1
WHITE_NUM = 2


def _point_north(p):
    return (p[0], p[1] - 1) if p[1] - 1 >= 0 else None


def _point_east(p, board_width):
    return (p[0] + 1, p[1]) if p[0] + 1 < board_width else None


def _point_south(p, board_height):
    return (p[0], p[1] + 1) if p[1] + 1 < board_height else None


def _point_west(p):
    return (p[0] - 1, p[1]) if p[0] - 1 >= 0 else None


def _get_orthos(p, board_width, board_height):
    orthos = [
        _point_north(p),
        _point_east(p, board_width),
        _point_south(p, board_height),
        _point_west(p),
    ]
    return [ortho for ortho in orthos if ortho is not None]


_ONE_HOT_TRUE = 1
_ONE_HOT_FALSE = 0


class WeiqiBoard:
    def __init__(self, width, height, n_players):
        self._WIDTH = width
        self._HEIGHT = height
        self._N_PLAYERS = n_players
        self._ALLOW_SELF_CAPTURE = False

        self._board = np.array(
            [
                [[_ONE_HOT_FALSE for _ in range(height)] for _ in range(width)]
                for _ in range(n_players)
            ],
            dtype=np.byte,
        )
        self._prev_boards = {}
        self._n_stones = [0 for _ in range(n_players)]
        self._n_captured_stones = [0 for _ in range(n_players)]

    def get_width(self):
        return self._WIDTH

    def get_height(self):
        return self._HEIGHT

    def get_player_num(self, p):
        for player_num in range(self._N_PLAYERS):
            if self._board[player_num][p[0]][p[1]] == _ONE_HOT_TRUE:
                return player_num + 1
        return 0

    # this recursive method will select all the points that are orthogonal
    # to the given point <p>, so long as an orthogonal point
    # matches the original stone color of <p>. these points are appended
    # to the given <group_list>.
    def _select_orthoganally(self, p, index, group_list):
        if self._board[index][p[0]][p[1]] == _ONE_HOT_TRUE and p not in group_list:
            group_list.append(p)
            orthos = _get_orthos(p, self._WIDTH, self._HEIGHT)
            for o in orthos:
                self._select_orthoganally(o, index, group_list)

    # returns a list of the empty points
    # which surround the given <GROUP_LIST> of stones.
    def _find_liberties(self, GROUP_LIST):
        liberties = []
        for p in GROUP_LIST:
            orthos = _get_orthos(p, self._WIDTH, self._HEIGHT)
            for o in orthos:
                if (
                    all(
                        [
                            self._board[i][o[0]][o[1]] == _ONE_HOT_FALSE
                            for i in range(self._N_PLAYERS)
                        ]
                    )
                    and o not in liberties
                ):
                    liberties.append(o)
        return liberties

    # returns True if the move was legal, and returns a list of captured points.
    def _set_stone(self, p, player_num, is_legality_probe=False):
        player_index = player_num - 1
        if any(
            [
                self._board[index][p[0]][p[1]] == _ONE_HOT_TRUE
                for index in range(self._N_PLAYERS)
            ]
        ):
            print("illegal: stone already exists there")
            return False, []

        backup_board = copy.deepcopy(self._board)
        backup_n_stones = copy.deepcopy(self._n_stones)
        backup_n_captured_stones = copy.deepcopy(self._n_captured_stones)

        cleared_points = []

        self._board[player_index][p[0]][p[1]] = _ONE_HOT_TRUE
        self._n_stones[player_index] += 1

        # checks for opposing captures.
        orthos = _get_orthos(p, self._WIDTH, self._HEIGHT)
        n_opposing_captured = 0
        for o in orthos:
            opposing_index = None
            for i in range(self._N_PLAYERS):
                if i == player_index:
                    continue
                if self._board[i][o[0]][o[1]] == _ONE_HOT_TRUE:
                    opposing_index = i
                    break

            if opposing_index is not None:
                opposing_group = []
                self._select_orthoganally(o, opposing_index, opposing_group)
                if (
                    len(opposing_group) > 0
                    and len(self._find_liberties(opposing_group)) == 0
                ):
                    # an opposing group has been captured by the play at <p>.
                    n_opposing_captured += len(opposing_group)
                    self._n_captured_stones[opposing_index] += len(opposing_group)
                    self._n_stones[opposing_index] -= len(opposing_group)
                    cleared_points.extend(opposing_group)
                    for captured in opposing_group:
                        x, y = captured
                        self._board[opposing_index][x][y] = _ONE_HOT_FALSE
                opposing_index = None

        # checks for self-capture.
        own_group = []
        self._select_orthoganally(p, player_index, own_group)
        n_own_liberties = len(self._find_liberties(own_group))

        # checks for repetitions from Ko.
        if n_opposing_captured == 1 and len(own_group) == 1:
            hash_num = hash(tuple(self._n_stones))
            if self._prev_boards.get(hash_num) is not None and any(
                np.array_equal(self._board, prev_board)
                for prev_board in self._prev_boards[hash_num]
            ):
                # taking Ko is a repetition, so everything reverts.
                self._board = copy.deepcopy(backup_board)
                self._n_stones = copy.deepcopy(backup_n_stones)
                self._n_captured_stones = copy.deepcopy(backup_n_captured_stones)
                return False, []

        if n_opposing_captured == 0 and n_own_liberties == 0:
            if self._ALLOW_SELF_CAPTURE and len(own_group) > 1:
                # a friendly group has captured itself with the play at <p>.
                # playing an immediately isolated and captured stone stays illegal.
                self._n_captured_stones[player_index] += len(own_group)
                self._n_stones[player_index] -= len(own_group)
                cleared_points.extend(own_group)
                for captured in own_group:
                    x, y = captured
                    self._board[player_index][x][y] = _ONE_HOT_FALSE
                return True, cleared_points

            else:
                # the stone creates a self-capture, so everything reverts.
                self._board = copy.deepcopy(backup_board)
                self._n_stones = copy.deepcopy(backup_n_stones)
                self._n_captured_stones = copy.deepcopy(backup_n_captured_stones)
                return False, []

        if not is_legality_probe:
            if (
                n_opposing_captured == 1
                and len(own_group) == 1
                and n_own_liberties == 1
            ):
                # adds board record.
                if not self._prev_boards.get(hash_num):
                    self._prev_boards[hash_num] = []
                self._prev_boards[hash_num].append(backup_board)
        else:
            # reverts now that legality is determined to be True.
            self._board = copy.deepcopy(backup_board)
            self._n_stones = copy.deepcopy(backup_n_stones)
            self._n_captured_stones = copy.deepcopy(backup_n_captured_stones)

        return True, cleared_points

    def move_is_legal(self, p, player_num):
        legal, _ = self._set_stone(p, player_to_move, is_legality_probe=True)
        return legal

    def add_initial_stone(self, p, player_num):
        index = player_num - 1
        self._board[index][p[0]][p[1]] = _ONE_HOT_TRUE

    def add_empty_space(self, p):
        for i in range(self._N_PLAYERS):
            self._board[i][p[0]][p[1]] = _ONE_HOT_FALSE

    # returns True if the move was legal, and returns a list of captured points.
    def make_move(self, p, player_num):
        legal, cleared_points = self._set_stone(p, player_num)
        return legal, cleared_points

    def to_str(self):
        result = ""
        CHARS = "◯⬤"
        for y in range(self._HEIGHT):
            for x in range(self._WIDTH):
                occupying_index = None
                for i in range(self._N_PLAYERS):
                    if self._board[i][x][y] == _ONE_HOT_TRUE:
                        occupying_index = i
                        break
                if occupying_index is None:
                    result += ". "
                else:
                    result += CHARS[occupying_index] + " "
            result += "\n"

        return result
