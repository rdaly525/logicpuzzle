from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV



N = 9
free_vars = [ SBV[10](name=f"v{i}") for i in range(N)]

s = SBV[10](0)
f = SMTBit(1)
for v in free_vars:
    s += (SBV[10](1)<<(v-1))
    f &= (v >0) & (v <= N)
f &= (s==2**N -1)





#for i in range(N-1):
#    f &= free_vars[i] <= free_vars[i+1]
print(f.value.serialize())
with smt.Solver('z3', logic=BV) as solver:
    solver.add_assertion(f.value)
    solved = solver.solve()
    assert solved
    print("Solved")
    print([solver.get_value(v.value).constant_value() for v in free_vars])
    #for r in range(n):
    #    rvals = []
    #    for c in range(n):
    #        var = free_vars[r][c]
    #        smt_var = solver.get_value(var.value)
    #        cval = smt_var.constant_value() 
    #        rvals.append(str(int(cval)))
    #    print(" ".join(rvals))

