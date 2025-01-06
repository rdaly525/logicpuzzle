"""
Towers Puzzle

A logic puzzle where you must place towers of different heights (1 to N) in a NxN grid.
Each number on the outside of the grid indicates how many towers can be seen from that direction.
Taller towers block the view of shorter towers behind them.

The numbers around the grid are:
- Top (T): Number of towers visible looking down each column
- Bottom (B): Number of towers visible looking up each column  
- Left (L): Number of towers visible looking right across each row
- Right (R): Number of towers visible looking left across each row

Rules:
1. Each row and column must contain exactly one tower of each height (1 to N)
2. The number of visible towers from each direction must match the given clues
"""

import random
import typing as tp
from ..utils.smt_utils import SMTConstraintProblem
import math
import itertools
# Holds the clues. the board is the solution
class Towers:
    def __init__(self, N: int, clues: tp.Optional[tp.Dict[str, int]] = None):
        self.N = N
        if clues is None:
            self._randomize()
        else:
            self.clues = clues
        # verify clues are in the right format
        for kind in ("T", "B", "L", "R"):
            assert len(self.clues[kind]) == self.N and all(isinstance(c, int) for c in self.clues[kind])

    # create a random valid puzzle. Technique for N=3"
    # start with a default board:
    # 1 2 3
    # 2 3 1
    # 3 1 2
    # then shuffle the rows and columns for the random valid board
    # then compute the clues
    def _randomize(self):
        # Create default board
        board = [[0] * self.N for _ in range(self.N)]
        for i in range(self.N):
            for j in range(self.N):
                board[i][j] = ((i + j) % self.N) + 1

        # Shuffle rows
        random.shuffle(board)

        # Shuffle columns by transposing, shuffling rows, then transposing back
        board = list(map(list, zip(*board)))  # transpose
        random.shuffle(board)
        board = list(map(list, zip(*board)))  # transpose back
        print(board)
        # Compute clues by counting visible towers from each direction
        clues = {'T': [], 'B': [], 'L': [], 'R': []}

        # Top clues
        for col in range(self.N):
            visible = 1
            max_height = board[0][col]
            for row in range(1, self.N):
                if board[row][col] > max_height:
                    visible += 1
                    max_height = board[row][col]
            clues['T'].append(visible)

        # Bottom clues
        for col in range(self.N):
            visible = 1
            max_height = board[self.N-1][col]
            for row in range(self.N-2, -1, -1):
                if board[row][col] > max_height:
                    visible += 1
                    max_height = board[row][col]
            clues['B'].append(visible)

        # Left clues
        for row in range(self.N):
            visible = 1
            max_height = board[row][0]
            for col in range(1, self.N):
                if board[row][col] > max_height:
                    visible += 1
                    max_height = board[row][col]
            clues['L'].append(visible)

        # Right clues
        for row in range(self.N):
            visible = 1
            max_height = board[row][self.N-1]
            for col in range(self.N-2, -1, -1):
                if board[row][col] > max_height:
                    visible += 1
                    max_height = board[row][col]
            clues['R'].append(visible)

        self.clues = clues

    def pretty_print(self, board=None):
        if board is None:
            board = [['XX' for _ in range(self.N)] for _ in range(self.N)]
        else:
            board = [[str(board[i][j]).rjust(2) for j in range(self.N)] for i in range(self.N)]

        # Print top clues without borders
        print("   ", end="")
        for i in range(self.N):
            print("    " + str(self.clues['T'][i]).rjust(2), end="")
        print()

        # Print top border of board  
        print("    +" + "-" * (6*self.N-1) + "+")

        # Print board with left and right clues
        for i in range(self.N):
            print(f"{str(self.clues['L'][i]).rjust(2)}  |  " + "    ".join(board[i]) + f"  |  {str(self.clues['R'][i]).rjust(2)}")
        
        # Print bottom border of board
        print("    +" + "-" * (6*self.N-1) + "+")

        # Print bottom clues without borders
        print("   ", end="")
        for i in range(self.N):
            print("    " + str(self.clues['B'][i]).rjust(2), end="")
        print()
class TowersSolver(SMTConstraintProblem):
    def __init__(self, towers: Towers):
        self.towers = towers
        if self.towers.clues is None:
            raise ValueError("Towers must have clues to be solved")
        bvlen = math.ceil(math.log2(self.towers.N)+2)
        super().__init__(default_bvlen=bvlen, z3_solver=False)
        # create a variable for each cell in the board
        self.board = [[self.new_var(name=f"board_{i}_{j}") for j in range(self.towers.N)] for i in range(self.towers.N)]

    # vars must be in the range 1 to N  
    def constraint_vals(self):
        for i in range(self.towers.N):
            for j in range(self.towers.N):
                self.add_constraint(self.board[i][j] >= 1)
                self.add_constraint(self.board[i][j] <= self.towers.N)

    # each row and each column must contain exactly one tower of each height (1 to N)
    def constraint_rows(self):
        for row in range(self.towers.N):
            for c1, c2 in itertools.combinations(range(self.towers.N), 2):
                self.add_constraint(self.board[row][c1] != self.board[row][c2])

    def constraint_cols(self):
        for col in range(self.towers.N):
            for r1, r2 in itertools.combinations(range(self.towers.N), 2):
                self.add_constraint(self.board[r1][col] != self.board[r2][col])

    def constraint_clues(self):
        # Given a list of heights, symbolically count the number of visible towers
        def count_visible(heights: tp.List):
            visible = self.BV(0)
            max_height = self.BV(0)
            for height in heights:
                cur_visible = (height > max_height).ite(self.BV(1), self.BV(0))
                visible += cur_visible.ite(self.BV(1), self.BV(0))
                max_height = cur_visible.ite(height, max_height)
            return visible

        # There are a total of N*4 clues, N for each direction,
        # For each clue, first create list of ordered hegihts (when looking in that direction)
        # then count the number of visible towers and add the constraint
        for kind in ("T", "B", "L", "R"):
            for i in range(self.towers.N):
                if kind == "T":
                    # Top view - read column i from top to bottom
                    heights = [self.board[j][i] for j in range(self.towers.N)]
                elif kind == "B":
                    # Bottom view - read column i from bottom to top 
                    heights = [self.board[j][i] for j in range(self.towers.N-1, -1, -1)]
                elif kind == "L":
                    # Left view - read row i from left to right
                    heights = [self.board[i][j] for j in range(self.towers.N)]
                else: # kind == "R"
                    # Right view - read row i from right to left
                    heights = [self.board[i][j] for j in range(self.towers.N-1, -1, -1)]
                    
                visible = count_visible(heights)
                self.add_constraint(visible == self.towers.clues[kind][i])

    def solve(self):
        self.constraint_vals()
        self.constraint_rows()
        self.constraint_cols()
        self.constraint_clues()
        for model in super().solve():
            board = [[model[self.board[i][j].value] for j in range(self.towers.N)] for i in range(self.towers.N)]
            yield board