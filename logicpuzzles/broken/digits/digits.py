import functools
from functools import lru_cache
import itertools as it


def solve(digits, goal, ops='asmd'):

    def eval(op, l,r):
        if op=='+':
            ret = l + r
        elif op=='*':
            ret = l * r
        elif op=='-':
            ret = l - r
            if ret <0:
                ret = None
        elif op=='/':
            if r==0:
                ret = None
            else:
                ret = l//r
                if ret*r != l:
                    ret = None
        else:
            raise ValueError
        return ret

    sols = set()
    def do_add(s, x):
        l = len(s)
        s.add(x)
        return len(s) != l

    def check_sol(v, p):
        if v == goal:
            sols.add(p)

    all_sols = {}
    def filt(f):
        @functools.wraps(f)
        def wrap(digits):
            for v, p in f(digits):
                check_sol(v, p)
                if v not in all_sols:
                    all_sols[v] = {p}
                else:
                    all_sols[v].add(p)
                yield v, p
        return wrap

    @filt
    def recurse(digits):
        N = len(digits)
        if N == 1:
            v = digits[0]
            p = str(digits[0])
            yield v, p
            return
        for i in range(1, N):
            for lhs in it.combinations(digits, i):
                rhs = tuple(set(digits) - set(lhs))
                rhs_sols = recurse(rhs)
                lhs_sols = recurse(lhs)
                for (lval, lp), (rval, rp) in it.product(lhs_sols, rhs_sols):
                    for op in ops:
                        val = eval(op, lval, rval)
                        if val is None:
                            continue
                        assert isinstance(val, int) and val >= 0
                        p = f"({lp}{op}{rp})"
                        yield val, p
    [None for _ in recurse(digits)]
    sols = sorted(sols, key= lambda v: len(v), reverse=True)
    return sols, all_sols