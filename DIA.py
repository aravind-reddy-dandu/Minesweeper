import random
from pprint import pprint
import math
import numpy
from Environment import Cell, Environment


class DI_Agent:

    def __init__(self, env):
        self.env = env
        self.grid_size = env.grid.shape[0]
        self.currGrid = [[Cell(j, i) for i in range(self.grid_size)] for j in range(self.grid_size)]
        self.mines_exploded = 0
        self.probability = None

    def play(self):
        random_cell = self.currGrid[random.randrange(0, len(self.currGrid) - 1)][
            random.randrange(0, len(self.currGrid) - 1)]
        self.env.query_cell(random_cell)
        while random_cell.is_mine:
            random_cell.is_mine = False
            random_cell.curr_value = None
            random_cell = self.currGrid[random.randrange(0, len(self.currGrid) - 1)][
                random.randrange(0, len(self.currGrid) - 1)]
            self.env.query_cell(random_cell)
        self.render_basic_view()
        while True:
            if self.look_over_grid() == 'Finished':
                break

        print(self.mines_exploded)

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
        if not self.open_random_cell():
            return 'Finished'
        return 'Done looping'

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

    def open_random_cell(self):
        if not self.have_free_cells():
            return False
        random_cell = self.currGrid[random.randrange(0, len(self.currGrid) - 1)][
            random.randrange(0, len(self.currGrid) - 1)]
        while not random_cell.is_flagged and random_cell.curr_value is not None:
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
        pprint(numeric_grid)



    # def probabilities_of_cells(self):
    #     for row in range(self.grid_size):
    #         for column in range(self.grid_size):
    #             cell = self.currGrid[row][column]
    #             if (cell.curr_value is not None) and not cell.is_flagged:
    #                 mines_remaining = cell.curr_value - cell.mines_surrounding
    #                 covered_cells = cell.covered_neighbours
    #                 prob_mine = mines_remaining / covered_cells
    #                 self.mark_neighbours_probability(cell, prob_mine)
    #
    # def mark_neighbours_probability(self, cell, prob_mine):
    #     for i in [-1, 0, 1]:
    #         for j in [-1, 0, 1]:
    #             if (i == 0 and j == 0) or not self.isCellValid(cell.row + i, cell.col + j):
    #                 continue
    #             neighbour = self.currGrid[cell.row + i][cell.col + j]
    #             if not neighbour.is_flagged and neighbour.curr_value is None:
    #                 if neighbour.probability < prob_mine or neighbour.probability is None:
    #                     neighbour.probability = prob_mine

    # IF cell == 1 finding count value
    # Substitute cell value as 1 and check for the number of valid possibilities
    def sub_1(self, cell):
        list1 = []
        list0 = []
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
                i[1] -= 1
                i[0].remove(cell)
        # repeat process till we find all the constrain equation values, if cell value is 0
        while 1:
            count1 = 0
            count2 = 0
            remove = []
            for i in range(0, len(equation_list)):
                check = equation_list[i][0]
                constraints = equation_list
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
                a *= math.factorial(len(i[0])) / (
                        math.factorial(i[1]) * math.factorial(len(i[0]) - i[1]))  # nCr formula
            return a

    KB = d2_list
# Substitute cell value as 0 and check for the number of valid possibilities
    def sub_0(self, cell):
        list1 = []
        list0 = []
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
                a *= math.factorial(len(i[0])) / (
                            math.factorial(i[1]) * math.factorial(len(i[0]) - i[1]))  # nCr formula
            return a

    # probability of each cell is the count of cell being a mine divided by total possibilities of it being a mine
    def probability(self):
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                cell = self.currGrid[row][column]
                cell.probability = sub_1(cell)/sub_1(cell) + sub_0(cell)



env = Environment(10, 0.2)
agent = DI_Agent(env)
agent.play()