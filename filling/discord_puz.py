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



def solve(init):
    nR = len(init['l'])
    nC = len(init['t'])
    bvlen = 6
    zero = ht.SMTBitVector[bvlen](0)
    one = ht.SMTBitVector[bvlen](1)

    # Use shifts.
    def digits_to_num(fs):
        n = len(fs)
        biglen = 4*n
        v = ht.SMTBitVector[biglen](0)
        for i, f in enumerate(fs):
            v |= f.zext(biglen-bvlen) << (4*i)
        return v


    def face_to_idx(f):
        r, c = f
        return r*nC + c

    def face_iter():
        yield from it.product(range(nR), range(nC))

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
        if r < nR-1:
            yield r+1, c
        if c > 0:
            yield r, c-1
        if c < nC-1:
            yield r, c+1

    #Free Variables:
    #Edges
    edges = {}
    for f0 in face_iter():
        for f1 in adj(f0):
            #e_from_to
            edges[(f0, f1)] = new_var(f"e_{f0}_{f1}", None)

    #Tree Count
    tcounts = {}
    #Fill number
    fills = {}
    #root index
    roots = {}
    for f in face_iter():
        tcounts[f] = new_var(f"tc_{f}", bvlen)
        fills[f] = new_var(f"f_{f}", bvlen)
        roots[f] = new_var(f"r_{f}", bvlen)

    ranks = {}
    for s in 'tblr':
        rs = init[s]
        for i in range(len(rs)):
            ranks[(s, i)] = new_var(f"rank_{s}{i}", bvlen)


    #Constraints:

    #At most one directed edge
    c_directed = []
    for f0, f1 in edge_iter():
        e0 = edges[(f0, f1)]
        e1 = edges[(f1, f0)]
        c_directed.append(~(e0 & e1))

    #each face has at most one incoming edge
    c_in_edge = []
    for f0 in face_iter():
        es = [edges[(f1, f0)] for f1 in adj(f0)]
        c_in_edge.append(bools_one(es) | bools_none(es))

    #tree count is the sum of the counts of incoming edges + 1
    #tree count is less than or equal to 9
    c_treecount = []
    for f0 in face_iter():
        es = [edges[(f0, f1)].ite(tcounts[f1], zero) for f1 in adj(f0)]
        c_treecount.append(tcounts[f0] == sum(es, one))
        c_treecount.append(tcounts[f0] <= 9)
        c_treecount.append(tcounts[f0] > 0)
    #Fill is equal across edges
    c_fill_eq = []
    for f0, f1 in edge_iter():
        e0 = edges[(f0, f1)]
        e1 = edges[(f1, f0)]
        c_fill_eq.append(fc.Implies(e0|e1, fills[f0]==fills[f1]))

    is_roots = {}
    for f0 in face_iter():
        es = [edges[(f1, f0)] for f1 in adj(f0)]
        is_roots[f0] = bools_none(es)

    #at roots, tcount is the same as fill
    c_tc_is_fill = []
    for f, is_root in is_roots.items():
        c_tc_is_fill.append(fc.Implies(is_root, tcounts[f]==fills[f]))

    #at roots, root is root index
    c_root = []
    for f, is_root in is_roots.items():
        c_root.append(fc.Implies(is_root, roots[f] == face_to_idx(f)))

    #neighbor fills implies roots are the same
    c_boundary = []
    for f0 in face_iter():
        for f1 in adj(f0):
            c_boundary.append(fc.Implies(fills[f0]==fills[f1], roots[f0]==roots[f1]))

    #Fills have a max of 9
    c_fill_max = []
    for fill in fills.values():
        c_fill_max.append(fill <= 9)

    #Extra constraint for optimization
    c_tc_lte_fill = []
    for f in face_iter():
        c_tc_lte_fill.append(tcounts[f] <= fills[f])

    #Ranks are between 1 and 36
    c_rank_range = []
    #Rank is the same as init if exists
    c_rank_init = []
    for (s, i), rank in ranks.items():
        c_rank_range.append(rank > 0)
        c_rank_range.append(rank <=36)
        if init[s][i] > 0:
            c_rank_init.append(rank==init[s][i])

    #ranks are unique
    c_rank_unique = []
    for rank0, rank1 in it.combinations(ranks.values(), 2):
        assert rank0 is not rank1
        c_rank_unique.append(rank0!=rank1)

    digits = {}
    #Largest digit at index 0
    for r in range(nR):
        vs = [fills[(r,c)] for c in range(nC)]
        digits[('l', r)] = vs
        digits[('r', r)] = list(reversed(vs))
    for c in range(nC):
        vs = [fills[(r,c)] for r in range(nR)]
        digits[('t', c)] = vs
        digits[('b', c)] = list(reversed(vs))

    # xs > ys
    def gt(xs, ys):
        res = []
        for i, (x, y) in enumerate(zip(xs,ys)):
            conds = [x==y for x, y in zip(xs[:i], ys[:i])] + [x > y]
            res.append(fc.And(conds))
        return fc.Or(res)

    #rank ordering
    c_rank_order = []
    for (r0, rank0), (r1, rank1) in it.combinations(ranks.items(), 2):
        d0 = digits[r0]
        d1 = digits[r1]
        c_rank_order.append(fc.Implies(rank0 > rank1, gt(d0, d1)))
        c_rank_order.append(fc.Implies(rank0 < rank1, gt(d1, d0)))


    f = fc.And([
        fc.And(c_directed),
        fc.And(c_in_edge),
        fc.And(c_treecount),
        fc.And(c_fill_eq),
        fc.And(c_tc_is_fill),
        fc.And(c_root),
        fc.And(c_boundary),
        fc.And(c_fill_max),
        fc.And(c_tc_lte_fill),
        # rank related
        fc.And(c_rank_range),
        fc.And(c_rank_init),
        fc.And(c_rank_unique),
        fc.And(c_rank_order),
    ])
    print(f.serialize())
    f = f.to_hwtypes().value
    m = get_model(f)
    assert m is not False
    for v, val in m.items():
        print(str(v), val)

    fill_str = "\n".join([" ".join([str(m[fills[(r, c)].value]) for c in range(nC)]) for r in range(nR)])
    print(fill_str)

    for s in 'tblr':
        print(f"{s}:", " ".join([str(m[ranks[(s,i)].value]) for i in range(len(init[s]))]))



    #pretty print
    s = []
    for r in range(nR):
        rstr = []
        for c in range(nC):
            fv = m[fills[(r,c)].value]
            tcv = m[tcounts[(r,c)].value]
            rv = m[roots[(r,c)].value]
            rstr.append(f"{fv}, {rv:<2}, {face_to_idx((r,c)):<2}")
        s.append("|".join(rstr))
    print("\n\n".join(s))


puz = dict(
    t = [5,  0,  0,  0,  0, 25, 13, 0, 0],
    b = [0,  0,  0, 15,  0, 28,  0, 0, 0],
    l = [36, 0, 16,  0, 27,  0,  0, 0, 0],
    r = [0, 31,  8,  0,  0,  0,  0, 0, 0],
)

solve(puz)


