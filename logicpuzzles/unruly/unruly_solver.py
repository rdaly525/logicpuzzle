from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV
import itertools as it
import typing as tp
from ..utils.smt_utils import SMTConstraintProblem
from ..board import Board, Face
from .unruly import UnrulyBoard

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
        for faces in self.iter_consecutive_faces(3, 'both'):
            total = self.gen_total([face.var for face in faces])
            self.add_constraint(total != 0)  # Not all zeros
            self.add_constraint(total != 3)  # Not all ones

    def constraint_equal_counts(self):
        # Equal number of black and white in each row and column
        # Check rows
        for faces in self.iter_consecutive_faces(self.nR, 'row'):
            row_sum = self.gen_total([face.var for face in faces])
            self.add_constraint(row_sum == self.nR // 2)

        # Check columns
        for faces in self.iter_consecutive_faces(self.nC, 'col'):
            col_sum = self.gen_total([face.var for face in faces])
            self.add_constraint(col_sum == self.nC // 2)

    def constraint_unruly(self):
        self.constraint_initial_board()
        self.constraint_no_consecutive() 
        self.constraint_equal_counts()
        self.constraint_binary()

    def solve(self) -> tp.Iterator[UnrulyBoard]:
        self.constraint_unruly()
        for model in super().solve():
            solution = {idx: model[face.var.value] for idx, face in self.f.items()}
            faces = [[solution[(r, c)] for c in range(self.nC)] for r in range(self.nR)]
            yield UnrulyBoard(self.nR, faces)