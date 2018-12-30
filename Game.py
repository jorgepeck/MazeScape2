from PodSixNet.Connection import ConnectionListener, connection
import pygame
from pygame.locals import *  # imports constants like K_w or KEYDOWN and imports image stuff

from colours import *
from inputbox import inputbox
import A_Star_Search

pygame.init()
pygame.font.init()
clock = pygame.time.Clock()



######## Cell Class ########
# Parameters:- xpos: integer, ypos: integer, size: integer
# Return type:- n/a
# Purpose: A class representing a cell of the maze. Has attributes and a method used to set the cells info once data has
# been recieved from server.
##########################
class Cell:
    def __init__(self, xpos, ypos, size):
        self.walls = None
        self.visited = False
        self.pos = (xpos, ypos)

        self.xpos = xpos
        self.ypos = ypos
        self.s = size
        self.pixelpos = None

        self.rect = None
        self.point_list = None
        # both have to be sent over network, therefore, kepts as a string representation first and converted client side


    ######## give_minfo Method ########
    # Parameters:- dict_arr: dictionary
    # Return type:- n/a
    # Purpose: With the info give from the server, the attributes are set
    ##########################
    def give_minfo(self, dict_arr):
        self.walls = dict_arr["walls"]
        self.visited = dict_arr["visited"]
        self.pos = tuple(dict_arr["pos"])  # json serialises tuples as lisets
        self.pixelpos = dict_arr["pixelpos"]

        self.rect = pygame.Rect(self.s*self.xpos, self.s*self.ypos, self.s, self.s)
        self.point_list = {"N": [self.rect.topleft, self.rect.topright],
                           "E": [self.rect.topright, self.rect.bottomright],
                           "S": [self.rect.bottomright, self.rect.bottomleft],
                           "W": [self.rect.topleft, self.rect.bottomleft]}


######## Maze Class ########
# Parameters:- n/a
# Return type:- n/a
# Purpose: Contains the maze and the information about it
##########################
class Maze:
    def __init__(self):
        self.maze = None
        self.root_node = None
        self.root_rect = None

        self.length = 0
        self.width = 0
        self.size = 0

    ######## deconstruct_maze_dict Method ########
    # Parameters:- dict_arr: dictionary
    # Return type:- n/a
    # Purpose: Sets information for each cell in the maze with the data given from the server
    ##########################
    def deconstruct_maze_dict(self, dict_arr):
        for x in range(self.length):
            for y in range(self.width):
                c = self.maze[x][y]
                c.give_minfo(dict_arr[x][y])

    ######## give_info Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sets information about the maze using the data given from the server. Also creates an array of the maze.
    ##########################
    def give_info(self, data):
        self.length = data["length"]
        self.width = data["width"]
        self.size = data["size"]
        self.root_node = tuple(data["root_node"])  # json doesnt recognise tuples, so gives lists, so converting back
        self.root_rect = pygame.Rect(self.size*self.root_node[0], self.size*self.root_node[1], self.size, self.size)
        self.maze = [[Cell(x, y, self.size) for y in range(self.width)] for x in range(self.length)]

        self.deconstruct_maze_dict(data["maze"])


######## Player Class ########
# Parameters:- pos: integer, col: tuple, name: string
# Return type:- n/a
# Purpose: Contains information about the player.
##########################
class Player(pygame.sprite.Sprite):  # extends the methods of sprite into our class
    def __init__(self, pos, col, name):
        super().__init__()  # extends the attributes of sprite class into player class
        self.colour = col
        self.image = pygame.Surface([21, 21])
        self.image.fill(col)
        self.rect = self.image.get_rect(topleft=pos)
        self.name = name


