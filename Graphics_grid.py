import pygame
from Environment import Cell


class GraphicGrid:

    def __init__(self, grid):
        self.grid = grid

    def updateGrid(self, grid):
        self.grid = grid
        self.initVisuals()

    def initVisuals(self):
        BLACK, GREEN, GREY, HEIGHT, MARGIN, RED, WIDTH, YELLOW, clock, screen = self.Init_view()

        # Draw the grid
        for row in range(len(self.grid)):
            for column in range(len(self.grid)):
                if self.grid[row][column] is None:
                    color = GREY
                elif self.grid[row][column] == 'b':
                    color = RED
                elif self.grid[row][column] == 'f':
                    color = YELLOW
                else:
                    color = GREEN
                pygame.draw.rect(screen,
                                 color,
                                 [(MARGIN + WIDTH) * column + MARGIN,
                                  (MARGIN + HEIGHT) * row + MARGIN,
                                  WIDTH,
                                  HEIGHT])
                if self.grid[row][column] == 'b':
                    screen.blit(pygame.font.SysFont('Arial', 25).render('B', True, BLACK),
                                ((MARGIN + WIDTH) * column + MARGIN + 5, (MARGIN + HEIGHT) * row + MARGIN - 5))
                elif self.grid[row][column] == 'f':
                    screen.blit(pygame.font.SysFont('Arial', 25).render('F', True, BLACK),
                                ((MARGIN + WIDTH) * column + MARGIN + 5, (MARGIN + HEIGHT) * row + MARGIN - 5))
                elif self.grid[row][column] is None:
                    pass
                else:
                    screen.blit(pygame.font.SysFont('Arial', 25).render(str(self.grid[row][column]), True, BLACK),
                                ((MARGIN + WIDTH) * column + MARGIN + 5, (MARGIN + HEIGHT) * row + MARGIN - 5))

        # Limit to 60 frames per second
        clock.tick(60)

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Be IDLE friendly. If you forget this line, the program will 'hang'
        # on exit.

    def Init_view(self):
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        GREEN = (0, 255, 0)
        RED = (255, 0, 0)
        GREY = (128, 128, 128)
        YELLOW = (255, 255, 0)
        # This sets the WIDTH and HEIGHT of each grid location
        WIDTH = 20
        HEIGHT = 20
        # This sets the margin between each cell
        MARGIN = 5
        # Initialize pygame
        pygame.init()
        # Set the HEIGHT and WIDTH of the screen
        l = int((len(self.grid) * 255) / 10)
        WINDOW_SIZE = [l, l]
        screen = pygame.display.set_mode(WINDOW_SIZE)
        # Set title of screen
        pygame.display.set_caption("MineSweeper")
        # Loop until the user clicks the close button.
        done = False
        # Used to manage how fast the screen updates
        clock = pygame.time.Clock()
        # Set the screen background
        screen.fill(BLACK)
        return BLACK, GREEN, GREY, HEIGHT, MARGIN, RED, WIDTH, YELLOW, clock, screen

    def quit_visuals(self):
        pygame.quit()
