def is_valid(board, x, y, dx, dy, n):
    if 0 <= x < len(board) and 0 <= y < len(board[0]) and 0 <= x + dx < len(board) and 0 <= y + dy < len(board[0]):
        return board[x][y] == n[0] and board[x + dx][y + dy] == n[1] and (x, y) not in used and (x + dx, y + dy) not in used
    return False

def solve_dominosa(board, dominos, index=0):
    if index == len(dominos):
        return True  # All dominos are placed

    domino = dominos[index]
    for i in range(len(board)):
        for j in range(len(board[i])):
            # Try to place horizontally
            if is_valid(board, i, j, 0, 1, domino):
                used.add((i, j))
                used.add((i, j + 1))
                if solve_dominosa(board, dominos, index + 1):
                    return True
                used.remove((i, j))
                used.remove((i, j + 1))

            # Try to place vertically
            if is_valid(board, i, j, 1, 0, domino):
                used.add((i, j))
                used.add((i + 1, j))
                if solve_dominosa(board, dominos, index + 1):
                    return True
                used.remove((i, j))
                used.remove((i + 1, j))

    return False

def generate_dominos(N):
    dominos = []
    for i in range(N + 1):
        for j in range(i, N + 1):
            dominos.append((i, j))
    return dominos

# Define the board
board = [
    [2, 2, 1, 3, 0],
    [1, 0, 2, 3, 1],
    [3, 0, 3, 0, 2],
    [3, 2, 0, 1, 1]
]

board = [
    [0, 1, 2],
    [1, 2, 0],
    [2, 0, 1],
]

# Generate dominos for N = 3
dominos = generate_dominos(3)

# Set to keep track of used cells
used = set()

if solve_dominosa(board, dominos):
    print("Solution found")
    for (i, j) in used:
        print(f"Domino at: ({i}, {j})")
else:
    print("No solution found")
