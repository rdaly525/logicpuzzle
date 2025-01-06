"""
Flip is a puzzle game from Simon Tatham's Portable Puzzle Collection.

The game is played on a square grid of black and white cells. The goal is to make all cells white.
When you click on a cell, that cell and all orthogonally adjacent cells (up, down, left, right) 
are flipped to their opposite color (black becomes white and white becomes black).

The challenge is to find the right sequence of moves that will turn all cells white.
Each puzzle has at least one solution.

In this implementation:
- 0 represents a white cell
- 1 represents a black cell
"""


from ..utils.smt_utils import SMTConstraintProblem
import random
import itertools as it
import hwtypes.smt_utils as fc

# A class that holds the problem state
class FlipBoard:
    def __init__(self, N, board=None):
        self.N = N
        if board is None:
            self._random_board()
        else:
            self.board = board
        assert len(self.board) == self.N
        assert all(len(row) == self.N for row in self.board)

    def _random_board(self):
        self.board = [[random.randint(0, 1) for _ in range(self.N)] for _ in range(self.N)]

    def pretty_print(self, sol):
        
        # First print the board
        print("\n".join([" ".join([str(self.board[r][c]) for c in range(self.N)]) for r in range(self.N)]))

        print("\n")
        # Then print the solution
        print("\n".join([" ".join([str(sol[r][c]) for c in range(self.N)]) for r in range(self.N)]))


class FlipSolver(SMTConstraintProblem):
    def __init__(self, board, goal_value=0, verbose=False):
        super().__init__(verbose=verbose)
        self.board = board
        self.goal_value = goal_value

        # Create the problem variables
        self.vars = [[self.new_var(f"x_{r}_{c}", 0) for c in range(self.board.N)] for r in range(self.board.N)]

    def constraint_flip(self):
        board_counts = [[self.Bit(v) for v in row] for row in self.board.board]
        for r, c in it.product(range(self.board.N), range(self.board.N)):
            for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < self.board.N and 0 <= c2 < self.board.N:
                    board_counts[r][c] ^= self.vars[r2][c2]
        self.add_constraint(fc.And([board_counts[r][c] == self.goal_value for r, c in it.product(range(self.board.N), range(self.board.N))]))

    def solve(self):
        self.constraint_flip()
        for model in super().solve():
            yield [[model[self.vars[r][c].value] for c in range(self.board.N)] for r in range(self.board.N)]





#WORKS
#n = 5
#board = [
#    [1, 1, 0, 1, 1],
#    [1, 1, 1, 1, 0],
#    [0, 1, 1, 0, 1],
#    [1, 0, 1, 1, 1],
#    [0, 1, 1, 1, 0],
#]
#
#init = [[SBV[1](v) for v in row] for row in board]
#
#free_vars = [[SBV[1](name=f"{r},{c}") for r in range(n)] for c in range(n)]
#
#for r in range(n):
#    for c in range(n):
#        points = [(r, c)]
#        for offset in (-1, 1):
#            ri = r + offset
#            if 0 <= ri < n:
#                points.append((ri, c))
#            ci = c + offset
#            if 0 <= ci < n:
#                points.append((r, ci))
#        print(r, c)
#        for ri, ci in points:
#            init[r][c] += free_vars[ri][ci]
#            print(f"  ({ri}, {ci})")
#
#formula = SMTBit(1)
#for r in range(n):
#    for c in range(n):
#        print(r,c,init[r][c])
#        formula &= init[r][c] == SBV[1](0)
#
#print(formula)
#
#with smt.Solver('z3', logic=BV) as solver:
#    solver.add_assertion(formula.value)
#    solved = solver.solve()
#    assert solved
#    print("Solved")
#    for r in range(n):
#        rvals = []
#        for c in range(n):
#            var = free_vars[r][c]
#            smt_var = solver.get_value(var.value)
#            cval = smt_var.constant_value() 
#            rvals.append(str(int(cval)))
#        print(" ".join(rvals))

