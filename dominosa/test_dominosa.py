from dominosa import Board, solve
from timeit import default_timer as dt
rep = 5
maxN = 40

times = {}
for N in range(30, maxN):
    timesN = []
    for _ in range(rep):
        b = Board(N)
        start = dt()
        sol = solve(b)
        tot = dt() - start
        assert sol is not None
        b.verify(sol)
        timesN.append(tot)
    print(f"{N}, {round(1000*sum(timesN)/rep)}")