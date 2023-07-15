import itertools as it

board = [
    [1,0,0,2,3],
    [0,1,3,2,1],
    [3,2,3,1,1],
    [2,2,3,0,0],
]

import random

class Board:
    def __init__(self, N, board=None):
        self.N = N
        self.NR = N
        self.NC = N + 1
        self.ds = list(it.combinations_with_replacement(range(self.N), 2))
        #board[r][c]
        if board is None:
            self._init_random()
        else:
            self.board = board

    def _init_random(self):
        while True:
            di_to_locs = {}
            di = 0
            self.board = [[None for _ in range(self.NC)] for _ in range(self.NR)]
            success = True
            for r, c in it.product(range(self.NR), range(self.NC)):
                if self.val(r, c) is not None:
                    continue
                opts = [self.val(r+1, c) is None, self.val(r, c+1) is None]
                if True not in opts:
                    success = False
                    break
                if all(opts):
                    idx = random.choice([0,1])
                else:
                    idx = opts.index(True)
                if idx==0:
                    other_rc = (r+1,c)
                else:
                    other_rc = (r, c+1)
                di_to_locs[di] = ((r,c), other_rc)
                self.set(r,c,di)
                self.set(*other_rc, di)
                di += 1
            if success:
                break
        ds = list(self.ds)
        random.shuffle(ds)
        for di, vs in enumerate(ds):
            if random.choice([0,1]):
                vs = list(reversed(vs))
            for i, loc in enumerate(di_to_locs[di]):
                self.set(*loc, vs[i])

    def _init_board(self, board):
        raise NotImplementedError

    def __str__(self):
        return "\n".join(["".join([str(self.val(r, c)) for c in range(self.NC)]) for r in range(self.NR)])

    def val(self, r, c):
        if r >= self.NR or c >= self.NC:
            return -1
        return self.board[r][c]

    def set(self, r, c, val):
        if r >= self.NR or c >= self.NC:
            print(r,c,val)
            raise ValueError
        self.board[r][c] = val

    def verify(self, dlocs):
        assert len(dlocs) == self.N * (self.N+1)/2
        tiles = []
        board = [[0 for _ in range(self.NC)] for _ in range(self.NR)]
        for (r,c,i) in dlocs:
            v0 = self.val(r,c)
            other = (r+1, c) if i==0 else (r, c+1)
            v1 = self.val(*other)
            tiles.append(sorted([v0, v1]))
            board[r][c] += 1
            board[other[0]][other[1]] += 1
        assert all(all(v==1 for v in board[r]) for r in range(self.NR))
        for t0, t1 in it.combinations(tiles, 2):
            assert t0 != t1



import hwtypes as ht
from hwtypes import smt_utils as fc
import pysmt.shortcuts as smt

def new_var(s):
    cache = {}
    if s in cache:
        return cache[s]
    v = ht.SMTBit(name=s)
    return v

def get_model(query, solver_name='z3', logic=None):
    vars = query.get_free_variables()
    model = smt.get_model(smt.And(query), solver_name=solver_name, logic=logic)
    if model:
        return {v: model.get_value(v).constant_value() for v in vars}
    return False

#  c c c c c  c c c c
#r
#r
#r     (r,c) |   <- 1
#r      ---
#r       0
#r
def solve(b: Board):
    NR, NC, N = b.NR, b.NC, b.N
    poss = {}
    for r in range(NR):
        for c in range(NC):
            poss[(r, c)] = (new_var(f"{r},{c},0"), new_var(f"{r},{c},1"))

    def get(r,c,i):
        if r in range(NR) and c in range(NC):
            return poss[(r, c)][i]
        else:
            return ht.SMTBit(0)
    # Board edge constraints
    edge_cons = [
        fc.And([~get(NR-1, c, 0) for c in range(NC)]),
        fc.And([~get(r, NC-1, 1) for r in range(NR)]),
    ]

    # Dominoe Border constraints

    border_cons = []
    for r in range(NR):
        for c in range(NC):
            d0 = get(r,c,0)
            border0 = (
                (r-1, c, 0),
                (r+1, c, 0),
                (r, c, 1),
                (r+1, c, 1),
                (r, c-1, 1),
                (r+1, c-1, 1),
            )
            d1 = get(r, c, 1)
            border1 = (
                (r, c-1, 1),
                (r, c+1, 1),
                (r, c, 0),
                (r, c+1, 0),
                (r-1, c, 0),
                (r-1, c+1, 0),
            )
            for d, border in ((d0, border0), (d1, border1)):
                border_cons.append(fc.Implies(d, fc.And([~get(*b) for b in border])))

    # Dominoe Constraints
    # At least one dominoe per square
    dsquare_cons = []
    for r in range(NR):
        for c in range(NC):
            edges = (
                (r, c, 0),
                (r-1, c, 0),
                (r, c, 1),
                (r, c-1, 1),
            )
            dsquare_cons.append(fc.Or([get(*e) for e in edges]))

    # Number constraints
    num_cons = []
    vals = []
    for r in range(NR):
        for c in range(NC):
            for i in range(2):
                other = (r, c+1) if i==1 else (r+1, c)
                vb = b.val(*other)
                if vb < 0:
                    continue
                va = b.val(r, c)
                vs = sorted([va, vb])
                vals.append((get(r,c,i),vs))
    for (d0, vs0), (d1, vs1) in it.combinations(vals, 2):
        if vs0 == vs1:
            num_cons.append(~(d0 & d1))
    f = fc.And([
        fc.And(edge_cons),
        fc.And(border_cons),
        fc.And(dsquare_cons),
        fc.And(num_cons),
    ])
    f = f.to_hwtypes().value
    m = get_model(f)
    if m:
        sol = []
        for r in range(NR):
            for c in range(NC):
                v0 = poss[(r,c)][0]
                v1 = poss[(r,c)][1]
                if m[v0.value]:
                    sol.append((r,c,0))
                if m[v1.value]:
                    sol.append((r,c,1))
        assert len(sol) == (N+1)*N/2
        return sol
    return None