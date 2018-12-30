######### Search Class ########
# Parameters:- maze: list, width: integer, length: integer
# Return type:- n/a
# Purpose: Contains the attributes and methods for the A* Search algorithm
###############################
class Search:
    def __init__(self, maze, width, length):
        self.maze = maze
        self.end = None
        self.start = None
        self.reached = False

        self.length = length
        self.width = width

        self.open_list = []
        self.closed_list = []
        self.just_started = True

        self.route = []

    ######## search Method ##########
    # Parameters:- current: MazeGen.Cell object
    # Return type:- n/a
    # Purpose: Checks var current if it is the goal node or not. If not, it will get next best node to traverse and
    # starts again
    #################################
    def search(self, current):
        if current is None:  # this is in the case there is an enclosed area which cant be traversed
            print("No route available")
            return
        else:
            if current.pos == self.end:
                self.retrace_route(current)
                self.reached = True
            else:
                neighbours = self.find_neighbours(current)  # find connected nodes to current

                self.add_open_l(neighbours, current)  # adds to open list
                self.open_list.remove(current)
                self.closed_list.append(current)

                self.search(self.find_lowest_f_score())  # recursive function

    ######## add_open_l Method ########
    # Parameters:- neighbours: list, current: MazeGen.Cell object
    # Return type:- n/a
    # Purpose: Will iterate though neighbour nodes and will calculate their g and h score to make a tentative f score,
    # to determine if node is usable in traversing the maze. If so adds it to the open list.
    ###################################
    def add_open_l(self, neighbours, current):
        for cell in neighbours:
            g = calc_dist_of_path(cell, current)  # distance so far if node is used
            h = calc_heuristic(cell, self.end)  # distance of node to goal
            tentative_f = h + g

            if cell in self.open_list:  # if in open list
                if cell.f_score >= tentative_f:  # can check if this neighbour is
                    cell.f_score = tentative_f  # tentative_f as we dont know if cell in open list has a
                    cell.parent = current  # better f score or not yet

            elif cell not in [*self.open_list, *self.closed_list]:  # unpack as one list
                cell.g_score = g
                cell.h_score = h
                cell.f_score = tentative_f
                cell.parent = current
                self.open_list.append(cell)

    ######## find_lowest_f_score Method ########
    # Parameters:- n/a
    # Return type:- None, curr[1]: MazeGen.Cell object
    # Purpose: Will find and return the cell which has the lowest f score in a list
    ############################################
    def find_lowest_f_score(self):
        if self.just_started:  # only one cell in open list so
            curr = self.open_list[0]
            self.just_started = False
            return curr
        else:
            if len(self.open_list) == 0:
                return None
            else:
                curr = (1000000, None)  # placeholder for first comparison
                for cell in self.open_list:
                    if cell.f_score <= curr[0]:
                        curr = (cell.f_score, cell)
                return curr[1]

    ######## find_neighbours Method ########
    # Parameters:- cell: MazeGen.Cell object
    # Return type:- n/a
    # Purpose: Locates the valid neighbouring nodes of the cell passed in
    ##########################
    def find_neighbours(self, cell):
        neighbours = []
        wall = ["N", "E", "S", "W"]
        x = cell.pos[0]
        y = cell.pos[1]
        direct = {"N": (x, y - 1), "E": (x + 1, y), "S": (x, y + 1),
                  "W": (x - 1, y)}

        for cell_dire in cell.walls:  # removes walls from list according to walls on cell to get list of dirs with no
            # walls
            wall.remove(cell_dire)

        for dire in wall:
            adj_cell = self.maze[direct[dire][0]][direct[dire][1]]
            if 0 <= adj_cell.pos[0] <= self.length-1 and 0 <= adj_cell.pos[1] <= self.width-1:# if coords aren't out of
                # bounds, can add as neighbour
                    neighbours.append(adj_cell)

        return neighbours  # returns list of valid coords with their dir

    ######## retrace_route Method ########
    # Parameters:- current: MazeGen.Cell object
    # Return type:- n/a
    # Purpose: Will retrace the route from the final cell to the first cell by using the parent attribute each cell has
    ##########################
    def retrace_route(self, current):
        if current.pos != self.start:
            self.route.append(current)  # append cell to route
            self.retrace_route(current.parent)  # recursion. use next cell in route to append next loop
        else:
            self.route.append(current)  # if the point is the end, we append the end and end the recursive loop

    ######## main Method ########
    # Parameters:- start: tuple, end: tuple
    # Return type:- None, self.route: list
    # Purpose: Determines if A* search is needed to find route or not, and if so, will set attributes and start the
    #          search
    ##########################
    def main(self, start, end):
        if start == end:
            return None
        else:
            # initial setting of attributes for the first cell to be traversed
            # all later nodes have this calculated as part of searching for lowest f score
            i_curr = self.maze[start[0]][start[1]]  # initial current
            i_curr.h_score = calc_heuristic(i_curr, end)
            i_curr.g_score = 1
            i_curr.parent = i_curr
            i_curr.f_score = i_curr.h_score + i_curr.g_score

            self.end = end
            self.start = start
            self.open_list = [i_curr]
            self.closed_list = []
            self.just_started = True
            self.route = []

            self.search(i_curr)

            return self.route

######## calc_heurisic function ########
# Parameters:- cell: MazeGen.Cell object, end: tuple
# Return type:- integer
# Purpose: Calculates and estimate distance of two points passed in in manhattan distance
##########################
def calc_heuristic(cell, end):
    return abs(cell.pos[0] - end[0]) + abs(cell.pos[1] - end[1])  # using manhattan distance

######## calc_dist_of_path function ########
# Parameters:- cell: MazeGen.Cell object, prev: MazeGen.Cell object
# Return type:- integer
# Purpose: Calculates the distance of the route so far given we use the var cell as the next step of the route
##########################
def calc_dist_of_path(cell, prev):
    return (abs(prev.pos[0] - cell.pos[0])
            + abs(prev.pos[1] - cell.pos[1])  # dist from last node
            + prev.g_score)  # plus dist of last node from last node, so will continue until root
