from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from random import randint
from time import sleep
import MazeGen
import Scoring

# send method of class edited so JSON serialised, not rencode
# json doesnt recognise tuples, so will sends a lists. need to convert at other end, client or server.


######## Player Class ########
# Parameters:- channel: ClientChannel object, p_id: integer, name: string, c_type: string
# Return type:- n/a
# Purpose: Stores attributes for each player.
##########################
class Player:
    def __init__(self, channel, p_id, name, c_type):
        self.channel = channel
        self.p_id = p_id
        self.c_type = c_type
        self.name = name


######## ClientChannel Class ########
# Parameters:- n/a
# Return type:- n/a
# Purpose: Contains the methods which can be called from the client, using PodSixNet and ascyncore
##########################  # inheritance of Channel
class ClientChannel(Channel):  # representation of a client connection
    def __init__(self, *args, **kwargs):  # unpacks all parameters, unknown or not
        super().__init__(*args, **kwargs)

    ######## get_client Method ########
    # Parameters:- gameid: integer, p: string
    # Return type:- self.Player object
    # Purpose: Returns the other client of the 2 player game, given the var p.
    ##########################
    def get_client(self, gameid, p):
        p = "p2" if p is 1 else "p1"  # player number 1 is p1. player number 2 p2. so here chooses opposite player for
        player = self._server.games_dct[gameid][p]  # given player number
        return player

    ######## Network_room_full_close Method ########
    # Parameters:- data: dictionary
    # Return type:- a/n
    # Purpose: Will receive the 'okay' message to close the connection to the clients channel, after the server has sent
    # the close message. It reads the clients current channel and closes it.
    ##########################
    def Network_room_full_close(self, data):
        client = self._server.players[data["id"]]
        # client[0].close()  # index 0 is channel

    ######## Network_menu Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: To call another method to send the scores to the client
    ##########################
    def Network_menu(self, data):  # if menu wants to get db
        channel = self._server.players[data["p_id"]][0]
        self._server.menu_setup(channel)

    ######## Network_give_info Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: After id is send to client, client sends back id, name and connection type used for the setup of the game
    ##########################
    def Network_give_info(self, data):
        p_tup = self._server.players[data["id"]]
        channel = p_tup[0]
        self._server.game_setup(data["id"], channel, data["name"], data["c"])

    ######## Network_start Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Setup for the game, setting gameid and removing clients from lists.
    ##########################
    def Network_start(self, data):  # for first time, as score and level are 0 and 1 respectively. other levels start
        # through network_finish
        p1 = self._server.players[data["p1_id"]]  # p1 is always the player who creates a new game.
        p2 = self._server.players[data["p2_id"]]

        del self._server.joining_player_dict[p2.p_id]  # p2 always joins a game
        del self._server.new_player_dict[p1.p_id]  # p1 is always a player to create a game

        self._server.send_to_all_j_clients(({"action": "game_slots", "players": self._server.new_player_dict}))

        while True:
            gameid = randint(0, 1000)
            try:
                self._server.games_dct[gameid]
            except KeyError:  # if not used
                break

        self._server.games_dct[gameid] = {"p1": p1, "p2": p2, "score": 0, "level": 1}

        p1.channel.Send({"action": "wait", "name": p2.name, "gameid": gameid})
        p2.channel.Send({"action": "wait", "name": p1.name, "gameid": gameid})

    ######## Network_begin Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: After clients have waited 5 seconds from wait screen, sends a message to begin.
    ##########################
    def Network_begin(self, data):
        gameid = data["gameid"]
        p1 = self._server.games_dct[gameid]["p1"]
        p2 = self._server.games_dct[gameid]["p2"]
        self._server.begin(p1, p2, 0, 1)  # score and level

    ######## Network_move Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Send coordinates of one client to the other
    ##########################
    def Network_move(self, data):
        player = self.get_client(data["gameid"], data["player"])
        player.channel.Send({"action": "move", "x": data["x"], "y": data["y"]})

    ######## Network_enemy_move Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sends coordinates of enemy to the other client from one client.
    ##########################
    def Network_enemy_move(self, data):
        player = self.get_client(data["gameid"], data["player"])
        player.channel.Send({"action": "enemy_move", "x": data["x"], "y": data["y"] })

    ######## Network_key_collide Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sends message to remove collided key from one client to the other
    ##########################
    def Network_key_collide(self, data):
        player = self.get_client(data["gameid"], data["player"])
        player.channel.Send({"action": "key_collide", "key": data["key"], "door_open": data["door_open"]})

    ######## Network_door_collide Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sends message from one client to the other that the client has entered the door
    ##########################
    def Network_door_collide(self, data):
        player = self.get_client(data["gameid"], data["player"])
        player.channel.Send({"action": "door_collide"})

    ######## Network_player_kill Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sends message from one client to the other that the client has died.
    ##########################
    def Network_player_kill(self, data):
        player = self.get_client(data["gameid"], data["player"])
        player.channel.Send({"action": "player_kill"})

    ######## Network_finish Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Will setup for another level or to quit the game. For the next level, saves current score and increments
    # the level. For quitting, will send a message to quit game to both clients, and adds score to database.
    ##########################
    def Network_finish(self, data):
        other = self.get_client(data["gameid"], data["player"])

        cont = data["cont"]
        gameid = data["gameid"]
        game = self._server.games_dct[gameid]

        if cont:  # wants to carry on playing
            other.channel.Send({"action": "clear"})  # clears on player 2 side, as only has cleared for player 1.
            game["score"] += data["score"]  # tally score so far
            game["level"] += 1  # add 1 level
            self._server.begin(game["p1"], game["p2"], game["score"], game["level"])

        elif not cont:  # wants to quit
            p1 = game["p1"]
            p2 = game["p2"]

            p1.channel.Send({"action": "quit"})
            p2.channel.Send({"action": "quit"})  # sends p2 the quit signal

            Scoring.add_score(data["name"], data["score"])  # adds score to json db

            del self._server.games_dct[gameid]  # deletes game
            del self._server.players[p1.p_id]  # deletes players from lists
            del self._server.players[p2.p_id]

    ######## Method ########
    # Parameters:-
    # Return type:-
    # Purpose:
    ##########################
    def Network_inst_win(self, data):
        player = self.get_client(data["gameid"], data["player"])
        player.channel.Send({"action": "inst_win"})

    ######## Network_get_names Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sends a list of names to client to ensure name is not taken
    ##########################
    def Network_get_names(self, data):
        player = self._server.players[data["id"]]
        names = Scoring.get_names()
        player.channel.Send({"action": "get_names", "names": names})

    ######## Network_manual_disconnect Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sent from the client quitting unexpectedly. Will send a message to the other client to quit to menu.
    ##########################
    def Network_manual_disconnect(self, data):
        other_player = self.get_client(data["gameid"], data["player"])
        other_player.channel.Send({"action": "quit"})

    ######## Network_disconnect Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Disconnects client from server after accessing score table in menu.
    ##########################
    def Network_disconnect(self, data):  # for menu
        channel = self._server.players[data["id"]][0]
        # channel.close()
        del self._server.players[data["id"]]

    ######## Network_close_signal Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: After client quits and doesnt need network connection anymore, deletes the variables
    ##########################
    def Network_close_signal(self, data):
        id = data["id"]
        p = "p1" if data["userNum"] == 1 else "p2"
        player = self._server.games_dct[data["gameid"]][p]

        if len(self._server.games_dct[data["gameid"]]) is 1:  # deletes game only if other player has quit.
            del self._server.games_dct[data["gameid"]]

        del self._server.games_dct[data["gameid"]][p]  # deletes player from lists and dicts
        # player.channel.close()
        del self._server.players[id]


