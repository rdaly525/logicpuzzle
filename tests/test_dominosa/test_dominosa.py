from logicpuzzles.dominosa.dominosa import DominosaBoard
from logicpuzzles.dominosa.dominosa_solver import DominosaSolver

from timeit import default_timer as dt

def test_dominosa():
    board = [
        [1,0,0,2,3],
        [0,1,3,2,1],
        [3,2,3,1,1],
        [2,2,3,0,0],
    ]

    N = 3  # Maximum number in the board
    b = DominosaBoard(N, board)
    print(b.pretty())
    start = dt()
    solver = DominosaSolver(b)
    print(f"isZ3: {solver.isZ3}")
    print(f"solver_info: {solver.solver_info}")
    for i, sol in enumerate(solver.solve(0)):
        assert sol is not None
        b.verify(sol)
        print(f"sol {i}:\n{b.pretty_print(sol)}")
    print(f"time: {dt()-start}")

if __name__ == "__main__":
    test_dominosa()