import random
from pprint import pprint
import math
import numpy
import pandas as pd
import itertools
from Environment import Cell, Environment
from Graphics_grid import GraphicGrid


class TI_Agent:

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
        self.env.query_cell(random_cell)
        self.unexplored_cells.remove(random_cell)
        self.render_basic_view()
        self.create_condition(random_cell)
        while True:
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
                    if cell1.is_flagged or cell1.is_mine:
                        constraint_value -= 1
                        continue
                    else:
                        condition.append(cell1)
        if len(condition) == constraint_value:
            for cell in condition:
                cell.is_flagged = True
                if cell in self.unexplored_cells:
                    self.unexplored_cells.remove(cell)
        elif condition and condition not in self.knowledge_base:
            self.knowledge_base.append([condition,constraint_value])
            self.probability()


    def possible_solutions(self,knowledge_base):
        unique_variables = []
        for condition in knowledge_base:
            for variable in condition[0]:
                if variable not in unique_variables:
                    unique_variables.append(variable)
        max_variables = 18 if len(unique_variables) > 18 else len(unique_variables)
        probable_sol = []
        max_variables_list = random.choices(unique_variables,k = max_variables)
        lst = list(map(list, itertools.product([0, 1], repeat=len(max_variables_list))))
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
                self.mine_cells.append(var)
                if var in self.unexplored_cells:
                    self.unexplored_cells.remove(var)
                var.is_flagged = True
            elif var_domain[var] == [0]:
                self.safe_cells.append(var)
        for condition in knowledge_base:
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
                    if neighbour in self.unexplored_cells:
                        self.unexplored_cells.remove(neighbour)
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
            self.possible_solutions(self.remove_dups(self.knowledge_base))
            random_cell = self.get_safe_cells()
            self.render_basic_view()
            # we have to write the logic for choosing random cell with probability
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


    # prob = 2  #for initialization
    # for row in range(self.grid_size):
    #     for column in range(self.grid_size):
    #         cell = self.currGrid[row][column]
    #         if cell.probability is not None and cell.probability is not 0:
    #             if cell.probability <= prob:
    #                 prob = cell.probability
    #                 random_cell = cell



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
        conditions = [condition[0] for condition in self.knowledge_base]
        random_cell = False
        conditions = list(itertools.chain.from_iterable(conditions))
        max = 0
        for cell in self.unexplored_cells:
            if conditions.count(cell) > max:
                max = conditions.count(cell)
                random_cell = cell
        return random_cell

# env = Environment(10, 0.3)
# agent = DI_Agent(env)
# agent.play()
avg = []
mine_density = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
for i in range(9):
  Store = []
  print("-------------------------------",i+1)
  for j in range(20):
    env = Environment(10, mine_density[i])
    agent = TI_Agent(env)
    agent.play()
    Store.append(agent.mines_exploded)
  avg.append(numpy.average(Store))

print("-------------------------------")
print(dict(zip(mine_density, avg)))