######## GameServer class ########
# Parameters:- n/a
# Return type:- n/a
# Purpose: Handles the methods called from the client for the server. Also contains own methods for setting up game
# connections and menu connections
##########################
class GameServer(Server):  # methods. inheritance though server
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # attributes
        print("Server started on LOCALHOST")
        self.games_dct = {}

        self.joining_player_dict = {}
        self.new_player_dict = {}
        self.players = {}

    ######## Connected Method ########
    # Parameters:- channel: ClientChannel object, addr: string
    # Return type:- n/a
    # Purpose: Called for each new client connection. Saves player in players dict, sets player id, and checks if server
    # is full or not and subsequently send a message to give id the client their id.
    ##########################
    def Connected(self, channel, addr):  # is called each time a new client connects to the server
        print("New Connection; ", channel, addr)
        while True:  # random id, not iteration
            p_id = randint(0, 1000)
            try:  # checks if used
                self.players[p_id]
            except KeyError:  # if not used
                break

        self.players[p_id] = (channel, p_id)

        if len(self.players) > 10:
            channel.Send({"action": "room_full_disconnect", "id": p_id})  # room full, send message to close screen, and
            # client sends back confirmation.
        else:
            channel.Send({"action": "get_id", "id": p_id})  # room is not full, so continue with setup

    ######## send_to_all_j_clients Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Sends all joining clients in the dictionary the data passed in
    ##########################
    def send_to_all_j_clients(self, data):
        for client in self.joining_player_dict.values():  # .values, not keys
            client.channel.Send(data)

    ######## menu_setup Method ########
    # Parameters:- channel: ClientChannel object
    # Return type:- n/a
    # Purpose: Is called from ClientChannel when the client sends a message to the server requesting for the score list
    ##########################
    def menu_setup(self, channel):
        score_list = Scoring.get_scores()
        channel.Send({"action": "give_scores", "scores": score_list})

    ######## game_setup Method ########
    # Parameters:- p_id: integer, channel: ClientChannel object, name: string, c_type: string
    # Return type:- n/a
    # Purpose: Called once the client requests to either join or make a new game. Adds client to respective list(new or
    # joining), and sets client as a player class in the players list.
    ##########################
    def game_setup(self, p_id, channel, name, c_type):
        player_class = Player(channel, p_id, name, c_type)
        self.players[p_id] = player_class  # adds new player class to dict of players

        if player_class.c_type == "new":
            self.new_player_dict[player_class.p_id] = (player_class.p_id, player_class.name)
            self.send_to_all_j_clients({"action": "game_slots", "players": self.new_player_dict}) # send all joining clients
            # an updated list of the new game clients.

        elif player_class.c_type == "join":
            self.joining_player_dict[player_class.p_id] = player_class
            player_class.channel.Send({"action": "game_slots", "players": self.new_player_dict})  # send new players list to
            # client

    ######## starting Method ########
    # Parameters:- p1: Player class, p2: Player class, gameid: integer, score: integer, level: integer
    # Return type:- n/a
    # Purpose: Creates the maze used for the game, as the set level/difficulty. Sends the clients the needed information
    # for the game screen, including a dict representation of each cell in the maze
    ##########################
    def begin(self, p1, p2, score, level):
        e_speed_dict = {1: 90, 2: 90, 3: 80, 4: 80, 5: 70}

        speed = 60 if level > 5 else e_speed_dict[level]  # the levels are endless, so in the case the level is > 8,
        # speed is kept to 25.
        m = MazeGen.Maze(level)
        m.main()

        simple_maze = [["" for _ in range(m.length)] for _ in range(m.width)]  # _ is unused var. Creates a empty array
        # representation of the final maze.

        for x in range(0, 20):
            for y in range(0, 20):
                obj = m.maze[x][y]
                simple_maze[x][y] = obj.__dict__  # turns each cell object to dict representation, as we cannot send
                # classes through the network.

        # sends all info
        p1.channel.Send({"action": "send_game_info", "maze": simple_maze, "length": m.length, "width": m.width,
                        "root_node": m.root_node, "size": m.size, "key_list": m.key_list, "door": m.door,
                         "o_name": p2.name, "colour": (0, 0, 255), "o_col": (255, 0, 0),
                         "e_col": (0, 0, 100), "oe_col": (100, 0, 0), "o_p_coords": (478, 3), "o_e_coords": (478, 478),
                         "level": level, "score": score, "e_speed": speed})

        p2.channel.Send({"action": "send_game_info", "maze": simple_maze, "length": m.length, "width": m.width,
                        "root_node": m.root_node, "size": m.size, "key_list": m.key_list, "door": m.door,
                         "o_name": p1.name, "colour": (255, 0, 0), "o_col": (0, 0, 255),
                         "e_col": (100, 0, 0), "oe_col": (0, 0, 100), "o_p_coords": (3, 3), "o_e_coords": (3, 478),
                         "level": level, "score": score, "e_speed": speed})

    ######## launch Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Will constantly loop self.Pump which checks for incoming messages, which the server will deal with using
    # the methods in ClientChannel
    ##########################
    def launch(self):
        while True:
            self.Pump()


######## main Method ########
# Parameters:- n/a
# Return type:- n/a
# Purpose: Sets up the server using the host and port specified.
##########################
def main():
    host, port = "localhost", 31425
    game_server = GameServer(localaddr=(host, int(port)))

    game_server.launch()


if __name__ == "__main__":
    main()
