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

    def __init__(self, env):
        self.env = env
        self.grid_size = env.grid.shape[0]
        self.currGrid = [[Cell(j, i) for i in range(self.grid_size)] for j in range(self.grid_size)]
        self.mines_exploded = 0
        self.safe_cells = list()
        self.mine_cells = list()
        self.graphics = GraphicGrid([])
        self.knowledge_base = list()
        self.unexplored_cells = list()

    def play(self):
        self.populate_unexplored_cells()
        random_cell = random.choice(self.unexplored_cells)
        while random_cell.is_mine:
            random_cell.is_mine = False
            random_cell.curr_value = None
            random_cell = self.currGrid[random.randrange(0, len(self.currGrid))][
                random.randrange(0, len(self.currGrid))]
            self.env.query_cell(random_cell)
        self.env.query_cell(random_cell)
        if random_cell.is_mine:
            random_cell.is_flagged = True
        self.unexplored_cells.remove(random_cell)
        self.render_basic_view()
        self.create_condition(random_cell)
        while True:
            if self.look_over_grid() == 'Finished':
                break
        print(self.mines_exploded)

    def remove_dups(self, list):
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
                self.populate_cell(cell)
                if (cell.curr_value is not None) and not cell.is_flagged:
                    if cell.curr_value - cell.mines_surrounding == cell.covered_neighbours:
                        if cell.curr_value != 0 and cell.covered_neighbours != 0:
                            self.flag_neighbours(cell)
                            return 'Done'
                    elif (cell.total_neighbours - cell.curr_value) - cell.safe_cells_surr == cell.covered_neighbours:
                        self.mark_neighbours_safe(cell)
                        return 'Done'
                    self.check_for_valid_sols()
                    self.knowledge_base = self.remove_dups(self.knowledge_base)
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
                    if cell1.curr_value is None and not cell1.is_flagged:
                        condition.append(cell1)
                    if cell1.is_flagged or cell1.is_mine:
                        constraint_value -= 1
                        continue
                    if cell1.curr_value is not None:
                        continue
        if len(condition) == constraint_value and not constraint_value < 0:
            for cell in condition:
                cell.is_flagged = True
                if cell in self.unexplored_cells:
                    self.unexplored_cells.remove(cell)
        elif condition and condition not in [con[0] for con in self.knowledge_base] and constraint_value >= 0:
            self.knowledge_base.append([condition, constraint_value])

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

    def check_for_valid_sols(self):
        for index, equation in enumerate(self.knowledge_base):
            cells_part = equation[0]
            if len(cells_part) == 1:
                if equation[1] == 0:
                    if cells_part[0].curr_value is not None:
                        self.safe_cells.append(cells_part[0])
                elif equation[1] == 1:
                    cells_part[0].is_flagged = True
                self.knowledge_base.remove(equation)
            elif len(cells_part) == equation[1] and not equation[1] < 0:
                for cell in cells_part:
                    cell.is_flagged = True
                self.knowledge_base.remove(equation)
        self.substitute_values(self.knowledge_base)

    def possible_solutions(self):
        self.substitute_values(self.knowledge_base)
        unique_variables = {}
        self.knowledge_base = self.remove_dups(self.knowledge_base)
        self.check_for_valid_sols()
        for condition in self.knowledge_base:
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
                dup_kb = copy.deepcopy(self.knowledge_base)
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
        for condition in self.knowledge_base:
            for safe_cell in self.safe_cells:
                if safe_cell in condition[0]:
                    condition[0].remove(safe_cell)
            for mine_cell in self.mine_cells:
                if mine_cell in condition[0]:
                    condition[0].remove(mine_cell)
                    condition[1] -= 1
        return flag

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

    def possible_solutions_old(self):
        self.substitute_values(self.knowledge_base)
        unique_variables = []
        self.knowledge_base = self.remove_dups(self.knowledge_base)
        for condition in self.knowledge_base:
            for variable in condition[0]:
                if variable not in unique_variables:
                    unique_variables.append(variable)
        max_variables = 13 if len(unique_variables) > 13 else len(unique_variables)
        probable_sol = []
        max_variables_list = random.choices(unique_variables, k=max_variables)
        lst = list(map(list, itertools.product([0, 1], repeat=len(max_variables_list))))
        for assignment in lst:
            flag = 0
            sat = 0
            for condition in self.knowledge_base:
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
                self.mine_cells.append(var)
                if var in self.unexplored_cells:
                    self.unexplored_cells.remove(var)
                var.is_flagged = True
            elif var_domain[var] == [0]:
                self.safe_cells.append(var)
        for condition in self.knowledge_base:
            for safe_cell in self.safe_cells:
                if safe_cell in condition[0]:
                    condition[0].remove(safe_cell)
            for mine_cell in self.mine_cells:
                if mine_cell in condition[0]:
                    condition[0].remove(mine_cell)
                    condition[1] -= 1

    def populate_unexplored_cells(self):
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                self.unexplored_cells.append(self.currGrid[row][column])

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
                elif neighbour.is_flagged or neighbour.is_mine:
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
                    if neighbour in self.unexplored_cells:
                        self.unexplored_cells.remove(neighbour)
                    self.env.query_cell(neighbour)
                    if neighbour.is_mine:
                        print('Queried wrongly')
                        sys.exit()
        self.render_basic_view()

    def flag_neighbours(self, cell):
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i == 0 and j == 0) or not self.isCellValid(cell.row + i, cell.col + j):
                    continue
                neighbour = self.currGrid[cell.row + i][cell.col + j]
                if neighbour.curr_value is None:
                    neighbour.is_flagged = True
                    if neighbour in self.unexplored_cells:
                        self.unexplored_cells.remove(neighbour)
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
            flag = self.possible_solutions()
            while flag:
                flag = self.possible_solutions()
            random_cell = self.get_safe_cells()
            self.render_basic_view()
            if not random_cell:
                random_cell = random.choice(self.unexplored_cells)
                while random_cell.is_flagged or (random_cell.curr_value is not None):
                    random_cell = self.currGrid[random.randrange(0, len(self.currGrid))][
                        random.randrange(0, len(self.currGrid))]
        if random_cell in self.unexplored_cells:
            self.unexplored_cells.remove(random_cell)
        self.env.query_cell(random_cell)
        if random_cell.is_mine:
            self.mines_exploded += 1
            random_cell.is_flagged = True
        elif (random_cell.curr_value is not None) and not random_cell.is_flagged:
            self.create_condition(random_cell)
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
        # if len(self.graphics.grid) == 0:
        #   self.graphics.updateGrid(numeric_grid)
        #   self.graphics.Init_view()
        #   self.graphics.initVisuals()
        # self.graphics.updateGrid(numeric_grid)
        # pprint(numeric_grid)

    # def validate_kb(self, kb):
    #     for equation in kb:
    #         cells_part = equation[0]
    #         val = equation[1]
    #         if len(cells_part) < val:
    #             return False
    #     return True


