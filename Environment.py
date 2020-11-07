import numpy as np
import random
from pprint import pprint


# Class for Cell object in grid
class Cell:
    def __init__(self, row, col):
        # Row: Row number of cell in grid
        self.row = row
        # Col: Column number of cell in grid
        self.col = col
        # ismine: Flagged by Environment if mine is opened
        self.is_mine = False
        # isflagged: Flagged by Agent if mine is identified
        self.is_flagged = False
        # currvalue:  Current  value  determined  after  opening  a safe cell
        self.curr_value = None
        # minessurrounding: Number of mines(including flagged ones) surrounding the Cell
        self.mines_surrounding = None
        # safecellssurr:  Number  of  Safe  Cells  surrounding  theCell
        self.safe_cells_surr = None
        # coveredneighbours:  Number  of  neighbours  yet  to  be opened
        self.covered_neighbours = None
        # totalneighbours: Total number of neighbours available for a Cell. Useful for cells in edges of grid
        self.total_neighbours = None
        self.probability = None

    # def __eq__(self, o: object) -> bool:
    #     if isinstance(o, Cell):
    #         return (self.row == o.row) and (self.col == o.col)
    #     return False


class Environment:
    def __init__(self, dimension, density):
        # Initializing with empty grid
        self.grid = None
        # Dimension of grid specified
        self.n = dimension
        # Number of mines
        self.m = int(dimension * dimension * density)
        # Calling create grid
        self.create_grid()
        # Not being used
        self.opened = np.zeros((self.n, self.n), dtype=bool)

    # Method to add required number of mines
    def add_mines(self):
        count = 0
        # While number of mines is less than required, adding mines
        while count < self.m:
            # Choosing a random cell
            l = (random.randrange(0, self.n), random.randrange(0, self.n))
            # If not already chosen, adding as a mine
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
        # All possible neighbours
        adj = [(i - 1, j - 1), (i - 1, j), (i - 1, j + 1), (i, j - 1), (i, j + 1), (i + 1, j - 1), (i + 1, j),
               (i + 1, j + 1)]
        # Checking if mine and increasing count
        for a in adj:
            if self.isValid(a):
                if self.grid[a] == -1:
                    c += 1
        return c

    # Adding values to each cell in the grid
    def add_values(self):
        # looping for all cells and updating count if it's not a mine
        for i in range(self.n):
            for j in range(self.n):
                if self.grid[(i, j)] != -1:
                    val = self.find_value((i, j))
                    self.grid[(i, j)] = val

    # Create a n*n grid with m mines
    def create_grid(self):
        # Initializing with all zeroes
        self.grid = np.zeros((self.n, self.n))
        # Adding mines and values
        self.add_mines()
        self.add_values()

    # This will be called by agent
    def query_cell(self, query_cell):
        # If invalid cell is queried, return. Won't happen
        if not self.isCellValid(query_cell.row, query_cell.col):
            return
        # Setting curr value to cell
        query_cell.curr_value = self.grid[query_cell.row][query_cell.col]
        # If queried cell is mine, flagging as mine
        if self.grid[query_cell.row][query_cell.col] == -1:
            query_cell.is_mine = True
            query_cell.curr_value = None

    def isCellValid(self, row: int, col: int):
        return (row >= 0) and (row < len(self.grid)) and (col >= 0) and (col < len(self.grid[0]))

# n = 10  # size of grid
# m = 30  # number of mines
# for i in range(20):
#     sample = Environment(10, 0.3)
#     cell = Cell(9, 9)
#     valid = sample.isCellValid(cell.row, cell.col)
#     print(valid)
