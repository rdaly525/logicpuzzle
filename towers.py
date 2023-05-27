from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV



N = 4
T = [2,1,3,2]
B = [1,2,2,3]
L = [2,4,2,1]
R = [3,1,2,3]

board = [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]

formula = SMTBit(1)
fvs = [[SBV[N](name=f"{r},{c}") for c in range(N)] for r in range(N)]
for r in range(N):
    for c in range(N):
        if board[r][c] != 0:
            formula &= (fvs[r][c]==board[r][c])

forms = []
for (kind, bound) in (
    ("T", T),
    ("B", B),
    ("L", L),
    ("R", R),
):
    for i, bval in enumerate(bound):
        t = []
        if kind == "T":
            #Top
            start = (0, i)
            v = (1, 0)
        elif kind == "B":
            start = (N-1, i)
            v = (-1, 0)
        elif kind == "L":
            start = (i, 0)
            v = (0, 1)
        elif kind == "R":
            start = (i, N-1)
            v = (0, -1)

        def f(j):
            idx = (v[0]*j+start[0],v[1]*j+start[1])
            print(kind, idx)
            t.append(fvs[idx[0]][idx[1]])
        for j in range(N):
            f(j)
        forms.append((kind, bval, t))

for kind, val, ts in forms:
    print(kind, val)
    for t in ts:
        print(f"  {t}")

def form(order, t):
    n = len(t)
    assert order <= n
    conds = []
    for i in range(n-order):
    #TODO
