from enum import Enum
import hwtypes as ht

class Board:
    def __init__(self, board: str, key_to_op):
        key_to_locs = {v:[] for v in key_to_op}
        vars = {}
        N = int(len(board.strip())**0.5)
        for r, row in enumerate(board.strip().split('\n')):
            for c, v in enumerate(row):
                vars[(r,c)] = ht.SMTBitVector[]
                assert v in key_to_op
                key_to_locs[v].append((r,c))
        assert





board0 = """
aabb
ccde
fgde
fghh
"""

key0 = dict(
    a=(2, '/'),
    b=(1, '-'),
    c=(6, '+'),
    d=(5, '+'),
    e=(4, '*'),
    f=(1, '-'),
    g=(3, '*'),
    h=(2, '/'),
)

b = Board(board0, key0)
