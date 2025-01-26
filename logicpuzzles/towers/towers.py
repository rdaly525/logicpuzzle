"""
Towers Puzzle

A logic puzzle where you must place towers of different heights (1 to N) in a NxN grid.
Each number on the outside of the grid indicates how many towers can be seen from that direction.
Taller towers block the view of shorter towers behind them.

The numbers around the grid are:
- Top (T): Number of towers visible looking down each column
- Bottom (B): Number of towers visible looking up each column  
- Left (L): Number of towers visible looking right across each row
- Right (R): Number of towers visible looking left across each row

Rules:
1. Each row and column must contain exactly one tower of each height (1 to N)
2. The number of visible towers from each direction must match the given clues
"""

import random
import typing as tp
from ..board import Board, Face, Vertex, Edge

class TowersBoard(Board):
    class face_t(Face):
        def __init__(self, r: int, c: int, val: tp.Optional[int] = None):
            super().__init__(r, c)
            self.val = val
            self.is_solved = val is not None  # Track if this is part of the initial puzzle
            self.solved_val = val  # Store the initial value if it was part of the puzzle
        
        def __str__(self):
            if self.val is None:
                return "  "
            return str(self.val)

    vertex_t = Vertex
    edge_t = Edge


    # TODO Add an argument for the face values that could be paritally filled in. 
    # Randomize as necessary. 
    def __init__(self, N: int, clues: tp.Optional[tp.Dict[str, tp.List[int]]] = None):
        super().__init__(N, N)
        self.N = N
        if clues is None:
            self._randomize()
            # Store clues but clear the board values
            self.clues = self.clues
            for (r,c), face in self.f.items():
                face.val = None
        else:
            self.clues = clues
            
        # verify clues are in the right format
        for kind in ("T", "B", "L", "R"):
            assert len(self.clues[kind]) == self.N and all(isinstance(c, int) for c in self.clues[kind])

    def _randomize(self):
        # Create default board
        board = [[0] * self.N for _ in range(self.N)]
        for i in range(self.N):
            for j in range(self.N):
                board[i][j] = ((i + j) % self.N) + 1

        # Shuffle rows
        random.shuffle(board)

        # Shuffle columns by transposing, shuffling rows, then transposing back
        board = list(map(list, zip(*board)))  # transpose
        random.shuffle(board)
        board = list(map(list, zip(*board)))  # transpose back

        # Store board state in faces
        for r in range(self.N):
            for c in range(self.N):
                self.f[(r,c)].val = board[r][c]

        # Compute clues by counting visible towers from each direction
        clues = {'T': [], 'B': [], 'L': [], 'R': []}

        # Top clues
        for col in range(self.N):
            visible = 1
            max_height = board[0][col]
            for row in range(1, self.N):
                if board[row][col] > max_height:
                    visible += 1
                    max_height = board[row][col]
            clues['T'].append(visible)

        # Bottom clues
        for col in range(self.N):
            visible = 1
            max_height = board[self.N-1][col]
            for row in range(self.N-2, -1, -1):
                if board[row][col] > max_height:
                    visible += 1
                    max_height = board[row][col]
            clues['B'].append(visible)

        # Left clues
        for row in range(self.N):
            visible = 1
            max_height = board[row][0]
            for col in range(1, self.N):
                if board[row][col] > max_height:
                    visible += 1
                    max_height = board[row][col]
            clues['L'].append(visible)

        # Right clues
        for row in range(self.N):
            visible = 1
            max_height = board[row][self.N-1]
            for col in range(self.N-2, -1, -1):
                if board[row][col] > max_height:
                    visible += 1
                    max_height = board[row][col]
            clues['R'].append(visible)

        self.clues = clues

    def create_face(self, r: int, c: int) -> face_t:
        return self.face_t(r, c)

    def pretty(self, h_len: int = 8, v_len: int = 4) -> str:
        # Calculate left padding needed for left clues
        left_padding = 3  # Width of left clues + space

        # Center 2-digit numbers in grid cells
        center_offset = (h_len - 2) // 2  # Space before number to center it

        # Print top clues with proper left padding
        result = [" " * left_padding + 
                  "".join(f"{' ' * center_offset}{str(x).rjust(2)}{' ' * (h_len - center_offset - 2)}" 
                         for x in self.clues['T'])]
        
        # Get the basic board layout
        board_str = super().pretty(h_len=h_len, v_len=v_len)
        board_lines = board_str.split('\n')
        
        # Add left and right clues
        for i, line in enumerate(board_lines):
            if i % v_len == v_len//2:  # Only add clues to center lines
                row_idx = i // v_len
                if row_idx < self.N:
                    # Add left clue and maintain alignment
                    line = f"{str(self.clues['L'][row_idx]).center(2)} {line} {str(self.clues['R'][row_idx]).rjust(2)}"
                else:
                    line = " " * left_padding + line
            else:
                # Add left padding to non-clue lines
                line = " " * left_padding + line
            board_lines[i] = line
            
        result.extend(board_lines)
        
        # Print bottom clues with proper left padding
        result.append(" " * left_padding + 
                     "".join(f"{' ' * center_offset}{str(x).rjust(2)}{' ' * (h_len - center_offset - 2)}" 
                            for x in self.clues['B']))
        
        return "\n".join(result)