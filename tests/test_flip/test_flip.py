from logicpuzzles.flip.flip import FlipSolver, FlipBoard

#board_init = [
#    [1, 1, 0, 1, 1],
#    [1, 1, 1, 1, 0],
#    [0, 1, 1, 0, 1],
#    [1, 0, 1, 1, 1],
#    [0, 1, 1, 1, 0],
#]
N = 4
board = FlipBoard(N)
num_sat = 0
N_TRIALS = 1000
for i in range(N_TRIALS):    
    board._random_board()
    is_sat = False
    for goal_value in [0, 1]:
        solver = FlipSolver(board, goal_value=goal_value, verbose=False)
        for model in solver.solve():
            #board.pretty_print(model)
            is_sat = True
            break
    if is_sat:
        num_sat += 1
print(f"Number of satisfiable solutions: {num_sat} out of {N_TRIALS}")