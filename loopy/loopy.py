import itertools
from collections import namedtuple
from itertools import product

from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV
from hwtypes.smt_utils import And, Or, Implies

from pysmt.logics import QF_BV

def _int_to_pysmt(x: int, sort):
    if sort.is_bv_type():
        return smt.BV(x % sort.width, sort.width)
    else:
        assert sort.is_bool_type()
        return smt.Bool(bool(x))

def cegis(query, E_vars, logic=QF_BV, max_iters=1000, solver_name="z3", verbose=False, exclude_list=[]):

    assert max_iters > 0

    for sol in exclude_list:
        sol_term = smt.Bool(True)
        for var, val in sol.items():
            sol_term = smt.And(sol_term, smt.Equals(var, val))
        query = smt.And(query, smt.Not(sol_term))

    #get exist vars:
    E_vars = set(E_vars)
    A_vars = query.get_free_variables() - E_vars  # exist vars

    with smt.Solver(logic=logic, name=solver_name) as solver:
        solver.add_assertion(smt.Bool(True))

        # Start with checking all A vals beings 0
        A_vals = {v: _int_to_pysmt(0, v.get_type()) for v in A_vars}
        solver.add_assertion(query.substitute(A_vals).simplify())
        for i in range(max_iters):
            if verbose and i%50==0:
                print(f".{i}", end='', flush=True)
            E_res = solver.solve()

            if not E_res:
                if verbose:
                    print("UNSAT")
                return None
            else:
                E_guess = {v: solver.get_value(v) for v in E_vars}
                query_guess = query.substitute(E_guess).simplify()
                model = smt.get_model(smt.Not(query_guess), solver_name=solver_name, logic=logic)
                if model is None:
                    if verbose:
                        print("SAT")
                    return E_guess
                else:
                    A_vals = {v: model.get_value(v) for v in A_vars}
                    solver.add_assertion(query.substitute(A_vals).simplify())

        raise IterLimitError(f"Unknown result in CEGIS in {max_iters} number of iterations")



def load_board(board_txt):
    lines = board_txt.split("\n")
    N = len(lines[0])
    assert all(len(line)==N for line in lines)
    board = [[int(v) if v != 'x' else None for v in line] for line in lines]
    assert len(board) == N
    return N, board


Edge = namedtuple('Edge', ['en', 'dir'])
#Edges are a list from 0 -> 3 (edges)
Face = namedtuple('Face', ['val', 'edges'])
Vertex = namedtuple('Vertex', ['val', 'edges'])
def doit(board_txt):
    N, faces = load_board(board_txt)
    #Each edge is on or off and a direction
    e_rows = [
        [
            Edge(
                en=SBV[3](name=f"r_en{i},{j}"),
                dir=SMTBit(name=f"r_dir{i},{j}"),
            ) for j in range(N+2)
        ] for i in range(N+1)
    ]
    e_cols = [
        [
            Edge(
                en=SBV[3](name=f"c_en{i},{j}"),
                dir=SMTBit(name=f"c_dir{i},{j}"),
            ) for j in range(N+2)
        ] for i in range(N+1)
    ]

    def cegis_loopy(query):
        E_vars = #?
        e_map = cegis(query, E_vars)
        solved = solver.solve()
        if solved:
            e_rows_v = [
                [
                    Edge(
                        bool(int(solver.get_value(e.en.value).constant_value())),
                        bool(int(solver.get_value(e.dir.value).constant_value())),
                    ) for e in es
                ] for es in e_rows
            ]
            e_cols_v = [
                [
                    Edge(
                        int(solver.get_value(e.en.value).constant_value()),
                        int(solver.get_value(e.dir.value).constant_value()),
                    ) for e in es
                ] for es in e_cols
            ]

    #     0123
