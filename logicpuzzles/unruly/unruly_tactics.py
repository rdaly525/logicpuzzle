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



# The rules can be encoded as follows:
# Assuming I[N][N] is the set of indices
# val(i) is the value of the cell at index i
# Rule 1: No three consecutive squares in a row or column can be the same color
#   forall i,j,k, ((i+1)==j & (j+1)==k) => (val(i) != val(j) | val(j) != val(k) | val(i) != val(k))
# Rule 2: Each row and column must contain an equal number of black and white squares
#   forall k. sum(val(I[k])) == N//2
#   forall k. sum(val(I[:][k])) == N//2



# A tactic is a tuple (pattern, predicate, action).
# Example 1:(in english), if two of three consecutive cells are the same color, then the third must be different color
#   Given:
#     a set of 3 consecutive cells, (x, y, z,)
#     two are known, one is unknown,
#     and the two known are equal,
#     then the unknown must be the opposite color
#   This can be written as a logical predicate:
#       forall i, j, k, ((i+1)==j & (j+1)==k) &
#       num_possible(i)==1 & num_possible(j)==1 & num_possible(k)==2 & 
#       val(i) == val(j) => 
#       val(k) != val(i)
# Example 2: (in english), if in a row there are N//2-1 squares of the same color, then the remaining square must be the opposite color
#   This can be written as a logical predicate:
#       forall, ((i+1)==j & (j+1)==k) &
#       num_possible(i)==1 & num_possible(j)==1 & num_possible(k)==1 & 
#       val(i) == val(j) => 
#       val(k) != val(i)

# The action is a constraint. If it does not depend on other variables, it is a domain space reduction.
class Tactic:
    def __init__(self, pattern, predicate, action):
        self.pattern = pattern
        self.predicate = predicate
        self.action = action


# An unruly board is a grid of black, white, and empty squares
# black is 0, white is 1, empty is 2
class UnrulyBoard:
    def __init__(self, N, board=None, percent_filled=0.2):
        self.N = N
        if board is None:
            self._random_board(percent_filled)
        else:
            self.board = board
        assert len(self.board) == self.N
        assert all(len(row) == self.N for row in self.board)

    def _random_board(self, percent_filled=0.2):
        # Calculate number of squares to fill
        total_squares = self.N * self.N
        num_filled = int(total_squares * percent_filled)
        
        # Create list of all positions
        positions = [(r,c) for r in range(self.N) for c in range(self.N)]
        
        # Randomly select positions to fill
        fill_positions = random.sample(positions, num_filled)
        
        # Initialize board and fill selected positions
        self.board = [[2 for _ in range(self.N)] for _ in range(self.N)]
        for r,c in fill_positions:
            self.board[r][c] = random.randint(0,1)


    def pretty_print(self, sol=None):
        # First print the board
        print("\n".join([" ".join([str(self.board[r][c]) for c in range(self.N)]) for r in range(self.N)]))
        if sol is not None:
            print("\n")
            # Then print the solution
            print("\n".join([" ".join([str(sol[r][c]) for c in range(self.N)]) for r in range(self.N)]))


