"""
Dominosa is a puzzle game where you are given a grid of numbers and must place dominoes to cover the entire grid.

Each domino covers exactly two adjacent squares (horizontally or vertically) and each domino must be used exactly once.
The numbers on the grid indicate which domino should cover that square.

For example, if a square has a 2 and an adjacent square has a 4, those squares must be covered by the [2,4] domino.

The goal is to place all dominoes such that:
1. Every square is covered by exactly one domino
2. Each domino is used exactly once
3. The numbers on the grid match the numbers on the domino covering them

For a puzzle with max number N, the available dominoes are all pairs [i,j] where 0 <= i <= j <= N.
"""


import itertools as it
from hwtypes import smt_utils as fc
from ..utils import smt_utils

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

    def __str__(self):
        return "\n".join(["".join([str(self.val(r, c)) for c in range(self.NC)]) for r in range(self.NR)])

    def val(self, r, c):
        if r >= self.NR or c >= self.NC or r < 0 or c < 0:
            return -1
        return self.board[r][c]

    def set(self, r, c, val):
        if r >= self.NR or c >= self.NC or r < 0 or c < 0:
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

    # Show the dominoes on the board include boundaries of the dominoes
    # For example, if the board is 
    # 0 1 2
    # 1 2 3
    # and the dominoes are (0,0,1), (0,2,0), (1,0,1),
    # the output should be:
    # +---+---+---+
    # | 0   1 | 2 |
    # +---+---+   +
    # | 1   2 | 3 |
    # +---+---+---+
    def pretty_print(self, dlocs):
        # Initialize empty grid with all borders
        h_borders = [[True]*(self.NC+1) for _ in range(self.NR+1)]
        v_borders = [[True]*(self.NC+1) for _ in range(self.NR+1)]
        
        # Remove borders between connected dominoes
        for r,c,dir in dlocs:
            if dir == 0: # vertical
                h_borders[r+1][c] = False
            else: # horizontal
                v_borders[r][c+1] = False
                
        # Build output string
        result = []
        
        # Top border
        result.append('+' + ''.join('---+' if h_borders[0][c] else '   +' for c in range(self.NC)))
        
        # Each row
        for r in range(self.NR):
            # Values with vertical borders
            row = '|'
            for c in range(self.NC):
                row += f' {self.val(r,c)} '
                row += '|' if v_borders[r][c+1] else ' '
            result.append(row)
            
            # Horizontal borders
            row = '+'
            for c in range(self.NC):
                row += '---' if h_borders[r+1][c] else '   '
                row += '+'
            result.append(row)
            
        return '\n'.join(result)



#  c c c c c  c c c c
#r
#r
#r     (r,c) |   <- 1
#r      ---
#r       0
#r

class DominosaSolver(smt_utils.SMTConstraintProblem):
    def __init__(
        self,
        b: Board,
        default_bvlen: int = 32,
        z3_solver=False,
        timeout=15000,
        logic=None,
        solver_name='z3',
        verbose=False,
    ):
        super().__init__(
            default_bvlen=default_bvlen,
            z3_solver=z3_solver,
            timeout=timeout,
            logic=logic,
            solver_name=solver_name,
            verbose=verbose,
        )
        self.b = b
        self.NR, self.NC, self.N = b.NR, b.NC, b.N
        self.poss = {}
        for r in range(self.NR):
            for c in range(self.NC):
                self.poss[(r, c)] = (self.new_var(f"{r},{c},0", 0, True), self.new_var(f"{r},{c},1", 0, True))
    

    def get(self, r, c, i):
        if r in range(self.NR) and c in range(self.NC):
            return self.poss[(r,c)][i]
        else:
            return self.Bit(0)

    # Board edge constraints
    def constraint_edge(self):
        for c in range(self.NC):
            self.add_constraint(~self.get(self.NR-1, c, 0))
        for r in range(self.NR):
            self.add_constraint(~self.get(r, self.NC-1, 1))

    # Dominoe Border constraints
    def constraint_border(self):
        for r in range(self.NR):
            for c in range(self.NC):
                d0 = self.get(r,c,0)
            border0 = (
                (r-1, c, 0),
                (r+1, c, 0),
                (r, c, 1),
                (r+1, c, 1),
                (r, c-1, 1),
                (r+1, c-1, 1),
            )
            d1 = self.get(r, c, 1)
            border1 = (
                (r, c-1, 1),
                (r, c+1, 1),
                (r, c, 0),
                (r, c+1, 0),
                (r-1, c, 0),
                (r-1, c+1, 0),
            )
            for d, border in ((d0, border0), (d1, border1)):
                self.add_constraint(fc.Implies(d, fc.And([~self.get(*b) for b in border])))

    # Each square must have at least one dominoe
    def constraint_domino(self):
        for r in range(self.NR):
            for c in range(self.NC):
                edges = (
                    (r, c, 0),
                    (r-1, c, 0),
                    (r, c, 1),
                    (r, c-1, 1),
                )
                self.add_constraint(fc.Or([self.get(*e) for e in edges]))

    def constraint_num(self):
        vals = []
        for r in range(self.NR):
            for c in range(self.NC):
                for i in range(2):
                    other = (r, c+1) if i==1 else (r+1, c)
                    vb = self.b.val(*other)
                    if vb < 0:
                        continue
                    va = self.b.val(r, c)
                    vs = sorted([va, vb])
                    vals.append((self.get(r,c,i), vs))
        for (d0, vs0), (d1, vs1) in it.combinations(vals, 2):
            if vs0 == vs1:
                self.add_constraint(~(d0 & d1))

    def solve(self, N: int):
        self.constraint_edge()
        self.constraint_border()
        self.constraint_domino()
        self.constraint_num()
        for model in super().solve(N):
            sol = []
            for r in range(self.NR):
                for c in range(self.NC):
                    for i in range(2):
                        if model[self.get(r,c,i).value]:
                            sol.append((r,c,i))
            yield sol


