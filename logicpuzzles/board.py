# class for a generic board
# values can be placed squares, vertices, and/or edges.
from enum import Enum
import itertools as it
import typing as tp
from dataclasses import dataclass

'''
        v[0,0]          e[h,0,1]        v[0,3]
            +---------+---------+---------+
            |         |         |         |
e[v,0,0]    |  f[0,0] |         |  f[0,2] | e[v,0,3]
            |         |         |         |
            +---------+---------+---------+
            |         |         |         |
e[v,1,0]    |         |         |         | e[v,1,3]
            |         |         |         |
            +---------+---------+---------+
            |         |         |         |
e[v,2,0]    |  f[2,0] |         |  f[2,2] | e[v,2,3]
            |         |         |         |
            +---------+---------+---------+
        v[3,0]          e[h,0,1]        v[3,3]

 
 '''   

class EDir(Enum):
    v=0
    h=1


@dataclass
class Edge:
    dir: EDir
    r: int
    c: int

    def __post_init__(self):
        assert isinstance(self.dir, EDir)
        assert isinstance(self.r, int)
        assert isinstance(self.c, int)

    @property
    def idx(self):
        return (self.dir, self.r, self.c)

    def __str__(self):
        return "-" if self.dir is EDir.h else "|"
    

@dataclass
class Face:
    r: int
    c: int

    def __post_init__(self):
        assert isinstance(self.r, int)
        assert isinstance(self.c, int)

    @property
    def idx(self):
        return (self.r, self.c)

    def __str__(self):
        return " "

@dataclass
class Vertex:
    r: int
    c: int

    def __post_init__(self):
        assert isinstance(self.r, int)
        assert isinstance(self.c, int)

    def __str__(self):
        return "+"


