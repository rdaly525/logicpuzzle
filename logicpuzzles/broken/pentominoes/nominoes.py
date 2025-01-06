def print_pentomino(pentomino_coords, N):
    # Create a 5x5 grid initialized with dots
    grid = [['.' for _ in range(N)] for _ in range(N)]

    # Mark the pentomino squares on the grid
    for x, y in pentomino_coords:
        grid[y][x] = '#'

    # Print the grid
    for row in grid:
        print(' '.join(row))

def generate_polyominoes(n):
    def normalize(polyomino):
        min_x = min(x for x, y in polyomino)
        min_y = min(y for x, y in polyomino)
        return tuple(sorted((x - min_x, y - min_y) for x, y in polyomino))

    def rotate(polyomino):
        return [(-y, x) for x, y in polyomino]

    def reflect(polyomino):
        return [(-x, y) for x, y in polyomino]

    def canonical(polyomino):
        transformations = [polyomino]
        for _ in range(3):
            transformations.append(rotate(transformations[-1]))
        transformations += [reflect(shape) for shape in transformations]
        return min(normalize(shape) for shape in transformations)

    def add_block(polyomino):
        last_x, last_y = polyomino[-1]
        potential_new_blocks = [(last_x + 1, last_y), (last_x - 1, last_y),
                                (last_x, last_y + 1), (last_x, last_y - 1)]
        new_shapes = []
        for block in potential_new_blocks:
            if block not in polyomino:
                new_shape = polyomino + [block]
                new_shapes.append(new_shape)
        return new_shapes

    shapes = {canonical([(0, 0)])}
    for _ in range(n - 1):
        new_shapes = set()
        for shape in shapes:
            new_shapes.update(canonical(shape) for shape in add_block(list(shape)))
        shapes = new_shapes

    return [list(shape) for shape in shapes]

# Example usage
for shape in generate_polyominoes(4):
    print(shape)


# Example usage
N = 5
for shape in generate_polyominoes(N):
    print_pentomino(shape, N)
    print()
