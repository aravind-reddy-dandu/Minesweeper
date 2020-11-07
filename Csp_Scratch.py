
import copy
import random
import sys
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
                self.populate_cell(cell)
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
        # build knowledge base and solve it
        knowledge = self.build_knowledge_base()
        flag = self.solve_knowledge(knowledge)
        while flag:
            knowledge = self.build_knowledge_base()
            flag = self.solve_knowledge(knowledge)
        if not self.open_random_cell():
            return 'Finished'
        return 'Done looping'

    def build_knowledge_base(self):
        knowledge = []
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                cell = self.currGrid[row][column]
                if (cell.curr_value is not None) and not cell.is_flagged and not cell.is_mine:
                    row = cell.row
                    col = cell.col
                    condition = []
                    constraint_value = cell.curr_value
                    for i in [-1, 0, 1]:
                        for j in [-1, 0, 1]:
                            if (i == 0 and j == 0) or not self.isCellValid(row + i, col + j):
                                continue
                            cell1 = self.currGrid[row + i][col + j]
                            self.populate_cell(cell1)
                            if cell1.curr_value is None and not cell1.is_flagged and not cell.is_mine:
                                condition.append(cell1)
                            elif cell1.is_flagged or cell1.is_mine:
                                constraint_value -= 1
                    if len(condition) > 0:
                        knowledge.append([condition, constraint_value])
        knowledge = self.remove_dups(knowledge)
        return knowledge

    def substitute_val_in_kb(self, change_cell, kb):
        for equation in kb:
            cells_part = equation[0]
            for cell in cells_part:
                if change_cell.row == cell.row and change_cell.col == cell.col:
                    if change_cell.curr_value is not None and not change_cell.is_flagged and not change_cell.is_mine:
                        cells_part.remove(cell)
                    elif change_cell.is_flagged or change_cell.is_mine:
                        cells_part.remove(cell)
                        equation[1] = equation[1] - 1

    def is_kb_solvable(self, kb):
        for index, equation in enumerate(kb):
            cells_part = equation[0]
            if len(cells_part) == equation[1]:
                return True
            if len(cells_part) == 1:
                return True
        return False

    def solve_dup_kb(self, kb):
        while self.is_kb_solvable(kb):
            for index, equation in enumerate(kb):
                cells_part = equation[0]
                if equation[1] < 0 or len(cells_part) < equation[1]:
                    return False
                if len(cells_part) == equation[1]:
                    # flag all cells
                    for cell in cells_part:
                        cell.is_flagged = True
                if len(cells_part) == 1:
                    if equation[1] == 0:
                        cells_part[0].curr_value = 0
                    elif equation[1] == 1:
                        cells_part[0].is_flagged = True
            self.substitute_values(kb)
        return True

    def substitute_values(self, kb):
        for index, equation in enumerate(kb):
            cells_part = equation[0]
            for cell in cells_part:
                if cell.curr_value is not None and not cell.is_flagged and not cell.is_mine:
                    cells_part.remove(cell)
                elif cell.is_flagged or cell.is_mine:
                    cells_part.remove(cell)
                    equation[1] = equation[1] - 1
            if len(cells_part) == 0:
                kb.remove(equation)

    def check_for_valid_sols(self, kb):
        for index, equation in enumerate(kb):
            cells_part = equation[0]
            if len(cells_part) == 0:
                kb.remove(equation)
                continue
            if len(cells_part) == 1:
                if equation[1] == 0:
                    if cells_part[0].curr_value is not None:
                        self.env.query_cell(cells_part[0])
                elif equation[1] == 1:
                    cells_part[0].is_flagged = True
                kb.remove(equation)
            elif len(cells_part) == equation[1] and not equation[1] < 0:
                for cell in cells_part:
                    cell.is_flagged = True
                kb.remove(equation)
        self.substitute_values(kb)

    def solve_knowledge(self, knowledge):
        # Try to solve knowledge base. If you can, flag cells, open cells and do stuff
        unique_variables = {}
        for condition in knowledge:
            for variable in condition[0]:
                if variable not in unique_variables.keys():
                    unique_variables[variable] = 1
                else:
                    unique_variables[variable] += 1
        interesting_vars = []
        for key in unique_variables.keys():
            if unique_variables[key] > 1:
                interesting_vars.append(key)
        flag = False
        for var in interesting_vars:
            fake_vals = [0, 1]
            if var.is_flagged:
                continue
            for fake_val in fake_vals:
                if var.is_flagged:
                    continue
                dup_kb = copy.deepcopy(knowledge)
                prev_val = var.curr_value
                if fake_val == 0:
                    var.curr_value = fake_val
                else:
                    var.is_flagged = True
                self.substitute_val_in_kb(var, dup_kb)
                # Check if Kb is breaking
                var.curr_value = prev_val
                if fake_val == 1 and var.is_flagged:
                    var.is_flagged = False
                if not self.solve_dup_kb(dup_kb):
                    # if not self.validate_kb(dup_kb):
                    if fake_val == 0:
                        if not var.is_flagged:
                            var.is_flagged = True
                            flag = True
                            if self.env.grid[var.row][var.col] != -1:
                                print("wrongly predicted")
                                sys.exit()
                    else:
                        if var.curr_value is None:
                            self.env.query_cell(var)
                            flag = True
                            if self.env.grid[var.row][var.col] == -1:
                                print("wrongly predicted")
                                sys.exit()
                    return True
        return flag

    def remove_dups(self, knowledge):
        res = []
        for i in knowledge:
            if i not in res:
                res.append(i)
        return res

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
                    if neighbour.is_mine:
                        print('Queried wrongly')
                        sys.exit()
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
        # if len(self.graphics.grid) == 0:
        #     # Initiating if this is te first time
        #     self.graphics.updateGrid(numeric_grid)
        #     self.graphics.Init_view()
        #     self.graphics.initVisuals()
        # # Updating graphics
        # self.graphics.updateGrid(numeric_grid)
        # # PPrint is impacting performance a lot
        # pprint(numeric_grid)


# Driver code to test
density_store = {}
flag_store = {}
# Iterating for range of mine density
for d in [4]:
    density = d / 10
    Store = {'bombs': [], 'time': [], 'flagged': []}
    for i in range(1):
        start = time.process_time()
        env = Environment(30, density)
        mines = env.m
        agent = NaiveAgent(env)
        agent.play()
        Store['bombs'].append(agent.mines_exploded)
        Store['flagged'].append((mines - agent.mines_exploded) / mines)
        Store['time'].append(time.process_time() - start)

    print('Average number of bombs exploded is ' + str(np.average(Store['bombs'])))
    print('Average time taken ' + str(np.average(Store['time'])))
    print('Average flags ' + str(np.average(Store['flagged'])))
    density_store[density] = str(np.average(Store['bombs']))
    flag_store[density] = str(np.average(Store['flagged']))
print(density_store)
for key in density_store.keys():
    print(str(key) + ',' + str(density_store[key]))
for key in flag_store.keys():
    print(str(key) + ',' + str(flag_store[key]))
