import itertools as it
import hwtypes as ht
from hwtypes import smt_utils as fc
import pysmt.shortcuts as smt
from shapely.geometry import LineString

board1_4x4 = [
    [0, 1, 0, 2],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [2, 0, 0, 3],
]
board1_7x7 = [
    [4, 0, 0, 3, 0, 0, 2],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 5, 0, 0, 5],
    [0, 0, 0, 0, 0, 1, 0],
    [3, 0, 1, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 5, 0, 3, 0],
]

board2_7x7 = [
    [4, 0, 0, 4, 0, 2, 0],
    [0, 0, 0, 0, 0, 0, 2],
    [0, 0, 0, 0, 0, 1, 0],
    [6, 0, 0, 6, 0, 0, 5],
    [0, 0, 0, 0, 0, 0, 0],
    [3, 0, 0, 5, 0, 2, 0],
    [0, 0, 0, 0, 0, 0, 2],
]

board3_7x7 = [
    [1, 0, 0, 0, 4, 0, 3],
    [0, 0, 0, 0, 0, 0, 0],
    [2, 0, 3, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 4, 0, 3, 0, 0],
    [1, 0, 0, 0, 0, 0, 1],
]

board1_15x15 = [
    [4, 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0, 3],
    [0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0],
    [0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
    [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 0, 5],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 5, 0, 0, 5, 0, 3, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0],
    [3, 0, 0, 0, 0, 2, 0, 0, 3, 0, 0, 0, 0, 0, 5],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 2, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
]

_cache = {}
def new_var(s, bvlen):
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

def solve(maxB, board=None):
    NR = len(board)
    NC = len(board[0])
    assert all(NC==len(b) for b in board)
    bvlen = (4*maxB).bit_length()
    BV0 = ht.SMTBitVector[bvlen](0)
    #Create Graph
    vs = {} #[v] -> num
    edges = [] #[ei] -> (sorted vpair, var)
    v_to_e = {} #[v] -> [ei]
    ei = 0
    for ri, row in enumerate(board):
        for ci, v in enumerate(row):
            if v==0:
                continue
            vs[(ri, ci)] = v
            r = ri
            while True:
                r += 1
                if r >= NR:
                    break
                if board[r][ci] == 0:
                    continue
                v0 = (ri, ci)
                v1 = (r, ci)
                var = new_var(f"{ri},{ci}-{r},{ci}", bvlen)
                data = (v0, v1, var)
                edges.append(data)
                v_to_e.setdefault(v0, []).append(ei)
                v_to_e.setdefault(v1, []).append(ei)
                ei += 1
                break
            c = ci
            while True:
                c += 1
                if c >= NC:
                    break
                if board[ri][c]==0:
                    continue
                v0 = (ri, ci)
                v1 = (ri, c)
                var = new_var(f"{ri},{ci}-{ri},{c}", bvlen)
                data = (v0, v1, var)
                edges.append(data)
                v_to_e.setdefault(v0, []).append(ei)
                v_to_e.setdefault(v1, []).append(ei)
                ei += 1
                break

    #All bridges are less than or equal to maxB
    max_cons = []
    for (_,_,v) in edges:
        max_cons.append(v <=maxB)

    #sum of bridges must be the vertex number
    v_cons = []
    for v, eis in v_to_e.items():
        v_cons.append(sum([edges[ei][2] for ei in eis], BV0) == vs[v])

    #No bridges must cross.
    #   Conflicting bridges must have one being 0

    # Calculates if 2 bridges intersect
    def intersects(v0_a, v1_a, v0_b, v1_b):
        all_v = [v0_a, v1_a, v0_b, v1_b]
        #Check for any overlapping points
        if any(all_v.count(v)>1 for v in all_v):
            return False
        la = LineString([v0_a, v1_a])
        lb = LineString([v0_b, v1_b])
        if la.intersects(lb):
            return True
        return False


    cross_cons = []
    for (v0_a, v1_a, var_a), (v0_b, v1_b, var_b) in it.combinations(edges, 2):
        if intersects(v0_a, v1_a, v0_b, v1_b):
            cross_cons.append((var_a==0) | (var_b==0))

    #Bridge graph needs to be connected

    f = fc.And([
        fc.And(max_cons),
        fc.And(v_cons),
        fc.And(cross_cons),
    ])
    print(f.serialize())
    f = f.to_hwtypes().value
    m = get_model(f)
    assert m is not False
    for v, val in m.items():
        print(str(v), val)

solve(2, board1_15x15)