######## Enemy Class ########
# Parameters:- pos: integer, col: tuple
# Return type:- n/a
# Purpose: Contains the information of the enemy
##########################
class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, col):
        super().__init__()  # extends the attributes of sprite class into player class
        self.colour = col
        self.image = pygame.Surface([21, 21])
        self.image.fill(col)
        self.rect = self.image.get_rect(topleft=pos)

        self.speed = None

        self.route = None
        self.pos_dict = None

        self.width = None
        self.length = None
        self.maze = None
        self.chase_alg = None

    ######## set_attributes Method ########
    # Parameters:- maze: list, width: integer, length: integer
    # Return type:- n/a
    # Purpose: Sets attributes related to the maze. Also setups the chase algorithm
    ##########################
    def set_attributes(self, maze, width, length):
        self.width = width
        self.length = length
        self.maze = maze
        self.chase_alg = A_Star_Search.Search(maze, width, length)

    ######## chase Method ########
    # Parameters:- player_pos: tuple, following: boolean
    # Return type:- n/a
    # Purpose: Makes a route from the player to the enemy, for the enemy to move along, using the A* search algorithm
    ##########################
    def chase(self, player_pos, following):  # following is used where the initial route is mapped out, and we are
        # only extending the route from the last pos in the initial route to the player.
        ppos = (player_pos[0] // 25, player_pos[1] // 25)
        if following:
            epos = (self.rect.topleft[0] // 25, self.rect.topleft[1] // 25)
            self.route = (self.chase_alg.main(ppos, epos))  # not an efficient way, as we are computing a new route each
            # time, but is quick enough for the game
        else:
            epos = (self.rect.topleft[0] // 25, self.rect.topleft[1] // 25)
            self.route = self.chase_alg.main(ppos, epos)

    ######## run Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Will only run after certain time intevals, to simulate a certain speed. Sets the enemies coordinates to
    # the next cell in the route to the player, and removes the cell from the route.
    ##########################
    def run(self):
        place = self.route[0]  # next place to goto
        self.rect.topleft = (place.rect.topleft[0] + 3, place.rect.topleft[1] + 3)  # moves enemy one step. +3 align pos
        self.route.remove(place)  # deletes that step from route


######## Key Class ########
# Parameters:- pos: tuple
# Return type:- n/a
# Purpose: Contains a rect and image for a key. Represented as a class due to the needs of pygames sprite groups
##########################
class Key(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos  # used to send over server
        self.image = pygame.image.load("key.png").convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)


######## Door Class ########
# Parameters:- pos: tuple
# Return type:- n/a
# Purpose: Contains various attributes for the door object.
##########################
class Door(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.open = False
        self.pos = pos

        self.door_closed_image = pygame.image.load("door_closed.png").convert_alpha()
        self.door_open_image = pygame.image.load("door_open.png").convert_alpha()
        self.image = self.door_closed_image
        self.rect = self.image.get_rect(topleft=pos)

    ######## switch_image Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Switches images of the door from closed to open, therefore creates a new rect.
    ##########################
    def switch_image(self):
        self.image = self.door_open_image
        self.rect = self.image.get_rect(topleft=self.pos)
        self.open = True


######## Mazescape Class ########
# Parameters:- screen: pygame.Surface object
# Return type:- n/a
# Purpose: The main holder for the games attributes and methods.
##########################
class Mazescape(ConnectionListener, pygame.sprite.Sprite):
    def __init__(self, screen):
        super(Mazescape, self).__init__()
        self.name = None
        self.vacant_games = []
        self.c_type = None

        self.screen = screen
        self.menu_button = pygame.Rect(300, 300, 150, 30)
        self.continue_button = pygame.Rect(300, 400, 150, 30)
        self.win_button = pygame.Rect(600, 100, 30, 30)

        self.running = True
        self.state = None
        self.win = None
        self.level = None
        self.score = None
        self.temp_score = 0

        self.p_id = None
        self.gameid = None
        self.userNum = None
        self.name_confirm = None

        self.init_time = 0
        self.milliseconds = 0
        self.seconds = 0
        self.minutes = 2  # 2 mins of play
        self.enemy_tick = None
        self.wait_tick = None

        self.player = None
        self.enemy = None
        self.other_player = None
        self.other_player_name = None
        self.other_enemy = None

        self.door = None

        self.M = None

        self.players_alive = 2
        self.players_out = 0

        self.keys_group = pygame.sprite.Group()
        self.door_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.player_group = pygame.sprite.Group()

        self.normal_font = pygame.font.SysFont("Calibri", 16)

# All Network_ methods are called from the server.

    ######## Network_connected Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Is called once there is a successful connection to the server.
    ##########################
    def Network_connected(self, data):
        print("You are now connected to the server")

    ######## Network_room_full_disconnect Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Is called when the server has more than 10 connections, prompting the game to quit and return to menu
    ##########################
    def Network_room_full_disconnect(self, data):
        connection.Send({"action": "room_full_close", "id": data["id"]})
        self.state = None

    ######## Network_get_id Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sets the clients id set by server. Sends message back to give name and connection type(join game or new
    # game)
    ##########################
    def Network_get_id(self, data):
        self.p_id = data["id"]
        connection.Send({"action": "give_info", "c": self.c_type, "name": self.name, "id": self.p_id})

    ######## Network_game_slots Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Makes each name in the list of room avalilble a rect object, and adding it to a list.
    ##########################
    def Network_game_slots(self, data):
        n_players = data["players"]
        y = 10
        self.vacant_games = []
        for key in n_players:  # for each tuple .. (player id, name), creates surface and makes rect
            text_surf = self.normal_font.render(n_players[key][1], False, BLACK)
            self.vacant_games.append([*n_players[key], text_surf, text_surf.get_rect(topleft=(20, y))])
            y += 15

    ######## Network_wait Method ########
    # Parameters:-
    # Return type:-
    # Purpose:
    ##########################
    def Network_wait(self, data):
        self.state = "wait"
        self.other_player_name = data["name"]
        self.gameid = data["gameid"]
        self.wait_tick = pygame.time.get_ticks()

    ######## Network_sendStartinginfo Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sets information given by server for the whole game.
    ##########################
    def Network_send_game_info(self, data):
        ppos = (3 if self.userNum is 1 else 478, 3)
        self.player = Player(ppos, data["colour"], self.name)

        epos = (3 if self.userNum is 1 else 478, 478)
        self.enemy = Enemy(epos, data["e_col"])
        self.enemy.speed = data["e_speed"]

        self.other_player = Player(data["o_p_coords"], data["o_col"], data["o_name"])
        self.other_enemy = Enemy(data["o_e_coords"], data["oe_col"])  # right below other_player

        self.level = data["level"]
        self.score = data["score"]

        self.M = Maze()
        self.M.give_info(data)

        for key_pos in data["key_list"]:
            konex, koney = key_pos  # a tuple
            k1x, k1y = self.M.maze[konex][koney].pixelpos  # gets pixels
            k1x, k1y = k1x + 3, k1y + 3  # adds 3 as it will not fill the whole square, gives some room on each side.
            # The image is 21 by 21 pixels so it will then fit
            key = Key((k1x, k1y))
            self.keys_group.add(key)

        dx, dy = data["door"]
        doorx, doory = self.M.maze[dx][dy].pixelpos  # convert from maze index to pixels
        doorx, doory = doorx + 3, doory + 3  # image is 21 by 21 so centered by adding 3 to each side
        self.door = Door((doorx, doory))

        self.player_group.add(self.player, self.other_player)
        self.enemy_group.add(self.enemy, self.other_enemy)
        self.door_group.add(self.door)

        self.enemy.set_attributes(self.M.maze, self.M.width, self.M.length)
        self.enemy.chase((self.player.rect.x, self.player.rect.y), False)

        self.state = "game"

        self.init_time = pygame.time.get_ticks()  # sets the timer

    ######## Network_move Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Receives coordinates of the other player, and replaces the old coordinates
    ##########################
    def Network_move(self, data):
        op_pos = (data["x"], data["y"])
        self.other_player.rect.topleft = op_pos

    ######## Network_enemy_move Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Recieves the coordinates of the enemy, and sets it to the other enemy class
    ##########################
    def Network_enemy_move(self, data):
        oe_pos = (data["x"], data["y"])
        self.other_enemy.rect.topleft = oe_pos

    ######## Network_key_collide Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: If the other player collects a key, this is called, to remove key from group, and so it
    ##########################
    def Network_key_collide(self, data):
        keypos = tuple(data["key"])  # as pos attribute is also tuple
        for key in self.keys_group:
            if key.pos == keypos:
                if self.keys_group.has(key):  # in case client has collected the key already
                    self.keys_group.remove(key)

        if data["door_open"]:
            self.door.switch_image()

    ######## Network_door_collide Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Removes other player and the other enemy from display as the player exits the door
    ##########################
    def Network_door_collide(self, data):
        self.player_group.remove(self.other_player)
        self.enemy_group.remove(self.other_enemy)
        self.players_out += 1

    ######## Network_player_kill Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Removes other player and enemy from display as the other player is killed
    ##########################
    def Network_player_kill(self, data):
        self.player_group.remove(self.other_player)
        self.enemy_group.remove(self.other_enemy)
        self.players_alive -= 1

    ######## Network_clear Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Resets the attributes used for the game, in the case the other client wants to carry on to the next level
    ##########################
    def Network_clear(self, data):  # Only called if the player is the joiner, as the other player would reset their
        # values their end, as they specify as to continuing to the next level.
        score = self.score  # we delete current score, but keep as temp as we add on to total in next game
        self.clear_values()
        self.temp_score = score

    # def Network_get_score(self, data):
    #     self.score += data["score"]

    def Network_inst_win(self, data):
        self.win = True

    ######## Network_get_names Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Recieves the names from the score list, to ensure name entered client side is not taken.
    ##########################
    def Network_get_names(self, data):
        name_lst = data["names"]
        self.end_game(name_lst)

    ######## Network_quit Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Returns the player to the main menu, after either finishing the game or due to a disconnection of the
    # other player during gameplay.
    ##########################
    def Network_quit(self, data):
        self.state = None  # menu will take care of the rest in the check game screen method
        connection.Send({"action": "close_signal", "gameid": self.gameid, "id": self.p_id, "userNum": self.userNum})

    ######## server_conn Method ########
    # Parameters:- c_type: string
    # Return type:- n/a
    # Purpose: Asks the user for a name. Connects the player to the server and then switches the screen to the game
    # selection screen.
    ##########################
    def server_conn(self, c_type):
        w = False
        warning = self.normal_font.render("Please enter a name", 1, WHITE)

        while True:
            self.screen.fill(TEAL)

            if w:
                self.screen.blit(warning, (300, 10))

            name = inputbox.ask(self.screen, "Enter Your Name", TEAL)
            if len(name) is 0:
                w = True
            else:
                self.name = name
                break

        self.c_type = c_type
        port = 31425
        host = "localhost"

        self.userNum = 1 if self.c_type == "new" else 2

        self.Connect((host, port))

        self.state = "selection"

    ######## game_loop Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Calls methods related to gameplay. Is called continuously from the menu top level loop.
    ##########################
    def game_loop(self):
        self.timer_tick()
        if self.player in self.player_group:
            self.enemy_run()
        self.collisions()
        self.score = self.calc_score()
        self.win_lose_check()

    ######## timer_tick Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Controls how much time passes for each game loop, to keep track of time to be displayed.
    ##########################
    def timer_tick(self):
        self.milliseconds += pygame.time.get_ticks() - self.init_time  # time elapsed since last loop.
        # calcs how many seconds and mins there has been since last tick
        if self.milliseconds > 1000:  # every 1000 ms the seconds go down by 1
            self.seconds -= 1
            self.milliseconds -= 1000  # take the 1000 off the total and so restarts at 0
        if self.seconds < 0:  # every time seconds go down past 0, add 60 back on and decrease mins by 1
            self.minutes -= 1
            self.seconds += 60

        self.init_time = pygame.time.get_ticks()

    ######## calc_score Method ########
    # Parameters:- n/a
    # Return type:- score: integer
    # Purpose: Calculates score using current time elapsed, players alive, and the level the players are on
    ##########################
    def calc_score(self):
        time_left = self.seconds + (self.minutes * 60)
        score = self.players_alive * ((time_left // 2) + (50 * self.level)) + self.temp_score  # temp score is score from
        return score  # last game

    ######## collsions Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Detects collisions between the player and the key, enemy or door. Sends a message to the other client if
    # a collision does happen
    ##########################
    def collisions(self):
        for key in self.keys_group:
            if pygame.sprite.collide_rect(key, self.player):
                self.keys_group.remove(key)
                if len(self.keys_group) is 0:  # controls door if no keys are left
                    self.door.switch_image()
                    self.door.open = True
                connection.Send({"action": "key_collide", "key": key.pos, "gameid": self.gameid,
                                 "player": self.userNum, "door_open": self.door.open})  # client key by matching pos

        if pygame.sprite.collide_rect(self.player, self.door) and self.door.open and self.player_group.has(self.player):
            # collision detection carries on even if player is dead and not blitted, so last part prevents statement
            # from running in that case.
            self.player_group.remove(self.player)
            self.enemy_group.remove(self.enemy)
            connection.Send({"action": "door_collide", "gameid": self.gameid, "player": self.userNum})
            self.players_out += 1

        elif pygame.sprite.collide_rect(self.player, self.enemy or self.other_enemy) \
                and self.player_group.has(self.player):
            # collision detection will carry on even if player is dead and not blitted, so we check if player is dead
            self.player_group.remove(self.player)
            self.enemy_group.remove(self.enemy)
            connection.Send({"action": "player_kill", "gameid": self.gameid, "player": self.userNum})
            self.players_alive -= 1

    ######## move Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: If a move key is pressed, checks if direction moving in is valid, as in no walls block player, and if
    # valid, changes players coordinates and sends other player message that the other player has moved
    ##########################
    def move(self):
        pressed_keys = pygame.key.get_pressed()
        dirs = {K_w: ((0, -25), "N"),
                K_s: ((0, 25), "S"),
                K_a: ((-25, 0), "W"),
                K_d: ((25, 0), "E")}

        for dire in dirs:
            if pressed_keys[dire] and not self.wall_collision(dirs[dire][1]):
                self.player.rect.move_ip(dirs[dire][0][0], dirs[dire][0][1])  # move in place, no copy of rect made.
                connection.Send({"action": "move", "gameid": self.gameid, "player": self.userNum,
                                 "x": self.player.rect.x, "y": self.player.rect.y})
                self.enemy.chase((self.player.rect.x, self.player.rect.y), True)  # used to extend route

    ######## enemy_run Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Moves the enemy along its route, only if a certain time has elapsed since last movement. Sends message to
    # other player that the enemy has moved
    ##########################
    def enemy_run(self):
        if len(self.enemy.route) is 0:  # if nowhere to go, assume player is caught and enemy gone. added for robustness
            pass
        elif self.enemy_tick is None:  # first time moving
            self.enemy_tick = pygame.time.get_ticks()
            self.enemy.run()
        else:
            time_elapsed = pygame.time.get_ticks() - self.enemy_tick
            if time_elapsed >= self.enemy.speed:  # if time elasped is a certain milliseconds long.
                self.enemy.run()
                self.enemy_tick = pygame.time.get_ticks()  # sets time to find the difference on next loop to see time
                connection.Send({"action": "enemy_move", "gameid": self.gameid, "player": self.userNum,
                                 "x": self.enemy.rect.x, "y": self.enemy.rect.y})  # sends message to other player that
                # the enemy has moved.

    ######## wall_collision Method ########
    # Parameters:- dire: string
    # Return type:- True, False: boolean
    # Purpose: Checks if direction the player moves in is not obstructed by a wall
    ##########################
    def wall_collision(self, dire):
        current_coord = self.player.rect.topleft
        cell_pos = (((current_coord[0] - 3) // 25), ((current_coord[1] - 3) // 25))  # div by 25 so can search in array
        current_cell = self.M.maze[cell_pos[0]][cell_pos[1]]
        try:
            current_cell.walls[dire]
        except LookupError:
            return False
        return True

    ######## win_lose_check Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Checks if certain conditions are met from game play, and if so, will set win to true/false, prompting
    # game to end.
    ##########################
    def win_lose_check(self):
        if self.players_alive is 0:  # both players dead
            self.win = False

        elif self.players_out == 2:  # both players are through the door
            self.win = True

        elif self.players_out == 1 and self.players_alive == 1:  # one player is out, one player is dead
            self.win = True

        elif self.minutes < 0:  # if time runs out before both players get out, they lose
            if self.players_out == 0:  # In the case that a player gets out
                self.win = False  #

        if self.win is not None:  # implying it has been set to true or false, we can end game. No need to put this code
            self.state = "finish"  # into each if statement above.

    ######## next_game Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: If player 1 decides to continue to the next level, attributes are cleared and server is notified to start
    # the next level.
    ##########################
    def next_game(self):  # only called through player 1, the client who made the new game. player 2 is notified from
        # server.
        self.state = "pending"  # blank screen while server makes maze and sends all the game data

        self.temp_score = self.score

        connection.Send({"action": "finish", "gameid": self.gameid, "player": self.userNum,
                         "cont": True, "score": self.temp_score})

        self.clear_values()

    ######## end_game Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: If player 1 decides to end game after playing, asks for a valid 3 digit name (actually 3 digits and not
    # taken), and sends signal to server to end game and update high score list.
    ##########################
    def end_game(self, names):
        m = False
        w = False
        warning = self.normal_font.render("It has to be 3 digits", 1, WHITE)
        taken = self.normal_font.render("Name is already taken", 1, WHITE)

        while True:
            self.screen.fill(TEAL)

            if m:
                self.screen.blit(taken, (300, 30))
            if w:
                self.screen.blit(warning, (300, 10))

            high_score_name = inputbox.ask(self.screen, "Enter a 3 digit name", TEAL)
            if len(high_score_name) is 3:
                if high_score_name not in names:
                    break
                else:
                    m = True
            else:
                w = True  # if we blit now, bg will blit over and it will cover up

        connection.Send({"action": "finish", "gameid": self.gameid, "player": self.userNum,
                         "cont": False, "score": self.score, "name": high_score_name})

        self.state = "pending"

    ######## clear_values Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Resets attributes for next game
    ##########################
    def clear_values(self):
        self.win = None
        self.level = None

        self.init_time = 0
        self.milliseconds = 0
        self.seconds = 0
        self.minutes = 2
        self.enemy_tick = None
        self.wait_tick = None
        self.score = 0

        self.player = None
        self.enemy = None
        self.other_player = None
        self.other_enemy = None

        self.door = None
        self.M = None

        self.players_alive = 2
        self.players_out = 0

        self.keys_group.empty()
        self.door_group.empty()
        self.enemy_group.empty()
        self.player_group.empty()

    ######## selection_screen Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Contains blit and draw statements to display buttons and text.
    ##########################
    def selection_screen(self):
        self.screen.fill(WHITE)
        if self.c_type == "join":
            text = self.normal_font.render("Choose a player to make a game with", 1, BLACK)
            self.screen.blit(text, (300, 0))
            x = 10
            for players in self.vacant_games:
                surface = players[2]
                rect = players[3]
                self.screen.blit(surface, rect.topleft)
                x += 15

        elif self.c_type == "new":
            text = self.normal_font.render("Waiting for player", 1, BLACK)
            self.screen.blit(text, (300, 0))

    ######## wait_screen Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Displays the other players name and counts down from 5 to 0 where then the game begins.
    ##########################
    def wait_screen(self):
        self.screen.fill(LIGHT_BLUE)

        if self.c_type == "new":
            text = self.normal_font.render(str("player found: " + self.other_player_name), 1, BLACK)
            self.screen.blit(text, (300, 0))
        elif self.c_type == "join":
            text = self.normal_font.render(str("playing with: " + self.other_player_name), 1, BLACK)
            self.screen.blit(text, (300, 0))

        time = pygame.time.get_ticks() - self.wait_tick
        time_text = self.normal_font.render(str(5 - time // 1000), 1, BLACK)
        self.screen.blit(time_text, (300, 300))

        if time >= 5000 and self.userNum is 1:  # if 5 seconds have passed.
            connection.Send({"action": "begin", "gameid": self.gameid})
            self.state = "pending"

    ######## game_screen Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Displays the whole of the game screen.
    ##########################
    def game_screen(self):
        self.screen.fill(TEAL)
        self.display_maze()

        text = self.normal_font.render("Player " + str(self.userNum), 1, BLACK)
        self.screen.blit(text, (600, 10))
        time = self.normal_font.render("Time Left: " + str(self.minutes) + ":" + str(self.seconds), 1, BLACK)
        self.screen.blit(time, (675, 10))
        level = self.normal_font.render("Level " + str(self.level) + "Speed: " + str(self.enemy.speed), 1, BLACK)
        self.screen.blit(level, (600, 30))
        score = self.normal_font.render("Score: " + str(self.score), 1, BLACK)
        self.screen.blit(score, (600, 50))

        pygame.draw.rect(self.screen, WHITE, self.win_button)

        if self.player_group.has(self.player):
            self.draw_path()

        self.keys_group.draw(self.screen)
        self.door_group.draw(self.screen)
        self.player_group.draw(self.screen)
        self.enemy_group.draw(self.screen)

    ######## finish_screen Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Displays the win or lose screen, with buttons to continue to next level or to return to menu.
    ##########################
    def finish_screen(self):
        win = self.normal_font.render("You Win", 1, BLACK)
        game_over = self.normal_font.render("Game Over", 1, BLACK)
        score = self.normal_font.render("Your score is: " + str(self.score), 1, BLACK)
        carry_on = self.normal_font.render("Continue to next level", 1, BLACK)
        finish = self.normal_font.render("Finish Game", 1, BLACK)

        if self.win:
            self.screen.fill(GREEN)
            self.screen.blit(score, (300, 200))
            self.screen.blit(win, (300, 10))

            if self.userNum is 1:  # only p1 decides as the host
                pygame.draw.rect(self.screen, TEAL, self.continue_button)
                self.screen.blit(carry_on, (300, 400))

                pygame.draw.rect(self.screen, TEAL, self.menu_button)
                self.screen.blit(finish, (300, 300))
        else:
            self.screen.fill(RED)
            self.screen.blit(score, (300, 200))
            self.screen.blit(game_over, (300, 10))

            if self.userNum is 1:  # only p1 decides as the host
                pygame.draw.rect(self.screen, TEAL, self.menu_button)
                self.screen.blit(finish, (300, 300))

    ######## waiting Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: A white screen shown when pending information from server
    ##########################
    def waiting(self):
        self.screen.fill(WHITE)

    ######## display_maze Method ########
    # Parameters:- screen: pygame.Surface object
    # Return type:- n/a
    # Purpose: Used to display the maze
    ##########################
    def display_maze(self):
        x_coord = -1
        y_coord = -1
        for x in range(self.M.length):
            x_coord += 1
            for y in range(self.M.width):
                y_coord += 1
                pygame.draw.rect(self.screen, WHITE, self.M.maze[x][y].rect)
                for dire, torf in self.M.maze[x][y].walls.items():
                    line_coord = self.M.maze[x][y].point_list[dire]
                    pygame.draw.line(self.screen, BLACK, line_coord[0], line_coord[1], 2)
            y_coord = -1

    ######## draw_path Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Displays a path through cells from the enemy to the player
    ##########################
    def draw_path(self):
        try:
            prev = self.enemy.route[0].rect.center  # first point is preset
            for point in self.enemy.route:  # all points in route
                curr = point.rect.center
                coords = [prev, curr]
                pygame.draw.line(self.screen, GREEN, coords[1], coords[0], 2)
                prev = curr
        except IndexError:  # for situations where there is no path, such that self.enemy.route = [], therefore cannot
            pass  # use indexing

    ######## event_loop Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Dependent on the state, different events are checked, such as mouse clicks with buttons, or if the window
    # closes.
    ##########################
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                connection.Send({"action": "manual_disconnect", "gameid": self.gameid, "player": self.userNum})

                connection.Pump()
                self.Pump()

                self.running = False
                exit()

            if event.type == KEYDOWN:
                if self.state == "game":
                    if self.player in self.player_group:  # if not dead
                        self.move()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # could use switch case with dict, but not much speed difference.
                if self.state == "game":
                    if self.win_button.collidepoint(*mouse_pos):
                        self.win = True
                        connection.Send({"action": "inst_win", "gameid": self.gameid, "player": self.userNum})

                elif self.state == "finish":
                    if self.continue_button.collidepoint(*mouse_pos) and self.win is True:  # player wants to carry on
                        self.next_game()
                    elif self.menu_button.collidepoint(*mouse_pos):  # player decides to quit
                        connection.Send({"action": "get_names", "id": self.p_id})

                elif self.state == "selection":
                    for player in self.vacant_games:  # list of players with surfaces
                        if player[3].collidepoint(*mouse_pos):
                            connection.Send({"action": "start", "p1_id": player[0], "p2_id": self.p_id})

    ######## loop Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Called from menu top level loop. Collates each method call into a single method.
    ##########################
    def loop(self):
        self.event_loop()
        if self.state == "game":  # if game is started
            self.game_loop()

        connection.Pump()  # sends messages
        self.Pump()  # recieves messages