class Board:
    edge_t: tp.Type[Edge] = Edge
    face_t: tp.Type[Face] = Face
    vertex_t: tp.Type[Vertex] = Vertex 

    def create_face(self, r: int, c: int) -> Face:
        return self.face_t(r, c)

    def create_edge(self, dir: EDir, r: int, c: int) -> Edge:
        return self.edge_t(dir, r, c)

    def create_vertex(self, r: int, c: int) -> Vertex:
        return self.vertex_t(r, c)

    def __init__(self, nR: int, nC: int):
        self.nR = nR
        self.nC = nC
        self.e = {} 
        self.f = {} 
        self.v = {} 

        # Vertical edges
        for r, c in it.product(range(nR), range(nC+1)):
            self.e[(EDir.v, r, c)] = self.create_edge(EDir.v, r, c)
        # Horizontal edges
        for r, c in it.product(range(nR+1), range(nC)):
            self.e[(EDir.h, r, c)] = self.create_edge(EDir.h, r, c)
        
        # Faces
        for r, c in it.product(range(nR), range(nC)):
            self.f[(r,c)] = self.create_face(r, c)
         
        # Vertices 
        for r, c in it.product(range(nR+1), range(nC+1)):
            self.v[(r,c)] = self.create_vertex(r, c)

    def pretty(self, h_len: int = 8, v_len: int = 4) -> str:
        """
        Creates a string representation of the board as a grid with vertices, edges, and faces.
        
        The grid is drawn using ASCII characters, with:
        - Vertices at grid intersections (default: '+')
        - Horizontal edges between vertices (default: '-')  
        - Vertical edges between vertices (default: '|')
        - Faces in the grid cells (default: ' ')

        Args:
            h_len: Width of each grid cell in characters (default: 8)
            v_len: Height of each grid cell in characters (default: 4)

        Returns:
            String representation of the board grid
        """
        edge_row = list(("+"+"-"*(h_len-1))*self.nC + "+")
        face_row = list(("|" + " "*(h_len-1)) * self.nC + "|")
        rows = []
        for r in range(self.nR):
            rows.append(list(edge_row))  # Create new list for edge row
            for _ in range(v_len-1):
                rows.append(list(face_row))  # Create new list for each face row
        rows.append(list(edge_row))  # Final edge row

        # Add vertices
        for (r, c), v in self.v.items():
            rows[r*v_len][c*h_len] = str(v)

        # Add edges
        for (dir, r, c), e in self.e.items():
            if dir == EDir.v:
                rows[r*v_len+v_len//2][c*h_len] = str(e)
            else:
                rows[r*v_len][c*h_len + h_len//2] = str(e)

        # Add faces
        for (r, c), f in self.f.items():
            rows[r*v_len+v_len//2][c*h_len + h_len//2] = str(f)

        return "\n".join(["".join(row) for row in rows])

    def boundary_edge(self, edge_idx: tuple[EDir, int, int]) -> tp.Optional[Edge]:
        """Optional override to define behavior for out-of-bounds edges"""
        return None

    def boundary_face(self, face_idx: tuple[int, int]) -> tp.Optional[Face]:
        """Optional override to define behavior for out-of-bounds faces"""
        return None

    def boundary_vertex(self, vertex_idx: tuple[int, int]) -> tp.Optional[Vertex]:
        """Optional override to define behavior for out-of-bounds vertices"""
        return None

    def get_face(self, face_idx: tuple[int, int]) -> tp.Optional[Face]:
        """Gets a face, using boundary_face for out-of-bounds indices"""
        if face_idx in self.f:
            return self.f[face_idx]
        return self.boundary_face(face_idx)

    def get_edge(self, edge_idx: tuple[EDir, int, int]) -> tp.Optional[Edge]:
        """Gets an edge, using boundary_edge for out-of-bounds indices"""
        if edge_idx in self.e:
            return self.e[edge_idx]
        return self.boundary_edge(edge_idx)

    def get_vertex(self, vertex_idx: tuple[int, int]) -> tp.Optional[Vertex]:
        """Gets a vertex, using boundary_vertex for out-of-bounds indices"""
        if vertex_idx in self.v:
            return self.v[vertex_idx]
        return self.boundary_vertex(vertex_idx)

    def face_to_faces(self, face_idx: tuple[int, int]) -> tp.Iterator[Face]:
        """Yields adjacent faces that share an edge with the given face"""
        r, c = face_idx
        adjacents = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        for adj_idx in adjacents:
            if face := self.get_face(adj_idx):
                yield face

    def face_to_edges(self, face_idx: tuple[int, int]) -> tp.Iterator[Edge]:
        """Yields edges that bound the given face"""
        r, c = face_idx
        edge_indices = [
            (EDir.h, r, c),      # top
            (EDir.v, r, c+1),    # right
            (EDir.h, r+1, c),    # bottom
            (EDir.v, r, c)       # left
        ]
        for edge_idx in edge_indices:
            if edge := self.get_edge(edge_idx):
                yield edge

    def face_to_vertices(self, face_idx: tuple[int, int]) -> tp.Iterator[Vertex]:
        """Yields vertices at the corners of the given face"""
        r, c = face_idx
        vertex_indices = [(r, c), (r, c+1), (r+1, c+1), (r+1, c)]
        for vertex_idx in vertex_indices:
            if vertex := self.get_vertex(vertex_idx):
                yield vertex

    def edge_to_faces(self, edge_idx: tuple[EDir, int, int]) -> tp.Iterator[Face]:
        """Yields faces adjacent to the given edge"""
        dir, r, c = edge_idx
        faces = [(r-1, c), (r, c)] if dir == EDir.h else [(r, c-1), (r, c)]
        for face_idx in faces:
            if face := self.get_face(face_idx):
                yield face

    def edge_to_edges(self, edge_idx: tuple[EDir, int, int]) -> tp.Iterator[Edge]:
        """Yields edges that share a vertex with the given edge"""
        dir, r, c = edge_idx
        if dir == EDir.h:
            edge_indices = [
                (EDir.v, r, c),      # left end
                (EDir.v, r, c+1),    # right end
                (EDir.v, r-1, c),    # left end up
                (EDir.v, r-1, c+1)   # right end up
            ]
        else:  # EDir.v
            edge_indices = [
                (EDir.h, r, c),      # top end
                (EDir.h, r+1, c),    # bottom end
                (EDir.h, r, c-1),    # top end left
                (EDir.h, r+1, c-1)   # bottom end left
            ]
        
        for edge_idx in edge_indices:
            if edge := self.get_edge(edge_idx):
                yield edge

    def edge_to_vertices(self, edge_idx: tuple[EDir, int, int]) -> tp.Iterator[Vertex]:
        """Yields vertices at the endpoints of the given edge"""
        dir, r, c = edge_idx
        vertex_indices = [(r, c), (r, c+1)] if dir == EDir.h else [(r, c), (r+1, c)]
        for vertex_idx in vertex_indices:
            if vertex := self.get_vertex(vertex_idx):
                yield vertex

    def vertex_to_faces(self, vertex_idx: tuple[int, int]) -> tp.Iterator[Face]:
        """Yields faces that have this vertex as a corner"""
        r, c = vertex_idx
        face_indices = [(r-1, c-1), (r-1, c), (r, c), (r, c-1)]
        for face_idx in face_indices:
            if face := self.get_face(face_idx):
                yield face

    def vertex_to_edges(self, vertex_idx: tuple[int, int]) -> tp.Iterator[Edge]:
        """Yields edges that have this vertex as an endpoint"""
        r, c = vertex_idx
        edge_indices = [
            (EDir.h, r, c-1),    # left
            (EDir.h, r, c),      # right
            (EDir.v, r-1, c),    # up
            (EDir.v, r, c)       # down
        ]
        for edge_idx in edge_indices:
            if edge := self.get_edge(edge_idx):
                yield edge

    def vertex_to_vertices(self, vertex_idx: tuple[int, int]) -> tp.Iterator[Vertex]:
        """Yields vertices connected by a single edge to this vertex"""
        r, c = vertex_idx
        vertex_indices = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        for vertex_idx in vertex_indices:
            if vertex := self.get_vertex(vertex_idx):
                yield vertex


