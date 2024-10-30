
from enum import Enum
from collections import namedtuple

import itertools as it
import hwtypes as ht
from hwtypes import smt_utils as fc
import pysmt.shortcuts as smt


_cache = {}
def new_var(s, bvlen):
    if bvlen is None:
        return ht.SMTBit(name=s)
    if s in _cache:
        return _cache[s]
    v = ht.SMTBitVector[bvlen](name=s)
    _cache[s] = v
    return v

def get_model(query, solver_name='z3', logic=None):
    vars = query.get_free_variables()
    model = smt.get_model(smt.And(query), solver_name=solver_name, logic=logic)
    if model:
        return {v: int(model.get_value(v).constant_value()) for v in vars}
    return False


Spot = namedtuple("Spot", ("idx","bounced"))
class Kind(Enum):
    diagl=0
    diagr=1
    space=2
    zomb=3
    vamp=4
    ghost=5

class Board:
    class Dir(Enum):
        U=0
        D=1
        L=2
        R=3

    def __init__(self, board, *,t,l,r,b):
        self.board = board
        self.constraints = dict(
            t=t,
            l=l,
            r=r,
            b=b
        )
        self.row_len = len(t)
        self.col_len = len(r)
        assert self.row_len == len(b)
        assert self.col_len == len(r)
        assert len(self.board) == self.row_len*self.col_len

    def path(self, idx : int, dir : Dir, bounced=False, spots=[]):
        if board[idx] is Kind.diagl:
            bounced = True
            new_dir = blah
            new_idx = blah
            return self.path(new_idx, new_dir, bounced, spots)
        if board[idx] is Kind.diagr:
            bounced = True
            new_dir = blah
            new_idx = blah
            return self.path(new_idx, new_dir, bounced, spots)
        if board[idx] is Kind.space:
            spots.append(Spot(idx=idx,bounced=bounced))
            new_dir = dir
            new_idx = blah
            return self.path(new_idx, new_dir, bounced, spots)

    def _next(self, idx, dir):
        raise NotImplementedError
        #returns the new_idx or None
        #loc =


char_to_enum = {
    "\\":Kind.diagl,
    "/":Kind.diagr,
    " ":Kind.space,
    "z":Kind.zomb,
    "v":Kind.vamp,
    "g":Kind.ghost
}

def parse(board_str,*,t,l,r,b):
    rows = board_str.split("\n")
    if len(rows[0])==0:
        rows = rows[1:]
    if len(rows[-1])==0:
        rows = rows[:-1]

    row_len = len(rows)
    col_len = None
    board = []
    for row in rows:
        cols = row.split(",")
        if col_len is None:
            col_len = len(cols)
        assert len(cols) == col_len
        for col in cols:
            assert col in char_to_enum
            board.append(char_to_enum[col])
    for v in board:
        assert v.value < 4
    b = Board(board,t=t,l=l,r=r,b=b)
    return b

def test():
    board = """
\,/, ,/
 , , , 
/,/,\, 
 , , ,\\
"""
    t = (0,0,1,3)
    l = (0,3,0,1)
    r = (0,3,3,0)
    b = (2,2,0,2)
    board = parse(board,t=t,l=l,r=r,b=b)
    print(board)

test()
