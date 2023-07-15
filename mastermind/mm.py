import hwtypes as ht
from hwtypes.smt_utils import And, Or
import pysmt.shortcuts as smt
from pysmt.logics import BV


def process_guess(guess, ans):
    for vals in (guess, ans):
        assert isinstance(vals, list)
        assert all(isinstance(v, int) and v >=0 for v in vals)
    used = [g==a for g,a in zip(guess, ans)]
    num_black = sum(used)
    num_white = 0
    for gi, g in enumerate(guess):
        for ai, a in enumerate(ans):
            if not used[ai] and a==g:
                num_white += 1
                used[ai] = True
                break
    return num_black, num_white


def process_guess2(guess, ans):
    N = len(guess)
    #key[ai][gi]
    key = [[g==a for g in guess] for a in ans]
    num_black = sum(key[i][i] for i in range(N))
    #used[ai] means ai is used
    used = [key[ai][ai] for ai in range(N)]

    #white[gi] means gi is white
    white = [False for ai in ans]
    for gi in range(N):
        for ai in range(N):
            is_white = (not white[gi]) and (not used[ai]) and key[ai][gi]
            white[gi] = white[gi] or is_white
            used[ai] = used[ai] or is_white
    num_white = sum(white)
    return num_black, num_white

def check(guess, ans, nb, nw):
    gold = process_guess(guess, ans)
    if (nb, nw) != gold:
        print(f"G1, {guess}, {ans}: {gold} != {nb}, {nw}")
        raise ValueError()
    gold2 = process_guess2(guess, ans)
    if (nb, nw) != gold2:
        print(f"G2, {guess}, {ans}: {gold2} != {nb}, {nw}")
        raise ValueError()


check([1,2,1], [2,1,2], 0, 2)
check([1,1,3], [1,2,2], 1, 0)
check([1,1,2], [1,3,1], 1, 1)
check([1,2,3], [3,1,2], 0, 3)
check([1,2,3], [4,5,6], 0, 0)
check([1,2,3], [1,2,3], 3, 0)


def solve(guess, f):
    fval = f.value.simplify()
    size = smt.get_formula_size(fval)
    with smt.Solver('z3', logic=BV) as solver:
        solver.add_assertion(f.value)
        solved = solver.solve()
        if solved:
            return [int(solver.get_value(v.value).constant_value()) for v in guess]
        else:
            assert 0

def solver(num_slots, num_colors, max_guess, ans):
    SType = ht.SMTBitVector[num_colors]
    assert isinstance(ans, list)
    assert len(ans)==num_slots
    assert all(isinstance(v, int) and 0 <= v < num_colors for v in ans)
    guess_var = [SType(name=f"P{i}") for i in range(num_slots)]
    f = And([(g >=0) & (g < num_colors) for g in guess_var]).to_hwtypes()
    print("Answer Key", ans)
    for k in range(max_guess):
        guess_int = solve(guess_var, f)
        assert all(isinstance(v, int) for v in guess_int)
        nb, nw = process_guess(guess_int, ans)
        print(f"Guess: {guess_int}, (Black, White): {nb}, {nw}", flush=True)
        if (nb, nw) == (num_slots, 0):
            print("Solved!")
            return k+1

        N = num_slots
        #key[ai][gi]
        key = [[g == a for g in guess_int] for a in guess_var]

        # used[ai]
        used = [key[ai][ai] for ai in range(N)]
        same = list(used)
        nb_v = sum(used, SType(0))

        # white[gi]
        white = [ht.SMTBit(0) for _ in range(N)]
        for gi in range(N):
            for ai in range(N):
                is_white = And([~white[gi], ~used[ai], key[ai][gi]]).to_hwtypes()
                white[gi] = white[gi] | is_white
                used[ai] = used[ai] | is_white
        nw_v = sum(white, SType(0))

        f &= (nb_v == nb)
        f &= (nw_v == nw)
        f &= ~(And(same).to_hwtypes())
    return None


import numpy as np
for n in range(5, 6):
    print("-"*80)
    print("Solving ", n)
    ans = np.random.randint(0, n, (n,)).tolist()
    solved = solver(num_slots=n, num_colors=n, max_guess=100, ans=ans)
    print(solved)
