import logicpuzzles.dominosa as D

from timeit import default_timer as dt
rep = 5
maxN = 20


board = [
    [1,0,0,2,3],
    [0,1,3,2,1],
    [3,2,3,1,1],
    [2,2,3,0,0],
]

N = 10
b = D.Board(N)
print(b)
start = dt()
solver = D.DominosaSolver(b)
print(f"isZ3: {solver.isZ3}")
print(f"solver_info: {solver.solver_info}")
for i, sol in enumerate(solver.solve(0)):
    assert sol is not None
    b.verify(sol)
    print(f"sol {i}:\n{b.pretty_print(sol)}")
print(f"time: {dt()-start}")