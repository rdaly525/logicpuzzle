from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV



#WORKS
n = 8

#white 1, black 2
board = [
    [1, 2, 0, 2, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 2, 0, 0, 0, 0, 0, 1],
    [0, 0, 2, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 1, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 0, 0],
]

fvs = [[SBV[1](name=f"{r},{c}") for r in range(n)] for c in range(n)]

def f(a,b,c):
    return (a&b&c == 0) & (a|b|c == 1)

formula = SMTBit(1)
for r in range(n):
    for c in range(n):
        #Initial board must match
        if board[r][c] == 1:
            formula &= fvs[r][c] == SBV[1](0)
        if board[r][c] == 2:
            formula &= fvs[r][c] == SBV[1](1)
        # No 3 consecutive can be the same color
        if r in range(1, n-1):
            formula &= f(fvs[r-1][c], fvs[r][c], fvs[r+1][c])
        if c in range(1, n-1):
            formula &= f(fvs[r][c-1], fvs[r][c], fvs[r][c+1])

#Sum of each column and row must equal n/2
sbits = len(bin(n))-2
for r in range(n):
    s = SBV[sbits](0)
    for c in range(n):
        s += fvs[r][c].zext(sbits-1)
    formula &= (s == n//2)

for c in range(n):
    s = SBV[sbits](0)
    for r in range(n):
        s += fvs[r][c].zext(sbits-1)
    formula &= (s == n//2)

with smt.Solver('z3', logic=BV) as solver:
    solver.add_assertion(formula.value)
    solved = solver.solve()
    assert solved
    print("Solved")
    for r in range(n):
        rvals = []
        for c in range(n):
            var = fvs[r][c]
            smt_var = solver.get_value(var.value)
            cval = smt_var.constant_value() 
            rvals.append(str(int(cval)))
        print(" ".join(rvals))

