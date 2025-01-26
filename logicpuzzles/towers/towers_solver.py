import math
import itertools as it
import typing as tp
from ..utils.smt_utils import SMTConstraintProblem
from ..board import Board, Face
from .towers import TowersBoard

class TowersSolver(SMTConstraintProblem, Board):
    class TowersFace(Face):
        def __init__(self, r: int, c: int, solver: 'TowersSolver', input_face: tp.Optional[TowersBoard.face_t] = None):
            super().__init__(r, c)
            self.var = solver.new_var(f"face_{r}_{c}")
            # Initialize from input face if provided
            self.is_solved = input_face.is_solved if input_face else False
            self.solved_val = input_face.solved_val if input_face else None

        def __str__(self):
            return "  "

    face_t = TowersFace
    vertex_t = TowersBoard.vertex_t
    edge_t = TowersBoard.edge_t

    def create_face(self, r: int, c: int) -> TowersFace:
        input_face = self.input_board.f[(r, c)]
        return self.face_t(r, c, self, input_face)

    def __init__(self, board: TowersBoard, verbose=False):
        if not isinstance(board, TowersBoard):
            raise TypeError("board must be an instance of TowersBoard")
            
        bvlen = math.ceil(math.log2(board.N)+2)
        self.input_board = board
        SMTConstraintProblem.__init__(self, default_bvlen=bvlen, verbose=verbose)
        Board.__init__(self, board.nR, board.nC)

    def constraint_vals(self):
        # Each cell must be between 1 and N
        for face in self.f.values():
            self.add_constraint(face.var >= 1)
            self.add_constraint(face.var <= self.input_board.N)

    def constraint_rows(self):
        # Each row must have unique values
        for faces in self.iter_consecutive_faces(self.nR, 'row'):
            for f1, f2 in it.combinations(faces, 2):
                self.add_constraint(f1.var != f2.var)

    def constraint_cols(self):
        # Each column must have unique values
        for faces in self.iter_consecutive_faces(self.nC, 'col'):
            for f1, f2 in it.combinations(faces, 2):
                self.add_constraint(f1.var != f2.var)

    def constraint_clues(self):
        # Given a list of faces, symbolically count the number of visible towers
        def count_visible(faces: tp.List['TowersSolver.TowersFace']):
            visible = self.BV(0)
            max_height = self.BV(0)
            for face in faces:
                cur_visible = (face.var > max_height).ite(self.BV(1), self.BV(0))
                visible += cur_visible.ite(self.BV(1), self.BV(0))
                max_height = cur_visible.ite(face.var, max_height)
            return visible

        # For each direction, get faces in order and check visibility matches clue
        for kind in ("T", "B", "L", "R"):
            for i in range(self.nR):
                if kind == "T":
                    # Top view - read column i from top to bottom
                    faces = list(self.iter_consecutive_faces(self.nR, 'col'))[i]
                elif kind == "B":
                    # Bottom view - read column i from bottom to top 
                    faces = list(reversed(list(self.iter_consecutive_faces(self.nR, 'col'))[i]))
                elif kind == "L":
                    # Left view - read row i from left to right
                    faces = list(self.iter_consecutive_faces(self.nR, 'row'))[i]
                else: # kind == "R"
                    # Right view - read row i from right to left
                    faces = list(reversed(list(self.iter_consecutive_faces(self.nR, 'row'))[i]))
                    
                visible = count_visible(faces)
                self.add_constraint(visible == self.input_board.clues[kind][i])

    def solve(self) -> tp.Iterator[TowersBoard]:
        self.constraint_vals()
        self.constraint_rows()
        self.constraint_cols()
        self.constraint_clues()
        for model in super().solve():
            # Create new board with solution values
            board = TowersBoard(self.nR, self.input_board.clues)
            for (r, c), face in self.f.items():
                val = model[face.var.value]
                board.f[(r, c)].val = val
                board.f[(r, c)].is_solved = face.is_solved
                board.f[(r, c)].solved_val = face.solved_val
            yield board 