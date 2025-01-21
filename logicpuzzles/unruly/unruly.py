"""
Unruly is a puzzle game created by Simon Tatham. The goal is to fill a grid with black (1) and white (0) squares 
following these rules:

1. No three consecutive squares in a row or column can be the same color
2. Each row and column must contain an equal number of black and white squares

The puzzle starts with some squares already filled in, and the player must complete the rest of the grid while
following all the rules.
"""

from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV
import itertools as it
import random
from ..utils.smt_utils import SMTConstraintProblem
from ..board import Board, Face, Vertex, Edge
from dataclasses import dataclass
import typing as tp

# An unruly board is a grid of black, white, and empty squares
# black is 0, white is 1, empty is 2
class UnrulyBoard(Board):
    @dataclass
    class face_t(Face):
        val: int = None
        def __str__(self):
            if self.val is None:
                return " "
            return str(self.val)

    vertex_t = Vertex
    edge_t = Edge

    def __init__(self, N, faces=None, percent_filled=0.2):
        super().__init__(N, N)
        self.N = N
        if faces is None:
            faces = self._random_board(percent_filled)
        assert len(faces) == self.nR
        assert all(len(row) == self.nC for row in faces)
         
        for (r, c), face in self.f.items():
            if faces[r][c] != 2:
                face.val = faces[r][c]


    def _random_board(self, percent_filled=0.2):
        # Calculate number of squares to fill
        total_squares = self.nR * self.nC
        num_filled = int(total_squares * percent_filled)
        
        # Create list of all positions
        positions = [(r,c) for r in range(self.nR) for c in range(self.nC)]
        
        # Randomly select positions to fill
        fill_positions = random.sample(positions, num_filled)
        
        # Initialize board and fill selected positions
        faces = [[2 for _ in range(self.nC)] for _ in range(self.nR)]
        for r,c in fill_positions:
            faces[r][c] = random.randint(0,1)
        return faces

class UnrulySolver(SMTConstraintProblem, Board):
    class UnrulyFace(Face):
        def __init__(self, r: int, c: int, solver: 'UnrulySolver', initial_val: int | None):
            super().__init__(r, c)
            self.var = solver.new_var(f"face_{r}_{c}")
            self.initial_val = initial_val

        def __str__(self):
            if self.initial_val is None:
                return " "
            return str(self.initial_val)

    face_t = UnrulyFace
    vertex_t = UnrulyBoard.vertex_t
    edge_t = UnrulyBoard.edge_t

    def create_face(self, r: int, c: int) -> UnrulyFace:
        initial_val = self.input_board.f[(r, c)].val
        return self.face_t(r, c, self, initial_val)

    def __init__(self, board: UnrulyBoard, verbose=False):
        if not isinstance(board, UnrulyBoard):
            raise TypeError("board must be an instance of UnrulyBoard")
            
        bvlen = len(bin(max(board.nR, board.nC)))  # Use max of dimensions for bit vector length
        self.input_board = board  # Store input board for create_face to access
        SMTConstraintProblem.__init__(self, default_bvlen=bvlen, verbose=verbose)
        Board.__init__(self, board.nR, board.nC)

    def constraint_binary(self):
        # Each cell must be either 0 or 1
        for face in self.f.values():
            self.add_constraint((face.var < 2))

    def constraint_initial_board(self):
        # Each cell must match initial board where specified
        for face in self.f.values():
            if face.initial_val is not None:
                self.add_constraint(face.var == face.initial_val)

    def constraint_no_consecutive(self):
        # No three consecutive cells can be same color in rows or columns
        for r in range(self.nR):
            for c in range(self.nC - 2):
                # Check rows
                faces = [self.f[(r, c)], self.f[(r, c+1)], self.f[(r, c+2)]]
                total = self.gen_total([face.var for face in faces])
                self.add_constraint(total != 0)  # Not all zeros
                self.add_constraint(total != 3)  # Not all ones

        for r in range(self.nR - 2):
            for c in range(self.nC):
                # Check columns
                faces = [self.f[(r, c)], self.f[(r+1, c)], self.f[(r+2, c)]]
                total = self.gen_total([face.var for face in faces])
                self.add_constraint(total != 0)  # Not all zeros
                self.add_constraint(total != 3)  # Not all ones

    def constraint_equal_counts(self):
        # Equal number of black and white in each row and column
        # Check rows
        for r in range(self.nR):
            row_vars = [self.f[(r, c)].var for c in range(self.nC)]
            row_sum = self.gen_total(row_vars)
            self.add_constraint(row_sum == self.nR // 2)

        # Check columns
        for c in range(self.nC):
            col_vars = [self.f[(r, c)].var for r in range(self.nR)]
            col_sum = self.gen_total(col_vars)
            self.add_constraint(col_sum == self.nC // 2)

    def constraint_unruly(self):
        self.constraint_initial_board()
        self.constraint_no_consecutive() 
        self.constraint_equal_counts()
        self.constraint_binary()

    def solve(self) -> tp.Iterator[dict[tuple[int, int], int]]:
        self.constraint_unruly()
        for model in super().solve():
            solution = {idx: model[face.var.value] for idx, face in self.f.items()}
            yield solution

    def pretty(self, solution):
        # construct new UnrulyBoard object with the solution, then pretty print it
        faces = [[solution[(r, c)] for c in range(self.nC)] for r in range(self.nR)]
        N = self.nR
        assert N == self.nC
        board = UnrulyBoard(N, faces)
        return board.pretty()