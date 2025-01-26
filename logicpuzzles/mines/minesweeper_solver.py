from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV
from ..utils.smt_utils import SMTConstraintProblem
from ..board import Board, Face
from .minesweeper import MineBoard
import typing as tp

class MinesweeperSolver(SMTConstraintProblem, Board):
    class SolverCell(Face):
        def __init__(self, r: int, c: int, solver: 'MinesweeperSolver', is_solved: bool = False, adjacent_mines: int = -1):
            super().__init__(r, c)
            self.is_solved = is_solved
            self.mine_var = solver.new_var(f"mine_{r}_{c}")  # BitVector for mine/no-mine
            self.adjacent_mines = adjacent_mines

        def __str__(self):
            if not self.is_solved:
                return " "
            return str(self.adjacent_mines)

    face_t = SolverCell
    vertex_t = MineBoard.vertex_t
    edge_t = MineBoard.edge_t

    def create_face(self, r: int, c: int) -> SolverCell:
        # Get information from the game board
        cell = self.game_board.solution.f[(r, c)]
        is_solved = (r, c) in self.game_board.revealed
        adjacent_mines = cell.adjacent_mines if is_solved else -1
        return self.face_t(r, c, self, is_solved, adjacent_mines)

    def __init__(self, game: 'Minesweeper', verbose=False):
        self.game_board = game
        # Calculate required bits to store sum of all cells
        max_sum = game.width * game.height
        required_bits = max_sum.bit_length()  # Number of bits needed to represent max_sum
        SMTConstraintProblem.__init__(self, default_bvlen=required_bits, verbose=verbose)
        Board.__init__(self, game.height, game.width)

    def constraint_minesweeper(self):
        # TODO: Add constraints
        pass

    def constraint_revealed_numbers(self):
        """Each revealed number must have exactly N adjacent mines"""
        for (r, c), cell in self.f.items():
            if cell.is_solved and cell.adjacent_mines >= 0:
                # Get all 8 adjacent cells using Board API
                adjacent_cells = [adj.mine_var 
                                for adj in self.face_to_faces((r, c), include_diagonals=True)]
                # Sum must equal the revealed number
                self.add_constraint(self.gen_total(adjacent_cells) == cell.adjacent_mines)

    def constraint_total_mines(self):
        """Total number of mines must equal the specified count"""
        all_cells = [cell.mine_var for cell in self.f.values()]
        self.add_constraint(self.gen_total(all_cells) == self.game_board.mines)

    def constraint_revealed_safe(self):
        """Revealed cells cannot be mines"""
        for (r, c), cell in self.f.items():
            if cell.is_solved:
                self.add_constraint(cell.mine_var == 0)

    def solve(self) -> tp.Iterator[MineBoard]:
        self.constraint_minesweeper()
        for model in super().solve():
            # TODO: Convert model to solution board
            pass 

    def __str__(self) -> str:
        """Pretty print the solver state using Board's pretty() method"""
        header = "Minesweeper Solver State:\n" + "-" * 30 + "\n"
        return header + self.pretty(h_len=4, v_len=2)  # Use smaller cell size for terminal display 

    def find_determinable_cells(self) -> tp.Iterator[tuple[tuple[int, int], bool]]:
        """Find all cells whose values can be determined from current constraints.
        Yields (row, col), is_mine for each determinable cell."""
        
        # First add all the basic game constraints
        self.constraint_revealed_numbers()
        self.constraint_total_mines()
        self.constraint_revealed_safe()
        
        # Find unsolved cells that have at least one solved neighbor
        for (r, c), cell in self.f.items():
            if not cell.is_solved:
                # Check if this cell has any solved neighbors
                has_solved_neighbor = any(adj.is_solved and adj.adjacent_mines >= 0 
                                       for adj in self.face_to_faces((r, c), include_diagonals=True))
                if has_solved_neighbor:
                    # Try assuming it's a mine
                    with self.solve_context():
                        self.add_constraint(cell.mine_var == 1)
                        mine_possible = self.is_sat()
                    
                    # Try assuming it's safe
                    with self.solve_context():
                        self.add_constraint(cell.mine_var == 0)
                        safe_possible = self.is_sat()
                    
                    # If only one possibility is satisfiable, we found a determinable cell
                    if mine_possible and not safe_possible:
                        yield (r, c), True
                    elif safe_possible and not mine_possible:
                        yield (r, c), False 