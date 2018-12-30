from random import randint, choice
import pygame


######## Cell Class ########
# Parameters:- xpos: integer, ypos: integer, size: integer
# Return type:- n/a
# Purpose: Contains the attributes for the cell, used in MazeGen and A_Star_Search
##########################
class Cell:
    def __init__(self, xpos, ypos, size):
        self.walls = {"N": None, "E": None, "S": None, "W": None}
        self.visited = False
        self.pos = (xpos, ypos)

        self.xpos = xpos
        self.ypos = ypos
        self.size = size

        self.pixelpos = (size*xpos, size*ypos)

        self.rect = "pygame.Rect(self.pixelpos[0], self.pixelpos[1], size, size)"
        # Both as string as we need to send cell obj over to client first.
        self.point_list = '{"N": [self.rect.topleft, self.rect.topright], '' \
        ''"E": [self.rect.topright, self.rect.bottomright], ' \
         '"S": [self.rect.bottomright, self.rect.bottomleft],' \
         '"W": [self.rect.topleft, self.rect.bottomleft]}'

        # used for A* Search
        self.parent = None
        self.g_score = 100000000  # infinite value, so a big val. could use math.inf, but is class and hard to serialise
        self.h_score = 0
        self.f_score = 100000000  # h val + shortest from root(g val)

