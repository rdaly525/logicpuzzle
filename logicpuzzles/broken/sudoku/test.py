from hwtypes import SMTBitVector
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV


SBV = SMTBitVector[10]


#WORKS
n = 9
board = [
    [6, 3, 0, 0, 0, 0, 0, 8, 1],
    [0, 2, 0, 0, 0, 3, 0, 0, 0],
    [0, 0, 0, 0, 1, 7, 4, 3, 0],
    [0, 9, 6, 4, 0, 0, 5, 7, 0],
    [0, 0, 0, 7, 6, 2, 0, 0, 0],
    [0, 8, 0, 0, 0, 0, 6, 0, 0],
    [0, 6, 0, 0, 2, 0, 0, 0, 0],
    [3, 0, 9, 0, 0, 0, 0, 6, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 9],
]





free_vars = [[SBV(name=f"{r},{c}") for r in range(9)] for c in range(9)]
f = SMTBit(1)

#initial conditions
#initial values must be the value
# values must be between 1 to 9
formula = SMTBit(1)
for r in range(n):
    for c in range(n):
        v = free_vars[r][c]
        if board[r][c] !=0:
            formula &= (v == board[r][c])
        else:
            formula &= (v > 0) & (v<=9)

#uniqueness of rows, columns, blocks
def unique(vs: list):
    assert len(vs)==9
    s = SBV(0)
    for v in vs:
        s |= (SBV(1)<<(v-1))
    global formula
    formula &= (s==2**9 -1)

#rows
for r in free_vars:
    unique(r)

#columns
for c in range(9):
    col = [free_vars[r][c] for r in range(9)]
    unique(col)

#blocks
for r in range(3):
    for c in range(3):
        b = []
        for rr in range(3):
            for cc in range(3):
                b.append(free_vars[r*3+rr][c*3+cc])
        unique(b)

print(formula)

with smt.Solver('z3', logic=BV) as solver:
    solver.add_assertion(formula.value)
    solved = solver.solve()
    if solved:
        solved_board = [[int(solver.get_value(free_vars[r][c].value).constant_value()) for r in range(9)] for c in range(9)]
    else:
        raise ValueError("No Solution!")

print("Solved")
for r in range(9):
    rvals = []
    for c in range(n):
        rvals.append(str(solved_board[r][c]))
    print(" ".join(rvals))
#check if unique


