from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV
from functools import partial, reduce, lru_cache
import operator
or_reduce = partial(reduce, operator.or_)
and_reduce = partial(reduce, operator.and_)



#WORKS
n = 7

#white 1, black 2
board = [
    [
        (7, 1),
        (7, 0),
        (7, 0),
        (0, 0),
        (7, 0),
        (5, 0),
        (5, 0),
    ],
    [
        (0, 34),
        (7, 0),
        (6, 35),
        (4, 0),
        (3, 0),
        (4, 32),
        (5, 12),
    ],
    [
        (0, 20),
        (0, 0),
        (7, 0),
        (3, 0),
        (3, 0),
        (5, 0),
        (4, 0),
    ],
    [
        (6, 0),
        (2, 0),
        (0, 0),
        (5, 0),
        (5, 0),
        (6, 0),
        (2, 0),
    ],
    [
        (0, 0),
        (3, 28),
        (3, 0),
        (6, 0),
        (3, 0),
        (5, 0),
        (3, 23),
    ],
    [
        (2, 17),
        (2, 0),
        (2, 0),
        (0, 0),
        (7, 0),
        (2, 40),
        (4, 0),
    ],
    [
        (1, 0),
        (2, 0),
        (0, 0),
        (4, 0),
        (2, 0),
        (2, 39),
        (8, 49),
    ],
]
fvs = [[SBV[6](name=f"{r},{c}") for r in range(n)] for c in range(n)]

lut = {
    0: (0, 1),
    1: (-1, 1),
    2: (-1, 0),
    3: (-1, -1),
    4: (0, -1),
    5: (1, -1),
    6: (1, 0),
    7: (1, 1),
}

def inbounds(v):
    return v >=0 and v < n

formula = []
for r in range(n):
    for c in range(n):
        cur = fvs[r][c]
        direction, val = board[r][c]
        if val !=0:
            formula.append(cur == val)
        else:
            formula.append(cur > 0)
        if direction == 8:
            continue
        d_r, d_c = lut[direction]
        poss = []
        for i in range(1, n):
            n_r = r + i*d_r
            n_c = c + i*d_c
            if inbounds(n_r) and inbounds(n_c):
                next_fv = fvs[n_r][n_c]
                poss.append(cur + 1 == next_fv)
        if len(poss) > 0:
            formula.append(or_reduce(poss))

print("formula")
for v in formula:
    print("  ",v.value)
print(">")
with smt.Solver('z3', logic=BV) as solver:
    solver.add_assertion(and_reduce(formula).value)
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


    for r in range(n):
        for c in range(n):
            var = fvs[r][c]
            smt_var = solver.get_value(var.value)
            cval = smt_var.constant_value()
            print(f"({r},{c}) = {cval}")