# avg = []
# mine_density = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
# for i in range(1,10):
#   Store = []
#   print("-------------------------------",i)
#   for j in range(10):
#     env = Environment(10, mine_density[i])
#     agent = CSPAgent(env)
#     agent.play()
#     Store.append(agent.mines_exploded)
#   avg.append(numpy.average(Store))
#
# print("-------------------------------")
# print(dict(zip(mine_density, avg)))

# for i in range(20):
#     env = Environment(10, 0.4)
#     agent = CSPAgent(env)
#     agent.play()
#     pprint(env.grid)
#
#     for row in range(10):
#         for column in range(10):
#             if env.grid[row][column] == -1 and not agent.currGrid[row][column].is_flagged:
#                 if agent.currGrid[row][column].is_mine:
#                     print('Bomb not flagged at ' + str(row) + ',' + str(column))
#                 print('Wrong at ' + str(row) + ',' + str(column))


# Driver code to test
density_store = {}
flag_store = {}
# Iterating for range of mine density
for d in [4]:
    density = d / 10
    Store = {'bombs': [], 'time': [], 'flagged': []}
    for i in range(20):
        start = time.process_time()
        env = Environment(10, density)
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
    print(str(key) + ',' + str(density_store[key]))
for key in flag_store.keys():
    print(str(key) + ',' + str(flag_store[key]))
