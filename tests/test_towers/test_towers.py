from logicpuzzles.towers import Towers, TowersSolver

T = Towers(N=12)
print(T.pretty_print())

solver = TowersSolver(T)
for board in solver.solve():
    print(T.pretty_print(board))
