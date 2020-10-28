import numpy


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.is_flagged = False
        self.curr_value = None
        self.mines_surrounding = None
        self.safe_cells_surr = None
        self.covered_neighbours = None


class CSPAgent:

    def __init__(self, env):
        self.env = env
        self.grid_size = env.grid.shape[0]
        self.currGrid = [[Cell(i, j) for i in range(self.grid_size)] for j in range(self.grid_size)]

    def play(self):
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                cell = self.currGrid[row][column]
                if (cell.curr_value is not None) and not cell.is_flagged:
                    pass

    def populate_cell(self, cell):
        row = cell.row
        col = cell.col
        mines = 0
        covered = 0
        safe = 0
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if i == 0 and j == 0:
                    # To do logic
                    continue
