from digits import solve
import plotly as pl
vals = [1, 2, 3, 4, 5, 6]
goal = 30

#d = []
#for goal in range(0,10):
#    d.append(sum([1 for _ in solve(vals, goal, ops='+-*/')]))
#    print(goal, d[-1])

sols, all_sols = solve(vals, goal, ops='+-*/')
for sol in sols:
    print(sol)
print(all_sols[max(all_sols)])