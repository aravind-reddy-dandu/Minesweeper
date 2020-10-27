import numpy as np
import random


# Add m mines to the grid
class Environment:
    def __init__(self, dimension, density):
        self.grid = None
        self.n = dimension
        self.m = int(dimension * dimension * density)
        self.create_grid()
        self.opened = np.zeros((self.n, self.n), dtype=bool)

    def add_mines(self):
        l = [(random.randrange(0, self.n - 1), random.randrange(0, self.n - 1)) for i in range(self.m)]
        for i in l:
            self.grid[i] = -1

    # find if the adjacent cell is within dimensions
    def isValid(self, adj):
        # Check if the adjacent value exixts in the grid.
        if adj[0] == -1 or adj[1] == -1 or adj[0] == self.n or adj[1] == self.n:
            return False
        else:
            return True

    # Find no.of mines surrounding each cell.

    def find_value(self, val):
        c = 0
        i = val[0]
        j = val[1]
        adj = [(i - 1, j - 1), (i - 1, j), (i - 1, j + 1), (i, j - 1), (i, j + 1), (i + 1, j - 1), (i + 1, j),
               (i + 1, j + 1)]
        for a in adj:
            if self.isValid(a):
                if self.grid[a] == -1:
                    c += 1
        return c

    # Adding values to each cell in the grid

    def add_values(self):
        for i in range(self.n):
            for j in range(self.n):
                if self.grid[(i, j)] != -1:
                    val = self.find_value((i, j))
                    self.grid[(i, j)] = val

    # Create a n*n grid with m mines

    def create_grid(self):
        self.grid = np.zeros((self.n, self.n))
        self.add_mines()
        self.add_values()


# n = 10  # size of grid
# m = 30  # number of mines
# for i in range(20):
#     sample = Environment(10, 0.3)
#     print(sample.grid)
