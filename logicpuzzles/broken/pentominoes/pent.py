import itertools as it
import hwtypes as ht
from hwtypes import smt_utils as fc
import pysmt.shortcuts as smt


def print_pentomino(pentomino_coords):
    # Create a 5x5 grid initialized with dots
    grid = [['.' for _ in range(5)] for _ in range(5)]

    # Mark the pentomino squares on the grid
    for x, y in pentomino_coords:
        grid[y][x] = '#'

    # Print the grid
    for row in grid:
        print(' '.join(row))

class Pentomino:
    def __init__(self, name, coords):
        self.name = name
        self.coords = coords

    def rotate(self):
        """ Rotate the pentomino 90 degrees clockwise """
        self.coords = [(y, -x) for x, y in self.coords]

    def flip_horizontal(self):
        """ Flip the pentomino horizontally """
        max_x = max(x for x, y in self.coords)
        self.coords = [(max_x - x, y) for x, y in self.coords]

    def normalize(self):
        """ Normalize the coordinates to start from (0,0) """
        min_x = min(x for x, y in self.coords)
        min_y = min(y for x, y in self.coords)
        self.coords = [(x - min_x, y - min_y) for x, y in self.coords]

    def get_all_rotations_and_flips(self):
        """ Generate all unique rotations and flips of the pentomino """
        configurations = set()

        for flip in [self.flip_horizontal, lambda: None]:
            for _ in range(4):
                self.normalize()
                config = tuple(sorted(self.coords))
                if config not in configurations:
                    configurations.add(config)
                self.rotate()
            flip()

        return [Pentomino(self.name, list(config)) for config in configurations]

    def get_coords(self, offset_r=0, offset_c=0):
        """ Return the coordinates of the pentomino with the given offsets """
        return [(r + offset_r, c + offset_c) for r, c in self.coords]


# Define each pentomino with its coordinates
pentominoes = [
    Pentomino("F", [(0, 0), (1, 0), (1, 1), (2, 1), (1, -1)]),
    Pentomino("I", [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]),
    Pentomino("L", [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3)]),
    Pentomino("P", [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)]),
    Pentomino("N", [(0, 0), (0, 1), (1, 1), (1, 2), (1, 3)]),
    Pentomino("T", [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)]),
    Pentomino("U", [(0, 0), (2, 0), (0, 1), (1, 1), (2, 1)]),
    Pentomino("V", [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]),
    Pentomino("W", [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]),
    Pentomino("X", [(0, 0), (1, 0), (1, -1), (2, 0), (1, 1)]),
    Pentomino("Y", [(0, 0), (1, 0), (2, 0), (3, 0), (1, 1)]),
    Pentomino("Z", [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)]),
]

tot = 0
for pentomino in pentominoes:
    print(pentomino.name, len(pentomino.get_all_rotations_and_flips()))
    tot += len(pentomino.get_all_rotations_and_flips())
    #for config in pentomino.get_all_rotations_and_flips():
    #    print_pentomino(config.coords)
    #    print()
    #print('*'*10)
print(tot)

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

def solve(nR, nC):

    bvlen = 6
    #For each pentomino I want to solve for a location (row, column) and flavor. The flavor is just the unique flips/rotations.
    loc_vars = {p.name: (new_var(f"{p.name}_r", bvlen), new_var(f"{p.name}_c", bvlen)) for p in pentominoes}
    flavor_vars = {p.name: new_var(f"{p.name}_f", bvlen) for p in pentominoes}
    #domain of board_vars is pentomino indices
    board_vars = {(r, c): new_var(f"board_{r}_{c}", bvlen) for r, c in it.product(range(nR), range(nC))}

    #Constraint location vars
    loc_cons = []
    for rv, cv in loc_vars.values():
        loc_cons.append(rv < nR)
        loc_cons.append(cv < nC)

    #Constraint flavor vars
    flavor_cons = []
    for p in pentominoes:
        nF = len(p.get_all_rotations_and_flips())
        flavor_cons.append(flavor_vars[p.name] < nF)

    board_cons = []
    for r, c in it.product(range(nR), range(nC)):
        board_cons.append(board_vars[(r, c)] < len(pentominoes))

    pent_cons = []
    for pi, p in enumerate(pentominoes):
        p_cons = []
        name = p.name
        for fi, p_ in enumerate(p.get_all_rotations_and_flips()):
            print(f"\n{name}: {fi}")
            print_pentomino(p_.get_coords())
            f_cons = []
            for ro, co in it.product(range(nR), range(nC)):
                pred = (flavor_vars[name] == fi) & (loc_vars[name][0] == ro) & (loc_vars[name][1] == co)
                if not all(0 <= r < nR and 0 <= c < nC for r, c in p_.get_coords(ro, co)):
                    #print('skipping', name, ro, co)
                    #print(p_.get_coords(ro, co))
                    f_cons.append(~pred)
                    continue
                rc_cons = []
                for r, c in p_.get_coords(ro, co):
                    rc_cons.append(board_vars[(r, c)] == pi)
                f_cons.append(fc.Implies(pred, fc.And(rc_cons)))
            p_cons.append(fc.And(f_cons))
        pent_cons.append(fc.And(p_cons))

    f = fc.And([
        fc.And(loc_cons),
        fc.And(flavor_cons),
        fc.And(board_cons),
        fc.And(pent_cons),
    ])
    #print(f.serialize())
    f = f.to_hwtypes().value
    m = get_model(f)
    assert m is not False

    def print_board():
        for r in range(nR):
            for c in range(nC):
                v = m[board_vars[(r, c)].value]
                n = pentominoes[v].name if v < len(pentominoes) else '.'
                print(n, end='')
            print()
    print_board()

if __name__ == "__main__":
    nR, nC = 3, 20
    solve(nR, nC)
