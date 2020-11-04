import numpy as np
import random
from pprint import pprint


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.is_mine = False
        self.is_flagged = False
        self.curr_value = None
        self.mines_surrounding = None
        self.safe_cells_surr = None
        self.covered_neighbours = None
        self.total_neighbours = None


# Add m mines to the grid
class Environment:
    def __init__(self, dimension, density):
        self.grid = None
        self.n = dimension
        self.m = int(dimension * dimension * density)
        self.create_grid()
        self.opened = np.zeros((self.n, self.n), dtype=bool)

    def add_mines(self):
        count = 0
        while count < self.m:
            l = (random.randrange(0, self.n), random.randrange(0, self.n))
            if self.grid[l] != -1:
                self.grid[l] = -1
                count += 1

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

    def query_cell(self, query_cell):
        if not self.isCellValid(query_cell.row, query_cell.col):
            return
        query_cell.curr_value = self.grid[query_cell.row][query_cell.col]
        if self.grid[query_cell.row][query_cell.col] == -1:
            query_cell.is_mine = True

    def isCellValid(self, row: int, col: int):
        return (row >= 0) and (row < len(self.grid)) and (col >= 0) and (col < len(self.grid[0]))


# n = 10  # size of grid
# m = 30  # number of mines
# for i in range(20):
#     sample = Environment(10, 0.3)
#     cell = Cell(9, 9)
#     valid = sample.isCellValid(cell.row, cell.col)
#     print(valid)
sample = Environment(10, 1)
pprint(sample.grid)