#def solve(b: Board):
#    NR, NC, N = b.NR, b.NC, b.N
#    poss = {}
#    for r in range(NR):
#        for c in range(NC):
#            poss[(r, c)] = (new_var(f"{r},{c},0"), new_var(f"{r},{c},1"))
#
#    def get(r,c,i):
#        if r in range(NR) and c in range(NC):
#            return poss[(r, c)][i]
#        else:
#            return ht.SMTBit(0)
#    # Board edge constraints
#    edge_cons = [
#        fc.And([~get(NR-1, c, 0) for c in range(NC)]),
#        fc.And([~get(r, NC-1, 1) for r in range(NR)]),
#    ]
#
#
#    border_cons = []
#    for r in range(NR):
#        for c in range(NC):
#            d0 = get(r,c,0)
#            border0 = (
#                (r-1, c, 0),
#                (r+1, c, 0),
#                (r, c, 1),
#                (r+1, c, 1),
#                (r, c-1, 1),
#                (r+1, c-1, 1),
#            )
#            d1 = get(r, c, 1)
#            border1 = (
#                (r, c-1, 1),
#                (r, c+1, 1),
#                (r, c, 0),
#                (r, c+1, 0),
#                (r-1, c, 0),
#                (r-1, c+1, 0),
#            )
#            for d, border in ((d0, border0), (d1, border1)):
#                border_cons.append(fc.Implies(d, fc.And([~get(*b) for b in border])))
#
#    # Dominoe Constraints
#    # At least one dominoe per square
#    dsquare_cons = []
#    for r in range(NR):
#        for c in range(NC):
#            edges = (
#                (r, c, 0),
#                (r-1, c, 0),
#                (r, c, 1),
#                (r, c-1, 1),
#            )
#            dsquare_cons.append(fc.Or([get(*e) for e in edges]))
#
#    # Number constraints
#    num_cons = []
#    vals = []
#    for r in range(NR):
#        for c in range(NC):
#            for i in range(2):
#                other = (r, c+1) if i==1 else (r+1, c)
#                vb = b.val(*other)
#                if vb < 0:
#                    continue
#                va = b.val(r, c)
#                vs = sorted([va, vb])
#                vals.append((get(r,c,i),vs))
#    for (d0, vs0), (d1, vs1) in it.combinations(vals, 2):
#        if vs0 == vs1:
#            num_cons.append(~(d0 & d1))
#    f = fc.And([
#        fc.And(edge_cons),
#        fc.And(border_cons),
#        fc.And(dsquare_cons),
#        fc.And(num_cons),
#    ])
#    f = f.to_hwtypes().value
#    m = get_model(f)
#    if m:
#        sol = []
#        for r in range(NR):
#            for c in range(NC):
#                v0 = poss[(r,c)][0]
#                v1 = poss[(r,c)][1]
#                if m[v0.value]:
#                    sol.append((r,c,0))
#                if m[v1.value]:
#                    sol.append((r,c,1))
#        assert len(sol) == (N+1)*N/2
#        return sol
#    return None