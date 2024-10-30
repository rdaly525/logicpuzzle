


from collections import namedtuple

Edge = namedtuple("Edge", ["v0", "v1"])
Vertex = namedtuple("Vertex", ["r", "c"])
Face = namedtuple("Face", ["r", "c"])

#This represents a board with faces, vertices, and edges.
class Board:
    def __init__(self, nR: int, nC: int):
        self.nR = nR
        self.nC = nC
        assert nR > 0
        assert nC > 0

    def enum_vertices(self):
        for r in range(self.nR):
            for c in range(self.nC):
                yield Vertex(r, c)

    def enum_edges(self):
        for r in range(self.nR):
            for c in range(self.nC):
                if r > 0:
                    yield (r, c), (r-1, c)
                if c > 0:
                    yield (r, c), (r, c-1)
