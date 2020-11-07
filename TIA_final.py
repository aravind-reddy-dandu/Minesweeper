import random
import copy
import sys
import time
from pprint import pprint

import numpy as np
import pandas as pd
import itertools
from Environment import Cell, Environment
from Graphics_grid import GraphicGrid


class CSPAgent:

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
        # Creating a condition for the cell in knowledge base.
        self.create_condition(random_cell)
        # Play until all cells are finished
        while True:
            if self.look_over_grid() == 'Finished':
                break
        #Print no. of mines exploded
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
                    self.check_for_valid_sols()
                    # Remove duplicates in knowledge base
                    self.knowledge_base = self.remove_dups(self.knowledge_base)
                    # Creating a condition for the cell in knowledge base.
                    self.create_condition(cell)
        # If nothing is done in looping, open a random cell. if no random cell is present, game is done
        if not self.open_random_cell():
            return 'Finished'
        return 'Done looping'

    # Remove duplicates from the knowledge base.
    def remove_dups(self, list):
        res = []
        for i in list:
            #Check if condition already exits in knowledge base.
            if i not in res:
                res.append(i)
        return res

    # Function to create condition for the cell based on the revealed number.
    def create_condition(self, cell):
        # Get row and column indices of the cell.
        row = cell.row
        col = cell.col
        condition = []
        # Constrain value is the revealed number of the cell.
        constraint_value = cell.curr_value
        # for each possible neighbour of the cell.
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                # Ignore the current cell
                if (i == 0 and j == 0):
                    continue
                # Check if it is a valid neighbour of the cell
                if (row + i >= 0 and col + j >= 0 and row + i < self.env.n and col + j < self.env.n):
                    # Assign the neighbour in cell1 and populate it.
                    cell1 = self.currGrid[row + i][col + j]
                    # Populate the neighbour information.
                    self.populate_cell(cell1)
                    # When the neighbour is unexplored and not flagged we append it in the condition
                    if cell1.curr_value is None and not cell1.is_flagged:
                        condition.append(cell1)
                    # When the neighbour is mine or is flagged we don't append it in the condition
                    # but decrease the constraint value by 1
                    if cell1.is_flagged or cell1.is_mine:
                        constraint_value -= 1
                        continue
                    # Ignore if the neighbour is an explored safe cell.
                    if cell1.curr_value is not None:
                        continue
        # When no. of cell in equation is equal to constraint value it means
        # all the cells in equation are mines so flag them.
        if len(condition) == constraint_value and not constraint_value < 0:
            for cell in condition:
                cell.is_flagged = True
                # Remove the flagged cell from unexplored cells list to avoid blast.
                if cell in self.unexplored_cells:
                    self.unexplored_cells.remove(cell)
        #Add the condition to the knowledge base
        elif condition and condition not in [con[0] for con in self.knowledge_base] and constraint_value >= 0:
            self.knowledge_base.append([condition, constraint_value])

    #Remove the safe cells and mine cells from the equations in the knowledge base.
    def substitute_values(self, kb):
        # Looping all the conditions in the knowledge base
        for index, equation in enumerate(kb):
            # Seperating cells from constraint value
            cells_part = equation[0]
            # for all the cells in a equation we remove safe explored cells and mine/flagged cells.
            for cell in cells_part:
                if cell.curr_value is not None and not cell.is_flagged and not cell.is_mine:
                    cells_part.remove(cell)
                elif cell.is_flagged or cell.is_mine:
                    cells_part.remove(cell)
                    equation[1] = equation[1] - 1
            # Remove null cells
            if len(cells_part) == 0:
                kb.remove(equation)

    #Cleaning the knowledge base
    def check_for_valid_sols(self):
        # Looping all the conditions in the knowledge base
        for index, equation in enumerate(self.knowledge_base):
            # Seperating cells from constraint value
            cells_part = equation[0]
            # If there is only 1 cell in the equation
            if len(cells_part) == 1:
                # Safe cell
                if equation[1] == 0:
                    if cells_part[0].curr_value is not None:
                        self.safe_cells.append(cells_part[0])
                # Mine cell identification.
                elif equation[1] == 1:
                    cells_part[0].is_flagged = True
                self.knowledge_base.remove(equation)
            # When no. of cell in equation is equal to constraint value it means all the cells
            # in equation are mines so flag them.
            elif len(cells_part) == equation[1] and not equation[1] < 0:
                for cell in cells_part:
                    cell.is_flagged = True
                # Remove the equation from knowledge base
                self.knowledge_base.remove(equation)
        self.substitute_values(self.knowledge_base)

    # Implementing proof by contradiction for Constraint Satisfaction problem heuristic
    def possible_solutions(self):
        # Cleaning the knowledge base
        self.substitute_values(self.knowledge_base)
        # Initializing unique variables in the knowledge base as null
        unique_variables = {}
        # Remove duplicates in knowledge base
        self.knowledge_base = self.remove_dups(self.knowledge_base)
        self.check_for_valid_sols()
        # Check the variable occurrence for each unique cell in knowledge base
        for condition in self.knowledge_base:
            for variable in condition[0]:
                if variable not in unique_variables.keys():
                    unique_variables[variable] = 1
                else:
                    unique_variables[variable] += 1
        # Cells occurred more than once are stored in interesting variables.
        interesting_vars = []
        for key in unique_variables.keys():
            if unique_variables[key] > 1:
                interesting_vars.append(key)
        flag = False
        # We are assigning values for each cell in interesting_vars and checking if this assignment breaks
        # the knowledge base if it does then the other value of the cell domain is true.
        for var in interesting_vars:
            fake_vals = [0, 1]
            #Ignore flagged cells.
            if var.is_flagged:
                continue
            # Assigning a value in the domain.
            for fake_val in fake_vals:
                # Ignore flagged cells.
                if var.is_flagged:
                    continue
                # Make a copy of the knowledge base
                dup_kb = copy.deepcopy(self.knowledge_base)
                # Store the current value of the cell
                prev_val = var.curr_value
                #Change the value of the cell to fake one
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
                        var.is_flagged = True
                        flag = True
                        self.mine_cells.append(var)
                        if var in self.unexplored_cells:
                            self.unexplored_cells.remove(var)
                        if self.env.grid[var.row][var.col] != -1:
                            print("wrongly predicted")
                            sys.exit()
                    else:
                        if var not in self.safe_cells:
                            self.safe_cells.append(var)
                            flag = True
                        # self.env.query_cell(var)
                        if self.env.grid[var.row][var.col] == -1:
                            print("wrongly predicted")
                            sys.exit()
                    self.check_for_valid_sols()
                    break
                self.check_for_valid_sols()

        # Clean the knowledge base
        for condition in self.knowledge_base:
            #Remove safe cells from the knowledge base
            for safe_cell in self.safe_cells:
                if safe_cell in condition[0]:
                    condition[0].remove(safe_cell)
            # Remove mine and flagged cells from knowledge base and reduce constraint value by 1
            for mine_cell in self.mine_cells:
                if mine_cell in condition[0]:
                    condition[0].remove(mine_cell)
                    condition[1] -= 1
        return flag

    # Check if the knowledge base is solvable
    def is_kb_solvable(self, kb):
        # Looping all the conditions in the knowledge base
        for index, equation in enumerate(kb):
            # Seperating cells from constraint value
            cells_part = equation[0]
            # When no. of cell in equation is equal to constraint value or 1 it means the equation is solvable.
            if len(cells_part) == equation[1]:
                return True
            if len(cells_part) == 1:
                return True
        return False

    # Solve the duplicate knowledge base which has substituted values
    def solve_dup_kb(self, kb):
        # loop until knowledge base is solvable.
        while self.is_kb_solvable(kb):
            # Looping all the conditions in the knowledge base
            for index, equation in enumerate(kb):
                # Seperating cells from constraint value
                cells_part = equation[0]
                # When constraint value is < 0 or > than no. of cells in equations it means knowledge base is broken.
                if equation[1] < 0 or len(cells_part) < equation[1]:
                    return False
                if len(cells_part) == equation[1]:
                    # flag all cells
                    for cell in cells_part:
                        cell.is_flagged = True
                # for single cell conditions classify safe and mine cells.
                if len(cells_part) == 1:
                    if equation[1] == 0:
                        cells_part[0].curr_value = 0
                    elif equation[1] == 1:
                        cells_part[0].is_flagged = True
            self.substitute_values(kb)
        return True

    def substitute_val_in_kb(self, change_cell, kb):
        # Looping all the conditions in the knowledge base
        for equation in kb:
            # Separating cells from constraint value
            cells_part = equation[0]
            # For each occurrence of cell in knowledge base we are substituting new fake value to test knowledge base
            for cell in cells_part:
                if change_cell.row == cell.row and change_cell.col == cell.col:
                    if change_cell.curr_value is not None and not change_cell.is_flagged and not change_cell.is_mine:
                        cells_part.remove(cell)
                    elif change_cell.is_flagged or change_cell.is_mine:
                        cells_part.remove(cell)
                        equation[1] = equation[1] - 1

    # Method to populate all cells initially to unexplored cells list.
    def populate_unexplored_cells(self):
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                self.unexplored_cells.append(self.currGrid[row][column])

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

    # Method to get a safe cell from the safe cells list
    def get_safe_cells(self):
        if len(self.safe_cells) > 0:
            safe_cell = self.safe_cells[0]
            self.safe_cells.remove(safe_cell)
            return safe_cell
        else:
            return False

    # Method to open random cell
    def open_random_cell(self):
        # Return if all cells are opened or flagged
        if not self.have_free_cells():
            return False
        # Get a safe cell to open
        random_cell = self.get_safe_cells()
        # If no safe cells available run possible solutions to see if new safe cells are available.
        if not random_cell:
            flag = self.possible_solutions()
            while flag:
                flag = self.possible_solutions()
            random_cell = self.get_safe_cells()
            self.render_basic_view()
            # logic for choosing random cell with probability
            if not random_cell:
                prob = 2
                for cell in self.unexplored_cells:
                    if cell.probability != None:
                        min_cell = cell
                        if min_cell.probability < prob:
                            prob = min_cell.probability
                            random_cell = min_cell
                    else:
                        continue
                else:
                    if not random_cell:
                        random_cell = self.most_occurred()
            if not random_cell:
                random_cell = random.choice(self.unexplored_cells)
                while random_cell.is_flagged or (random_cell.curr_value is not None):
                    random_cell = self.currGrid[random.randrange(0, len(self.currGrid))][
                        random.randrange(0, len(self.currGrid))]
        if random_cell in self.unexplored_cells:
            self.unexplored_cells.remove(random_cell)
        # Query that random cell
        self.env.query_cell(random_cell)
        if random_cell.is_mine:
            self.mines_exploded += 1
            random_cell.is_flagged = True
        elif (random_cell.curr_value is not None) and not random_cell.is_flagged:
            self.create_condition(random_cell)
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

    # IF cell == 1 finding count value
    # Substitute cell value as 1 and check for the number of valid possibilities
    def sub_1(self, cell, kb):
        equation_list = kb
        list1 = []
        list0 = []
        cell_neighbours = []
        row = cell.row
        col = cell.col
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or not self.isCellValid(row + i, col + j):
                    continue
                neighbour = self.currGrid[row + i][col + j]
                cell_neighbours.append(neighbour)
        # taking only required equation from KB
        for i in equation_list:
            count_1 = 0
            for j in cell_neighbours:
                if j in i[0]:
                    count_1 += 1
            if count_1 == 0:
                equation_list.remove(i)
        # substitute cell as 1 in the equations of the knowledge base
        for i in equation_list:
            if cell in i[0]:
                i[1] -= 1
                i[0].remove(cell)
        # repeat process till we find all the constrain equation values, if cell value is 0
        while 1:
            count1 = 0
            count2 = 0
            remove = []
            for i in range(0, len(equation_list)):
                # finding other cell values when given cell is assumed to be a mine
                if len(equation_list[i][0]) == equation_list[i][1]:
                    count1 += 1
                    for k in equation_list[i][0]:
                        list1.append(k)  # append cells to list1
                    remove.append(equation_list[i][0])
                elif equation_list[i][1] == 0:
                    count2 += 1
                    for k in equation_list[i][0]:
                        list0.append(k)  # append cells to list0
                    remove.append(equation_list[i][0])
            for i in equation_list:
                for j in remove:
                    if j == i[0]:
                        equation_list.remove(i)

            # updating the equations
            for i in range(0, len(equation_list)):
                for j in list0:
                    if j in equation_list[i][0]:
                        count2 += 1
                        equation_list[i][0].remove(j)
                for k in list1:
                    if k in equation_list[i][0]:
                        count1 += 1
                        equation_list[i][1] -= 1
                        equation_list[i][0].remove(k)

            if count1 != 0 or count2 != 0:
                continue
            else:
                break

        if len(equation_list) == 0:
            return 1
        else:
            a = 1
            for i in equation_list:
                a *= math.factorial(len(i[0])) / (math.factorial(i[1]) * math.factorial(len(i[0]) - i[1]))  # nCr formula
            return a

