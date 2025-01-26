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

import random
import itertools as it
from ..board import Board, Face, Vertex, Edge
from dataclasses import dataclass

class DominosaBoard(Board):
    @dataclass 
    class face_t(Face):
        val: int = None
        def __str__(self):
            if self.val is None:
                return " "
            return str(self.val)

    vertex_t = Vertex
    edge_t = Edge

    def __init__(self, N, board=None):
        # For N, we need N rows and N+1 columns
        super().__init__(N, N+1)
        self.N = N
        self.ds = list(it.combinations_with_replacement(range(self.N), 2))
        
        if board is None:
            self._init_random()
        else:
            for (r, c), face in self.f.items():
                face.val = board[r][c]

    def _init_random(self):
        while True:
            di_to_locs = {}
            di = 0
            board = [[None for _ in range(self.nC)] for _ in range(self.nR)]
            success = True
            for r, c in it.product(range(self.nR), range(self.nC)):
                if board[r][c] is not None:
                    continue
                opts = [
                    r+1 < self.nR and board[r+1][c] is None,
                    c+1 < self.nC and board[r][c+1] is None
                ]
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
                board[r][c] = di
                board[other_rc[0]][other_rc[1]] = di
                di += 1
            if success:
                break

        ds = list(self.ds)
        random.shuffle(ds)
        for di, vs in enumerate(ds):
            if random.choice([0,1]):
                vs = list(reversed(vs))
            for i, loc in enumerate(di_to_locs[di]):
                board[loc[0]][loc[1]] = vs[i]

        for (r, c), face in self.f.items():
            face.val = board[r][c]

    def verify(self, dlocs):
        tiles = []
        board = [[0 for _ in range(self.nC)] for _ in range(self.nR)]
        for (r,c,i) in dlocs:
            v0 = self.f[(r,c)].val
            other = (r+1, c) if i==0 else (r, c+1)
            v1 = self.f[other].val
            tiles.append(sorted([v0, v1]))
            board[r][c] += 1
            board[other[0]][other[1]] += 1
        assert all(all(v==1 for v in board[r]) for r in range(self.nR))
        for t0, t1 in it.combinations(tiles, 2):
            assert t0 != t1

    def pretty_print(self, dlocs):
        h_borders = [[True]*(self.nC+1) for _ in range(self.nR+1)]
        v_borders = [[True]*(self.nC+1) for _ in range(self.nR+1)]
        
        for r,c,dir in dlocs:
            if dir == 0: # vertical
                h_borders[r+1][c] = False
            else: # horizontal
                v_borders[r][c+1] = False
                
        result = []
        result.append('+' + ''.join('---+' if h_borders[0][c] else '   +' for c in range(self.nC)))
        
        for r in range(self.nR):
            row = '|'
            for c in range(self.nC):
                row += f' {self.f[(r,c)].val} '
                row += '|' if v_borders[r][c+1] else ' '
            result.append(row)
            
            row = '+'
            for c in range(self.nC):
                row += '---' if h_borders[r+1][c] else '   '
                row += '+'
            result.append(row)
            
        return '\n'.join(result)