#   0 +-+-
#   1 | |
#   2 +-+

    def print_board(erv, ecv):
        b = [list(" "*(2*N+1)) for _ in range(2*N+1)]
        for pi, pj in product(range(2*N+1), repeat=2):
            if (pi%2==0 and pj%2==0):
                #Vertex
                b[pi][pj]="\u253c"

        #Add numbers
        for i, j in product(range(N), repeat=2):
            pi = i*2+1
            pj = j*2+1
            f = faces[i][j]
            if f is not None:
                b[pi][pj] = str(f)

        L = "\u2190"
        U = "\u2191"
        R = "\u2192"
        D = "\u2193"
        # Add Edges
        #Add row edges
        for i in range(N+1):
            pi = 2*i
            for j in range(N):
                e = erv[i][j+1]
                pj = 2*j+1
                c = "\u2500"
                if e.en:
                    c = R if e.dir else L
                b[pi][pj] = c

        # Add col edges
        for i in range(N + 1):
            pj = 2 * i
            for j in range(N):
                e = ecv[i][j + 1]
                pi = 2 * j + 1
                c = "\u2502"
                if e.en:
                    c = U if e.dir else D
                b[pi][pj] = c

        print("\n".join(("".join(b_) for b_ in b)))


    def iter_edges():
        for edgeset in (e_rows, e_cols):
            for edges in edgeset:
                for e in edges:
                    yield e
    def iter_faces():
        for i, j in product(range(N), repeat=2):
            val = faces[i][j]
            eN = e_rows[i][j+1]
            eS = e_rows[i+1][j+1]
            eW = e_cols[j][i+1]
            eE = e_cols[j+1][i+1]
            yield Face(val, [eE, eN, eW, eS])

    def iter_vertices():
        for i, j in product(range(N+1), repeat=2):
            eN = e_cols[j][i]
            eS = e_cols[j][i+1]
            eW = e_rows[i][j]
            eE = e_rows[i][j+1]
            yield Vertex(None, [eE, eN, eW, eS])

    def add_edges(edges):
        return sum([e.en for e in edges], SBV[3](0))

    def solve(f):
        #E(ens, dirs) AND[
        #    f(ens, dirs) & wind(dirs)==4,
        #    A(dirs2) f(ens, dirs2) => (wind(dirs2) == (4,-4))))
        fval = f.to_hwtypes().value.simplify()
        with smt.Solver('z3', logic=BV) as solver:
            solver.add_assertion(fval)
            solved = solver.solve()
            if solved:
                e_rows_v = [
                    [
                        Edge(
                            bool(int(solver.get_value(e.en.value).constant_value())),
                            bool(int(solver.get_value(e.dir.value).constant_value())),
                        ) for e in es
                    ] for es in e_rows
                ]
                e_cols_v = [
                    [
                        Edge(
                            int(solver.get_value(e.en.value).constant_value()),
                            int(solver.get_value(e.dir.value).constant_value()),
                        ) for e in es
                    ] for es in e_cols
                ]
            else:
                raise ValueError("No solution!")
        return e_rows_v, e_cols_v

    #Each edge en must be 0 or 1
    constraint_edge_valid = And([e.en < 2 for e in iter_edges()])

    #boiundary edges are en=0
    cons = []
    for i in range(N+1):
        cons.append(And(
            [es[i][j].en==0 for j, es in product((0, N+1), (e_cols, e_rows))]
        ))
    constraint_boundary = And(cons)

    # Number constraints
    # Each face may or may not have a number. the number represents
    # the total number of used edges around that face
    con = []
    for f in iter_faces():
        if f.val is None:
            continue
        esum = add_edges(f.edges)
        con.append(esum == f.val)
    constraint_numbers = And(con)

    #Connection constraints:
    #Each vertex must have exactly 0 or 2 edges
    con = []
    for v in iter_vertices():
        s = add_edges(v.edges)
        con.append((s==0)|(s==2))
    constraint_conn = And(con)

    # Direction constraints:
    # East and North are 1

    #Each vertex has consistent direction
    con = []
    for v in iter_vertices():
        dirs = [e.dir for e in v.edges]
        #Flips the direction so that 1 means pointing towards center
        for i in (0, 1):
            dirs[i] = ~dirs[i]
        _con = []
        for (i,j) in itertools.combinations(range(4), 2):
            da, db = dirs[i], dirs[j]
            ena, enb = v.edges[i].en, v.edges[j].en
            _con.append(Implies(ena + enb == 2, da ^ db))
        con.append(And(_con))
    constraint_dir = And(con)

    #Single Loop Constraints:
    #The 'winding nubmer' can be computed locally and summed
    # That should equal exaclty 1 full turn (4)
    T = SBV[32]
    winds = []
    wind_dict = {}
    for vi, v in enumerate(iter_vertices()):
        wind_dict[vi] = {}
        dirs = [e.dir for e in v.edges]
        ens = [e.en for e in v.edges]
        # Flips the direction so that 1 means pointing towards center
        for i in (0, 1):
            dirs[i] = ~dirs[i]

        for i in range(4):
            #right wind
            j = (i+1)%4
            en = (ens[i] + ens[j]==2) & dirs[i]
            wind = en.ite(T(1), T(0))
            winds.append(wind)
            wind_dict[vi][(i,j)] = wind
            #left wind
            j = (i+3)%4
            en = (ens[i] + ens[j]==2) & dirs[i]
            wind = en.ite(T(-1), T(0))
            winds.append(wind)
            wind_dict[vi][(i,j)] = wind

    constraint_loop = sum(winds, T(0))==4

    f = And([
        constraint_edge_valid,
        constraint_boundary,
        constraint_numbers,
        constraint_conn,
        constraint_dir,
        constraint_loop
    ])
    es = solve(f)
    print_board(*es)

board1 = '''\
22xx33x
23x2xx2
2x332xx
xx20xx3
xxxx2xx
xx210xx
x12x1x3'''

board2 = '''\
x3x
202
xxx'''

board3 = '''4'''

doit(board1)
