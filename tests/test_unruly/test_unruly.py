import pytest
from logicpuzzles.unruly.unruly import UnrulyBoard, UnrulySolver

def test_basic_unruly_solve():
    # Test board with a known solution
    board = [
        [1, 2, 2, 2, 2, 2, 1, 2],
        [2, 2, 2, 2, 2, 1, 2, 2],
        [2, 2, 2, 2, 2, 2, 2, 1],
        [2, 2, 2, 2, 1, 2, 2, 2],
        [2, 2, 2, 2, 2, 2, 1, 1],
        [2, 2, 1, 2, 2, 2, 2, 2],
        [2, 2, 2, 2, 1, 2, 2, 2],
        [2, 1, 1, 2, 2, 2, 2, 2],
    ]
    
    unruly_board = UnrulyBoard(8, board)
    solver = UnrulySolver(unruly_board)
    
    # Get first solution
    solution = next(solver.solve())
    unruly_board.pretty_print(solution)
    # Verify solution meets all constraints
    N = unruly_board.N
    
    # Test rule 1: No three consecutive same color
    def check_consecutive(arr):
        for i in range(len(arr) - 2):
            assert not (arr[i] == arr[i+1] == arr[i+2] == 1)
            assert not (arr[i] == arr[i+1] == arr[i+2] == 0)
    
    # Check rows and columns for three consecutive
    for row in solution:
        check_consecutive(row)
    
    for col in zip(*solution):
        check_consecutive(col)
    
    # Test rule 2: Equal number of black and white
    for row in solution:
        assert sum(row) == N//2
    
    for col in zip(*solution):
        assert sum(col) == N//2


def test_initial_constraints():
    # Test that solution respects initial filled squares
    initial_board = [
        [1, 0, 2, 2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2, 2, 2, 2],
    ]
    
    unruly_board = UnrulyBoard(8, initial_board)
    solver = UnrulySolver(unruly_board)
    solution = next(solver.solve())
    
    # Check that initial constraints are preserved
    assert solution[0][0] == 1  # white
    assert solution[0][1] == 0  # black

#test_basic_unruly_solve()
#test_initial_constraints()

def test_random_unruly_solve():
    N_TRIALS = 100
    histogram = {}
    for percent_filled in [0.05*i for i in range(10)]:
        sat_cnt = 0
        for i in range(N_TRIALS):
            #print(f"Trial {i+1} of {N_TRIALS}")
            unruly_board = UnrulyBoard(8, percent_filled=percent_filled)
            solver = UnrulySolver(unruly_board)
            for solution in solver.solve():
                sat_cnt += 1
                break
        histogram[percent_filled] = sat_cnt
    print(histogram)

test_random_unruly_solve()