import random
from pprint import pprint

import numpy
import pandas as pd
import itertools
from Environment import Cell, Environment
from Graphics_grid import GraphicGrid


class CSPAgent:

    def __init__(self, env):
        self.env = env
        self.grid_size = env.grid.shape[0]
        self.currGrid = [[Cell(j, i) for i in range(self.grid_size)] for j in range(self.grid_size)]
        self.mines_exploded = 0
        self.safe_cells = list()
        self.graphics = GraphicGrid([])
        self.knowledge_base = list()


    def play(self):
        random_cell = self.currGrid[random.randrange(0, len(self.currGrid) - 1)][random.randrange(0, len(self.currGrid) - 1)]
        self.env.query_cell(random_cell)
        while random_cell.is_mine:
            random_cell.is_mine = False
            random_cell.curr_value = None
            random_cell = self.currGrid[random.randrange(0, len(self.currGrid) - 1)][random.randrange(0, len(self.currGrid) - 1)]
            self.env.query_cell(random_cell)
        self.render_basic_view()
        while True:
            self.possible_solutions(self.remove_dups(self.knowledge_base))
            if self.look_over_grid() == 'Finished':
                break
        print(self.mines_exploded)

    def remove_dups(self,list):
        res = []
        for i in list:
            if i not in res:
                res.append(i)
        return res

    def look_over_grid(self):
        self.populate_all_cells()
        self.render_basic_view()
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                cell = self.currGrid[row][column]
                #self.populate_cell(cell)
                if (cell.curr_value is not None) and not cell.is_flagged:
                    if cell.curr_value - cell.mines_surrounding == cell.covered_neighbours:
                        if cell.curr_value != 0 and cell.covered_neighbours != 0:
                            self.flag_neighbours(cell)
                            return 'Done'
                    elif (cell.total_neighbours - cell.curr_value) - cell.safe_cells_surr == cell.covered_neighbours:
                        self.mark_neighbours_safe(cell)
                        return 'Done'
                    self.create_condition(cell)

        if not self.open_random_cell():
            return 'Finished'
        return 'Done looping'

    def create_condition(self, cell):
        row = cell.row
        col = cell.col
        condition = []
        constraint_value = cell.curr_value
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0):
                    continue
                if (row + i >= 0 and col + j >= 0 and row + i < self.env.n and col + j < self.env.n):
                    cell1 = self.currGrid[row + i][col + j]
                    self.populate_cell(cell1)
                    if cell1.curr_value is not None:
                        continue
                    if cell1.is_flagged:
                        constraint_value -= 1
                        continue
                    else:
                        condition.append(cell1)
        if condition and condition not in self.knowledge_base:
            self.knowledge_base.append([condition,constraint_value])


    def possible_solutions(self,knowledge_base):
        unique_variables = []
        for condition in knowledge_base:
            for variable in condition[0]:
                if variable not in unique_variables:
                    unique_variables.append(variable)
        max_variables = 15
        lst = list(map(list, itertools.product([0, 1], repeat=max_variables)))
        probable_sol = []
        max_variables_list = unique_variables[0:15]
        for assignment in lst:
            flag = 0
            sat = 0
            for condition in knowledge_base:
                sum = condition[1]
                sol = 0
                j = 0
                f = 0
                for var in condition[0]:
                    j += 1
                    if var in max_variables_list:
                        i = max_variables_list.index(var)
                        sol += assignment[i]
                    else:
                        break;
                else:
                    if j == len(condition[0]):
                        sat += 1
                        if (sol != sum):
                            break;
                        if (sol == sum):
                            flag += 1
            if flag == sat:
                probable_sol.append(assignment)
        probable_sol_df = pd.DataFrame(probable_sol)
        domain = []
        for col in probable_sol_df:
            domain.append(probable_sol_df[col].unique().tolist())
        var_domain = dict(zip(max_variables_list, domain))
        for var in var_domain:
            if var_domain[var] == [1]:
                var.is_flagged = True
            elif var_domain[var] == [0]:
                self.safe_cells.append(var)


    def populate_all_cells(self):
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                self.populate_cell(self.currGrid[row][column])

    def isCellValid(self, row: int, col: int):
        return (row >= 0) and (row < len(self.currGrid)) and (col >= 0) and (col < len(self.currGrid[0]))

    def populate_cell(self, cell):
        row = cell.row
        col = cell.col
        mines = 0
        covered = 0
        safe = 0
        total_neighbours = 0
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or not self.isCellValid(row + i, col + j):
                    continue
                neighbour = self.currGrid[row + i][col + j]
                total_neighbours += 1
                if neighbour.curr_value is None and not neighbour.is_mine and not neighbour.is_flagged:
                    covered += 1
                elif neighbour.is_flagged:
                    mines += 1
                else:
                    safe += 1
        cell.covered_neighbours = covered
        cell.mines_surrounding = mines
        cell.safe_cells_surr = safe
        cell.total_neighbours = total_neighbours

    def mark_neighbours_safe(self, cell):
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or not self.isCellValid(cell.row + i, cell.col + j):
                    continue
                neighbour = self.currGrid[cell.row + i][cell.col + j]
                if not neighbour.is_flagged and neighbour.curr_value is None:
                    self.env.query_cell(neighbour)
        self.render_basic_view()

    def flag_neighbours(self, cell):
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or not self.isCellValid(cell.row + i, cell.col + j):
                    continue
                neighbour = self.currGrid[cell.row + i][cell.col + j]
                if neighbour.curr_value is None:
                    neighbour.is_flagged = True
        self.render_basic_view()

    def have_free_cells(self):
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                cell = self.currGrid[row][column]
                if cell.curr_value is None and not cell.is_flagged:
                    return True
        return False

    def get_safe_cells(self):
        if len(self.safe_cells) > 0:
            safe_cell = self.safe_cells[0]
            self.safe_cells.remove(safe_cell)
            return safe_cell
        else:
            return False

    def open_random_cell(self):
        if not self.have_free_cells():
            return False
        random_cell = self.get_safe_cells()
        if not random_cell:
             random_cell = self.currGrid[random.randrange(0, len(self.currGrid) - 1)][random.randrange(0, len(self.currGrid) - 1)]
        while random_cell.is_flagged or (random_cell.curr_value is not None):
            random_cell = self.currGrid[random.randrange(0, len(self.currGrid) - 1)][
                random.randrange(0, len(self.currGrid) - 1)]
        self.env.query_cell(random_cell)
        if random_cell.is_mine:
            self.mines_exploded += 1
            random_cell.is_flagged = True
        self.render_basic_view()
        return True

    def render_basic_view(self):
        numeric_grid = [['N' for x in range(self.grid_size)] for y in range(self.grid_size)]
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                numeric_grid[row][column] = self.currGrid[row][column].curr_value
                if self.currGrid[row][column].is_flagged:
                    numeric_grid[row][column] = 'f'
                if self.currGrid[row][column].is_mine:
                    numeric_grid[row][column] = 'b'
        #if len(self.graphics.grid) == 0:
         #   self.graphics.updateGrid(numeric_grid)
          #  self.graphics.Init_view()
           # self.graphics.initVisuals()
        #self.graphics.updateGrid(numeric_grid)
        #pprint(numeric_grid)


Store = []
for i in range(10):
    env = Environment(10, 0.3)
    agent = CSPAgent(env)
    agent.play()
    Store.append(agent.mines_exploded)

avg = numpy.average(Store)
print(avg)
