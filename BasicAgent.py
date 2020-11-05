import random
from pprint import pprint
import time

import numpy as np
from Environment import Cell, Environment
from Graphics_grid import GraphicGrid


class NaiveAgent:

    # Agent takes an environment as input to play
    def __init__(self, env):
        self.env = env
        # Grid size
        self.grid_size = env.grid.shape[0]
        # Creating a grid with agent's perspective. All actions will be performed on this
        self.currGrid = [[Cell(j, i) for i in range(self.grid_size)] for j in range(self.grid_size)]
        # Number of mines exploded for a game
        self.mines_exploded = 0
        # Initial variable for graphics
        self.graphics = GraphicGrid([])

    def play(self):
        # Getting a random cell to start with. Here I'm selecting a free cell as initial point to be fair with agent.
        # Can be commented if not needed
        random_cell = self.currGrid[random.randrange(0, len(self.currGrid))][
            random.randrange(0, len(self.currGrid))]
        # Queiying the chosen random cell
        self.env.query_cell(random_cell)
        # if first cell is mine, looping until agent finds a free cell to start with
        while random_cell.is_mine:
            random_cell.is_mine = False
            random_cell.curr_value = None
            random_cell = self.currGrid[random.randrange(0, len(self.currGrid))][
                random.randrange(0, len(self.currGrid))]
            self.env.query_cell(random_cell)
        # Calling to render view
        self.render_basic_view()
        # Play until all cells are finished
        while True:
            if self.look_over_grid() == 'Finished':
                break

        print(self.mines_exploded)

    # Main functions to loop over cells once and check for any inferences
    def look_over_grid(self):
        # Populating all cells with current values
        self.populate_all_cells()
        self.render_basic_view()
        # Looping through all the cells
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                cell = self.currGrid[row][column]
                # self.populate_cell(cell)
                # Working only if current cell is covered
                if (cell.curr_value is not None) and not cell.is_flagged:
                    # If curr value minus neighbouring mines is the covered neighbours, all cells are mines
                    if cell.curr_value - cell.mines_surrounding == cell.covered_neighbours:
                        # Checking for edge cases. If curr value is 0 or covered neighbours is 0, this shouldn't be done
                        if cell.curr_value != 0 and cell.covered_neighbours != 0:
                            self.flag_neighbours(cell)
                            return 'Done'
                    # If the total number of safe neighbors (total neighbours - clue) minus the number of revealed
                    # safe neighbors is the number of hidden neighbors, every hidden neighbor is safe
                    elif (cell.total_neighbours - cell.curr_value) - cell.safe_cells_surr == cell.covered_neighbours:
                        self.mark_neighbours_safe(cell)
                        return 'Done'
        # If nothing is done in looping, open a random cell. if no random cell is present, game is done
        if not self.open_random_cell():
            return 'Finished'
        return 'Done looping'

    # Method to populate all cells
    def populate_all_cells(self):
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                self.populate_cell(self.currGrid[row][column])

    # Check if cell co-ordinates are within range
    def isCellValid(self, row: int, col: int):
        return (row >= 0) and (row < len(self.currGrid)) and (col >= 0) and (col < len(self.currGrid[0]))

    # Populate a single cell
    def populate_cell(self, cell):
        row = cell.row
        col = cell.col
        mines = 0
        covered = 0
        safe = 0
        total_neighbours = 0
        # This loop covers all neighbours including self
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                # Continue if it's the same cell
                if (i == 0 and j == 0) or not self.isCellValid(row + i, col + j):
                    continue
                # Get the neighbour
                neighbour = self.currGrid[row + i][col + j]
                # Incrementing total neighbours
                total_neighbours += 1
                # If it's not opened and not flagged, it's covered
                if neighbour.curr_value is None and not neighbour.is_mine and not neighbour.is_flagged:
                    covered += 1
                # If it's flagged, increment mines count
                elif neighbour.is_flagged:
                    mines += 1
                else:
                    # Increment safe count otherwise
                    safe += 1
        # Populating all found values
        cell.covered_neighbours = covered
        cell.mines_surrounding = mines
        cell.safe_cells_surr = safe
        cell.total_neighbours = total_neighbours

    # Method to mark all neighbours as safe which is just querying them
    def mark_neighbours_safe(self, cell):
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or not self.isCellValid(cell.row + i, cell.col + j):
                    continue
                neighbour = self.currGrid[cell.row + i][cell.col + j]
                # Querying covered neighbours
                if not neighbour.is_flagged and neighbour.curr_value is None:
                    self.env.query_cell(neighbour)
        # Show current state
        self.render_basic_view()

    # Method to flag all neighbours
    def flag_neighbours(self, cell):
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or not self.isCellValid(cell.row + i, cell.col + j):
                    continue
                neighbour = self.currGrid[cell.row + i][cell.col + j]
                # If not opened, flag it
                if neighbour.curr_value is None:
                    neighbour.is_flagged = True
        self.render_basic_view()

    # Check if there are any cree cells in grid
    def have_free_cells(self):
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                cell = self.currGrid[row][column]
                if cell.curr_value is None and not cell.is_flagged:
                    return True
        return False

    # Method to open random cell
    def open_random_cell(self):
        # Return if all cells are opened or flagged
        if not self.have_free_cells():
            return False
        # Initialize a random cell
        random_cell = self.currGrid[random.randrange(0, len(self.currGrid))][
            random.randrange(0, len(self.currGrid))]
        # Random cell should be a covered cell
        while random_cell.is_flagged or (random_cell.curr_value is not None):
            random_cell = self.currGrid[random.randrange(0, len(self.currGrid))][
                random.randrange(0, len(self.currGrid))]
        # Query that random cell
        self.env.query_cell(random_cell)
        # If cell turns out to be a mine flagged by environment, increment dead count
        if random_cell.is_mine:
            self.mines_exploded += 1
            random_cell.is_flagged = True
        # Show current state
        self.render_basic_view()
        return True

    # Method to render view. This was initially called basic. Didn't change it. Shows graphics as well
    def render_basic_view(self):
        # A new grid with all values as N. Will be overwritten as we populate
        numeric_grid = [['N' for x in range(self.grid_size)] for y in range(self.grid_size)]
        # Looping through current grid instance(this has cell objects) and populating numeric grid
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                # Setting value
                numeric_grid[row][column] = self.currGrid[row][column].curr_value
                # Setting value as 'f' if flagged
                if self.currGrid[row][column].is_flagged:
                    numeric_grid[row][column] = 'f'
                # Setting value as 'b' if it's a mine
                if self.currGrid[row][column].is_mine:
                    numeric_grid[row][column] = 'b'
        # Code to initiate pygame graphical view
        if len(self.graphics.grid) == 0:
            # Initiating if this is te first time
            self.graphics.updateGrid(numeric_grid)
            self.graphics.Init_view()
            self.graphics.initVisuals()
        # Updating graphics
        self.graphics.updateGrid(numeric_grid)
        # PPrint is impacting performance a lot
        pprint(numeric_grid)


# Driver code to test
density_store = {}
# Iterating for range of mine density
for d in range(1, 10, 1):
    density = d/10
    Store = {'bombs': [], 'time': []}
    for i in range(50):
        start = time.process_time()
        env = Environment(10, density)
        agent = NaiveAgent(env)
        agent.play()
        Store['bombs'].append(agent.mines_exploded)
        Store['time'].append(time.process_time() - start)

    print('Average number of bombs exploded is ' + str(np.average(Store['bombs'])))
    print('Average time taken ' + str(np.average(Store['time'])))
    density_store[density] = str(np.average(Store['bombs']))
print(density_store)
for key in density_store.keys():
    print(str(key) + ',' + str(density_store[key]))
