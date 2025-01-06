from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV



#WORKS
n = 5
board = [
    [1, 1, 0, 1, 1],
    [1, 1, 1, 1, 0],
    [0, 1, 1, 0, 1],
    [1, 0, 1, 1, 1],
    [0, 1, 1, 1, 0],
]

init = [[SBV[1](v) for v in row] for row in board]

free_vars = [[SBV[1](name=f"{r},{c}") for r in range(n)] for c in range(n)]

for r in range(n):
    for c in range(n):
        points = [(r, c)]
        for offset in (-1, 1):
            ri = r + offset
            if 0 <= ri < n:
                points.append((ri, c))
            ci = c + offset
            if 0 <= ci < n:
                points.append((r, ci))
        print(r, c)
        for ri, ci in points:
            init[r][c] += free_vars[ri][ci]
            print(f"  ({ri}, {ci})")

formula = SMTBit(1)
for r in range(n):
    for c in range(n):
        print(r,c,init[r][c])
        formula &= init[r][c] == SBV[1](0)

print(formula)

with smt.Solver('z3', logic=BV) as solver:
    solver.add_assertion(formula.value)
    solved = solver.solve()
    assert solved
    print("Solved")
    for r in range(n):
        rvals = []
        for c in range(n):
            var = free_vars[r][c]
            smt_var = solver.get_value(var.value)
            cval = smt_var.constant_value() 
            rvals.append(str(int(cval)))
        print(" ".join(rvals))

