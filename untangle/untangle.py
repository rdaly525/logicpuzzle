import itertools as it
import hwtypes as ht
from hwtypes import smt_utils as fc
import pysmt.shortcuts as smt
from shapely.geometry import LineString
import networkx as nx
import matplotlib.pyplot as plt

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



def solve(g: nx.Graph):
    N = len(g.nodes)
    bvlen = 16
    pos = {n: (new_var(f"{n}_x", bvlen), new_var(f"{n}_y", bvlen)) for n in g.nodes}
    c_intersects = []
    for ea, eb in it.combinations(g.edges, 2):
        a0, a1 = pos[ea[0]], pos[ea[1]]
        b0, b1 = pos[eb[0]], pos[eb[1]]
        c_intersects.append(in

    f = fc.And([
        fc.And(c_intersects),
    ])
    print(f.serialize())
    f = f.to_hwtypes().value
    m = get_model(f)
    assert m is not False
    for v, val in m.items():
        print(str(v), val)

es = [
    (0, 2),
    (0, 5),
    (0, 8),
    (0, 9),
    (1, 2),
    (1, 4),
    (1, 7),
    (1, 8),
    (2, 1),
    (2, 0),
    (2, 3),
    (2, 7),
    (3, 2),
    (3, 7),
    (3, 9),
    (4, 1),
    (4, 5),
    (4, 6),
    (4, 8),
    (5, 4),
    (5, 0),
    (5, 6),
    (5, 9),
    (6, 5),
    (6, 9),
    (6, 4),
    (7, 3),
    (7, 2),
    (7, 1),
]
bvlen = 16
es = [e for e in es if e[0] < e[1]]

#Creates a graph with labeled nodes
def edges_to_nxgraph(es):
    g = nx.Graph()
    for e in es:
        g.add_edge(*e)
    return g

def show_nxgraph(g):
    nx.draw(g, with_labels=True)
    plt.show()

def solve(g: nx.Graph):
    pos = {}
    for n in g.nodes:
        pos[n] = (new_var(f"{n}_x", bvlen), new_var(f"{n}_y", bvlen))


def intersects(p0, p1):
    x0, y0 = p0
    x1, y1 = p1


g1 = edges_to_nxgraph(es)
solve(g1)
show_nxgraph(g1)