class UnrulySolver(SMTConstraintProblem):
    def __init__(self, board, verbose=False):
        bvlen = len(bin(board.N))
        super().__init__(default_bvlen=bvlen, verbose=verbose)
        self.board = board

        # Create the problem variables
        self.vars = [[self.new_var(f"x_{r}_{c}") for c in range(self.board.N)] for r in range(self.board.N)]

    def constraint_binary(self):
        # Each cell must be either 0 or 1
        for r, c in it.product(range(self.board.N), range(self.board.N)):
            self.add_constraint((self.vars[r][c] < 2))

    def constraint_initial_board(self):
        # Each cell must match initial board where specified
        for r, c in it.product(range(self.board.N), range(self.board.N)):
            if self.board.board[r][c] != 2:
                self.add_constraint(self.vars[r][c] == self.board.board[r][c])

    def constraint_no_consecutive(self):
        # No three consecutive cells can be same color in rows or columns
        for r in range(self.board.N):
            for c in range(self.board.N-2):
                # Check rows
                self.add_constraint(~((self.vars[r][c]==1) & (self.vars[r][c+1]==1) & (self.vars[r][c+2]==1)))
                self.add_constraint(~((self.vars[r][c]==0) & (self.vars[r][c+1]==0) & (self.vars[r][c+2]==0)))

        for r in range(self.board.N-2):
            for c in range(self.board.N):
                # Check columns  
                self.add_constraint(~((self.vars[r][c]==1) & (self.vars[r+1][c]==1) & (self.vars[r+2][c]==1)))
                self.add_constraint(~((self.vars[r][c]==0) & (self.vars[r+1][c]==0) & (self.vars[r+2][c]==0)))

    def constraint_equal_counts(self):
        # Equal number of black and white in each row and column
        for r in range(self.board.N):
            row_sum = self.gen_total(self.vars[r])
            self.add_constraint(row_sum == self.board.N//2)

        for c in range(self.board.N):
            col_sum = self.gen_total([self.vars[r][c] for r in range(self.board.N)])
            self.add_constraint(col_sum == self.board.N//2)

    def constraint_unruly(self):
        self.constraint_initial_board()
        self.constraint_no_consecutive() 
        self.constraint_equal_counts()
        self.constraint_binary()

    def solve(self):
        self.constraint_unruly()
        for model in super().solve():
            yield [[model[self.vars[r][c].value] for c in range(self.board.N)] for r in range(self.board.N)]


##WORKS
#n = 8
#
##white 1, black 2
#board = [
#    [1, 2, 0, 2, 0, 0, 1, 0],
#    [0, 0, 0, 0, 0, 1, 0, 0],
#    [0, 2, 0, 0, 0, 0, 0, 1],
#    [0, 0, 2, 0, 1, 0, 0, 0],
#    [0, 0, 0, 0, 0, 0, 1, 1],
#    [0, 0, 1, 0, 0, 2, 0, 0],
#    [0, 0, 0, 0, 1, 0, 0, 0],
#    [0, 1, 1, 0, 0, 0, 0, 0],
#]
#
#fvs = [[SBV[1](name=f"{r},{c}") for r in range(n)] for c in range(n)]
#
#def f(a,b,c):
#    return (a&b&c == 0) & (a|b|c == 1)
#
#formula = SMTBit(1)
#for r in range(n):
#    for c in range(n):
#        #Initial board must match
#        if board[r][c] == 1:
#            formula &= fvs[r][c] == SBV[1](0)
#        if board[r][c] == 2:
#            formula &= fvs[r][c] == SBV[1](1)
#        # No 3 consecutive can be the same color
#        if r in range(1, n-1):
#            formula &= f(fvs[r-1][c], fvs[r][c], fvs[r+1][c])
#        if c in range(1, n-1):
#            formula &= f(fvs[r][c-1], fvs[r][c], fvs[r][c+1])
#
##Sum of each column and row must equal n/2
#sbits = len(bin(n))-2
#for r in range(n):
#    s = SBV[sbits](0)
#    for c in range(n):
#        s += fvs[r][c].zext(sbits-1)
#    formula &= (s == n//2)
#
#for c in range(n):
#    s = SBV[sbits](0)
#    for r in range(n):
#        s += fvs[r][c].zext(sbits-1)
#    formula &= (s == n//2)
#
#with smt.Solver('z3', logic=BV) as solver:
#    solver.add_assertion(formula.value)
#    solved = solver.solve()
#    assert solved
#    print("Solved")
#    for r in range(n):
#        rvals = []
#        for c in range(n):
#            var = fvs[r][c]
#            smt_var = solver.get_value(var.value)
#            cval = smt_var.constant_value() 
#            rvals.append(str(int(cval)))
#        print(" ".join(rvals))
#
#