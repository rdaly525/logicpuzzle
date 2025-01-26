"""
Unruly is a puzzle game created by Simon Tatham. The goal is to fill a grid with black (1) and white (0) squares 
following these rules:

1. No three consecutive squares in a row or column can be the same color
2. Each row and column must contain an equal number of black and white squares

The puzzle starts with some squares already filled in, and the player must complete the rest of the grid while
following all the rules.
"""

import random
from ..board import Board, Face, Vertex, Edge
from dataclasses import dataclass

# An unruly board is a grid of black, white, and empty squares
# black is 0, white is 1, empty is 2
class UnrulyBoard(Board):
    @dataclass
    class face_t(Face):
        val: int = None
        def __str__(self):
            if self.val is None:
                return " "
            return str(self.val)

    vertex_t = Vertex
    edge_t = Edge

    def __init__(self, N, faces=None, percent_filled=0.2):
        super().__init__(N, N)
        self.N = N
        if faces is None:
            faces = self._random_board(percent_filled)
        assert len(faces) == self.nR
        assert all(len(row) == self.nC for row in faces)
         
        for (r, c), face in self.f.items():
            if faces[r][c] != 2:
                face.val = faces[r][c]

    def _random_board(self, percent_filled=0.2):
        # Calculate number of squares to fill
        total_squares = self.nR * self.nC
        num_filled = int(total_squares * percent_filled)
        
        # Create list of all positions
        positions = [(r,c) for r in range(self.nR) for c in range(self.nC)]
        
        # Randomly select positions to fill
        fill_positions = random.sample(positions, num_filled)
        
        # Initialize board and fill selected positions
        faces = [[2 for _ in range(self.nC)] for _ in range(self.nR)]
        for r,c in fill_positions:
            faces[r][c] = random.randint(0,1)
        return faces