# Substitute cell value as 0 and check for the number of valid possibilities
    def sub_0(self, cell, kb):
        equation_list = kb
        list1 = []
        list0 = []
        cell_neighbours = []
        row = cell.row
        col = cell.col
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or not self.isCellValid(row + i, col + j):
                    continue
                neighbour = self.currGrid[row + i][col + j]
                cell_neighbours.append(neighbour)
        # taking only required equation from KB
        for i in equation_list:
            count_1 = 0
            for j in cell_neighbours:
                if j in i[0]:
                    count_1 += 1
            if count_1 == 0:
                equation_list.remove(i)
        # sub cell = 0
        for i in equation_list:
            if cell in i[0]:
                i[0].remove(cell)
        # repeat process till we find all the constrain equation values, if cell value is 0
        while 1:
            count1 = 0
            count2 = 0
            remove = []
            for i in range(0, len(equation_list)):
                if len(equation_list[i][0]) == equation_list[i][1]:
                    count1 += 1
                    for k in equation_list[i][0]:
                        list1.append(k)  # append cells to list1
                    remove.append(equation_list[i][0])
                elif equation_list[i][1] == 0:
                    count2 += 1
                    for k in equation_list[i][0]:
                        list0.append(k)  # append cells to list0
                    remove.append(equation_list[i][0])
            for i in equation_list:
                for j in remove:
                    if j == i[0]:
                        equation_list.remove(i)

            # updating the equations
            for i in range(0, len(equation_list)):
                for j in list0:
                    if j in equation_list[i][0]:
                        count2 += 1
                        equation_list[i][0].remove(j)
                for k in list1:
                    if k in equation_list[i][0]:
                        count1 += 1
                        equation_list[i][1] -= 1
                        equation_list[i][0].remove(k)

            if count1 != 0 or count2 != 0:
                continue
            else:
                break
        if len(equation_list) == 0:
            return 1
        else:
            a = 1
            for i in equation_list:
                a *= math.factorial(len(i[0])) / (math.factorial(i[1]) * math.factorial(len(i[0]) - i[1]))  # nCr formula
            return a

    # probability of each cell is the count of cell being a mine divided by total possibilities of it being a mine
    def probability(self):
        conditions = [condition[0] for condition in self.knowledge_base]
        for cell in self.unexplored_cells:
            if cell in conditions:
                    cell.probability = self.sub_1(cell, self.knowledge_base) / (self.sub_1(cell, self.knowledge_base) + self.sub_0(cell , self.knowledge_base))
                # p1 = self.sub_1(cell, self.knowledge_base)
                # p0 = self.sub_0(cell, self.knowledge_base)
                # a = cell.probability

    #Triple improved agent
    def most_occurred(self):
        #get all the conditions in the knowledge base
        conditions = [condition[0] for condition in self.knowledge_base]
        #Initialize random_cell as null
        random_cell = False
        #Merge the list of conditions into a single list
        conditions = list(itertools.chain.from_iterable(conditions))
        max = 0
        # for each cell in knowledge base we check the no of occurences and return most occurred cell.
        for cell in self.unexplored_cells:
            if conditions.count(cell) > max:
                max = conditions.count(cell)
                random_cell = cell
        return random_cell


# Driver code to test
density_store = {}
flag_store = {}
# Iterating for range of mine density
for d in range(1,10):
    density = d / 10
    Store = {'bombs': [], 'time': [], 'flagged': []}
    for i in range(10):
        start = time.process_time()
        env = Environment(20, density)
        mines = env.m
        agent = CSPAgent(env)
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
    print(str(key) + ',' + str(density_store[key]) + ',' + str(flag_store[key]))
for key in flag_store.keys():
    print(str(key) + ',' + str(flag_store[key]))
