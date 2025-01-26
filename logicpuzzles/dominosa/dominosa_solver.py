from hwtypes import smt_utils as fc
from ..utils.smt_utils import SMTConstraintProblem
from ..board import Board, Face, Edge, EDir
from .dominosa import DominosaBoard
import itertools as it

class DominosaSolver(SMTConstraintProblem, Board):
    class DominosaFace(Face):
        def __init__(self, r: int, c: int, val: int):
            super().__init__(r, c)
            self.val = val

        def __str__(self):
            return str(self.val)

    face_t = DominosaFace

    def create_face(self, r: int, c: int) -> DominosaFace:
        return self.face_t(r, c, self.input_board.f[(r,c)].val)

    class DominosaEdge(Edge):
        def __init__(self, dir: EDir, r: int, c: int, solver: 'DominosaSolver'):
            super().__init__(dir, r, c)
            self.var = solver.new_var(f"edge_{dir.name}_{r}_{c}", 0, True)

    edge_t = DominosaEdge

    def create_edge(self, dir: EDir, r: int, c: int) -> DominosaEdge:
        return self.edge_t(dir, r, c, self)

    def __init__(self, board: DominosaBoard, **kwargs):
        if not isinstance(board, DominosaBoard):
            raise TypeError("board must be an instance of DominosaBoard")
        
        self.input_board = board
        SMTConstraintProblem.__init__(self, **kwargs)
        Board.__init__(self, board.nR, board.nC)  # This already creates all faces

    def constraint_edge(self):
        """No dominoes can be placed on boundary edges"""
        for edge in self.iter_boundary_edges():
            self.add_constraint(~edge.var)

    def constraint_one_domino(self):
        """Each square must be covered by exactly one domino"""
        for fidx in self.f:
            # Use face_to_edges() to get all edges around this face
            edges = [edge.var for edge in self.face_to_edges(fidx)]
            # Exactly one edge must be True
            self.add_constraint(self.gen_total(edges) == 1)

    def constraint_num(self):
        """Each domino must connect matching numbers according to the rules"""
        # Track all domino placements to ensure no duplicates
        vals = []
        
        # For each edge, check the numbers it would connect
        for (dir, r, c), edge in self.e.items():
            # Use edge_to_faces() to get the faces this edge connects
            faces = list(self.edge_to_faces((dir, r, c)))
            if len(faces) == 2:  # Skip boundary edges
                v1 = faces[0].val
                v2 = faces[1].val
                vals.append((edge.var, sorted([v1, v2])))

        # No two dominoes can have the same values
        for (d1, vs1), (d2, vs2) in it.combinations(vals, 2):
            if vs1 == vs2:
                self.add_constraint(~(d1 & d2))

    def solve(self, N: int):
        self.constraint_edge()
        self.constraint_one_domino()
        self.constraint_num()
        
        for model in super().solve(N):
            sol = []
            for (dir, r, c), edge in self.e.items():
                if model[edge.var.value]:
                    # Convert to original format where 0=vertical, 1=horizontal
                    dir_val = 1 if dir == EDir.h else 0
                    sol.append((r,c,dir_val))
            yield sol 