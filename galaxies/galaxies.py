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

def bools_one(vs):
    return fc.Or([
        fc.And([
            (v if j==i else ~v) for j,v in enumerate(vs)
        ]) for i in range(len(vs))
    ]).to_hwtypes()

def bools_none(vs):
    return fc.And([~v for v in vs]).to_hwtypes()

def bools_all(vs):
    return fc.And([v for v in vs]).to_hwtypes()

def bools_atleast_one(vs):
    raise NotImplementedError

from dataclasses import dataclass
import typing as tp

@dataclass
class Board:
    nR: int
    nC: int
    faces: tp.List[tp.Tuple[int, int]]
    edges: tp.List[tp.Tuple[
        tp.Tuple[int, int],
        tp.Tuple[int, int]
    ]]
    vertices: tp.List[tp.Tuple[int, int]]

    @property
    def N(self):
        return len(self.faces) + len(self.edges) + len(self.vertices)


def solve(b: Board):
    bvlen = b.N.bit_length()
    SBV = ht.SMTBitVector[bvlen]
    zero = SBV(0)
    one = SBV(1)


    def face_to_idx(f):
        r, c = f
        return r*b.nC + c

    def face_iter():
        yield from it.product(range(b.nR), range(b.nC))

    def edge_iter():
        for r, c in face_iter():
            if r > 0:
                yield (r, c), (r-1, c)
            if c > 0:
                yield (r, c), (r, c-1)

    def adj(f):
        r, c = f
        if r > 0:
            yield r-1, c
        if r < b.nR-1:
            yield r+1, c
        if c > 0:
            yield r, c-1
        if c < b.nC-1:
            yield r, c+1

    #Free Variables:
    vars = {}
    for r, c in face_iter():
        vars[(r, c)] = new_var(f"f_{r}_{c}", bvlen)

    #Constraints:
    c_varID = []
    for v in vars.values():
        c_varID.append(v < b.N)

    c_mirror = []
    for r, c in


    f = fc.And([
        fc.And(c_varID),
    ])
    print(f.serialize())
    f = f.to_hwtypes().value
    m = get_model(f)
    assert m is not False

    #pretty print
    s = []
    for r in range(b.nR):
        rstr = []
        for c in range(b.nC):
            fv = m[vars[(r, c)].value]
            rstr.append(f"{fv:<2}")
        s.append(" ".join(rstr))
    print("\n\n".join(s))


b1 = Board(
    nR=4,
    nC=4,
    faces=[(2, 0), (3, 1)],
    edges=[((0, 2), (1, 2)), ((1, 3), (1, 4)), ((2, 1), (2, 2)), ((3, 3), (3, 4))],
    vertices=[],
)


solve(b1)


