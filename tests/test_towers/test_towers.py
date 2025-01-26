from logicpuzzles.towers.towers import TowersBoard
from logicpuzzles.towers.towers_solver import TowersSolver

# Create a random puzzle of size 12
board = TowersBoard(N=5)
print("Initial puzzle:")
print(board.pretty())

# Solve the puzzle
solver = TowersSolver(board)
print("\nSolution:")
for solution in solver.solve():
    print(solution.pretty())
    break  # Just show first solution