######## Maze Class ########
# Parameters:- level: integer, width: integer, length: integer, size: integer
# Return type:- n/a
# Purpose: Contains the attributes and methods for the maze generation
##########################
class Maze:  # depth-first generation
    def __init__(self, level, width=20, length=20, size=25):
        self.size = size
        self.n_dire = {"N": "S", "E": "W", "S": "N", "W": "E"}
        self.width = width
        self.length = length
        root = (randint(0, self.length - 1), randint(0, self.width - 1))  # 0 is counted as a value, so -1 is needed
        self.root_node = root  # so -1 is required
        self.maze = [[(Cell(x, y, size)) for y in range(self.width)] for x in range(self.length)]
        self.stack = []
        self.running = True
        self.root_rect = pygame.Rect(size*root[0], size*root[1], size, size)

        self.key_list = []
        self.door = None

        self.create_object_pos(level)

    ######## create_object_pos Method ########
    # Parameters:- level: integer
    # Return type:- n/a
    # Purpose: Will create none duplicate positions for the keys and the door, the former being positioned in either
    #          left or right segments of the maze
    ##########################
    def create_object_pos(self, level):
        key_lim = 7 if level > 5 else level + 1  # each level has + 1 keys until level > 7, where keys are 7
        rand_door_pos = {"N": (randint(0, self.length - 1), 0),
                         "E": (self.width - 1, randint(0, self.length - 1)),
                         "S": (randint(0, self.width - 1), self.length - 1),
                         "W": (0, randint(0, self.length - 1))}
        switch = 0  # used to swap between random place on the left or random place on the right by changing boundaries
        bounds = [  # two arrays in an array
            [(0, (self.width // 2) - 2),  # key is from left to 1 from the left middle. x has - 1 due to too many vals,
             (0, self.length - 1)],  # - 1 again as to ensure not middle exact. Don't want keys destined for right and
            # left in same column
            [((self.width // 2), self.width - 1),  # key is from 1 to the right of middle to end. would be - 1 as too
             (0, self.length - 1)]  # many vals then + 1 for not middle exact. Cancels each other out so nothing.
        ]

        for num in range(0, key_lim):
            # bigger than the actual difference. ie in range (0, 1) means 2 loops, not one
            while True:  # keeps making new positions for key if doesnt pass the ifs
                key = (randint(*bounds[switch][0]), randint(*bounds[switch][1]))  # *= unpacks tuple, no indexing needed
                if key in [*self.key_list, self.door, (0, 0), (19, 19), (0, 19), (19, 19)]:  # check pos if overlaps
                    continue  # door or players pos and will loop again, making new key pos if it does overlap
                else:
                    if switch == 1:  # swaps boundries that the pos of key can be in
                        switch -= 1
                    else:
                        switch += 1
                    self.key_list.append(key)  # once checked and valid
                    break
        while True:
            self.door = rand_door_pos[choice(["N", "E", "S", "W"])]  # chooses random coord
            if self.door not in [*self.key_list, (0, 0), (19, 19), (0, 19), (19, 19)]:
                break  # keeps looping until valid coord found

    ######## generate Method ########
    # Parameters:- current: self.Cell object
    # Return type:- n/a
    # Purpose: Will loop through random neighbouring cells, and break the wall between, to form a path, backtracking if
    #          if needed where there aren't any neighbouring cells. Loops each iteration with the random cell as current
    ##########################
    def generate(self, current):
        while True:
            current.visited = True
            neighbours = self.get_neighbours(current, False)
            if len(neighbours) is 0:
                if current.pos == self.root_node:
                    break
                else:
                    current = self.stack.pop()  # backtracks the route
                    # self.generate(self.stack.pop())
            else:
                rand_neighbour = choice(neighbours)  # random neighbour. the var set contains tuple; (dir, x, y)
                dire = rand_neighbour[0]
                n_cell = self.maze[rand_neighbour[1]][rand_neighbour[2]]
                self.break_wall(current, n_cell, dire)
                self.stack.append(n_cell)  # add to stack the n_cell cell for backtracking

                current = n_cell
                # self.generate(n_cell)

        self.dead_end_create_for_objects()

    ######## dead_end_removal Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Removes any dead ends after the cell has been generated, unless dead end is used for a key or a door
    ##########################
    def dead_end_removal(self):
        x_coord = -1
        y_coord = -1
        for x in range(self.length):
            x_coord += 1
            for y in range(self.width):
                y_coord += 1
                cell = self.maze[x][y]
                neighbours = []
                if len(cell.walls) >= 3:
                    if cell.pos not in [*self.key_list, self.door]:  # if the cell is not a dead end which is needed
                        initial_neighbours = self.get_neighbours(cell, 1)
                        for cell_pos in initial_neighbours:  # checks neighbors if they are deadends for items
                            if cell_pos[1:] not in [*self.key_list, self.door]:  # tuple has the following("N", x, y)
                                neighbours.append(cell_pos)  # validates cell which don't interfere with dend for object
                        if len(neighbours) is not 0:
                            rand_neighbour = choice(neighbours)
                            n_cell = self.maze[rand_neighbour[1]][rand_neighbour[2]]
                            self.break_wall(cell, n_cell, rand_neighbour[0])
            y_coord = -1

    ######## dead_end_create_for_objects Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Creates dead ends for the objects, if needed, after the maze has been generated
    ##########################
    def dead_end_create_for_objects(self):
        for pos in [*self.key_list, self.door]:  # unpacks tuple again
            cell = self.maze[pos[0]][pos[1]]
            x = cell.pos[0]
            y = cell.pos[1]
            direct = {"N": (x, y - 1), "E": (x + 1, y),  # for adjacent cell to add wall too
                      "S": (x, y + 1), "W": (x - 1, y)}
            valid_dirs = ["N", "E", "S", "W"]  # removes existing walls of cell leaving walls valid to add on

            walls = cell.walls
            for w in walls:  # finds walls available to add on by removing existing ones from list
                valid_dirs.remove(w)

            while len(valid_dirs) is not 1:  # will keep adding walls until one left, so 3 are there in total
                wall = choice(valid_dirs)
                self.maze[pos[0]][pos[1]].walls[wall] = None  # makes dict entry for new wall
                self.maze[direct[wall][0]][direct[wall][1]].walls[self.n_dire[wall]] = None  # same here, but using the
                # n_dir as bottom wall will be top wall of other cell for example.
                valid_dirs.remove(wall)  # remove wall, as not valid anymore

        self.dead_end_removal()

    ######## break_wall Method ########
    # Parameters:- current: self.Cell object, n_cell: self.Cell object, dire: string
    # Return type: n/a
    # Purpose: Breaks the wall between both cells by deleting specific directions for the cell and the adjacent cell
    ##########################
    def break_wall(self, current, n_cell, dire):
        n_cell_dire = self.n_dire[dire]
        del current.walls[dire]
        del n_cell.walls[n_cell_dire]

    ######## get_neighbours Method ########
    # Parameters:- cell: self.Cell object, deadend: boolean
    # Return type:- neighbors: list
    # Purpose: Returns a list of valid neighbours for either maze generation or for the removal of dead ends.
    ##########################
    def get_neighbours(self, cell, deadend):
        neighbours = []
        x = cell.pos[0]
        y = cell.pos[1]
        direct = {"N": ("N", x, y - 1), "E": ("E", x + 1, y),
                  "S": ("S", x, y + 1), "W": ("W", x - 1, y)}

        for cell_dire in cell.walls:  # as the maze is inverted in vertical dir's when displaying
            coord = direct[cell_dire]
            x = coord[1]
            y = coord[2]
            if 0 <= x <= self.length-1 and 0 <= y <= self.width-1: # if coords are valid
                if not deadend:  # used if not dead end removal, we need to only choose neighbours not yet visited
                    if self.maze[x][y].visited is not True:
                        neighbours.append(coord)
                else:  # if dead end removal, we need all 3 cells so we can break a random wall
                    neighbours.append(coord)
        return neighbours  # returns list of valid coords with their dir

    ######## main Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Initiates the generation of the maze and after the creation and removal of certain dead ends
    ##########################
    def main(self):
        current_cell = self.maze[self.root_node[0]][self.root_node[1]]
        self.stack.append(current_cell)
        self.generate(current_cell)


if __name__ == "__main__":
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    TEAL = (0, 128, 128)
    LIGHT_BLUE = (135, 206, 250)

    pygame.init()
    # while True:
    #     try:
    #         length = int(input("Choose the length of maze: "))
    #         width = int(input("Choose the width of maze: "))
    #         # size = int(input("Choose the size of each square: "))
    #         break
    #     except ValueError:
    #         print("The value entered must be an integer.")
    M = Maze(1)
    M.main()
    s = pygame.display.set_mode((700, 700))
    print(M.key_list, M.door)