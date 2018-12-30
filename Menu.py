from PodSixNet.Connection import ConnectionListener, connection
import pygame
import Game

from colours import *

pygame.init()
pygame.font.init()

width, height = 800, 600
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()


######## Menu Class ########
# Parameters:- n/a
# Return type:- n/a
# Purpose: Has all the attributes and method needed for the menu screens and is the top level loop, looping through the
# game if needed.
##########################
class Menu(ConnectionListener):  # Inheritance of connection listener, which includes pump, connect and send methods
    def __init__(self):
        self.running = True
        self.big_font = pygame.font.SysFont("Calibri", 64)
        self.normal_font = pygame.font.SysFont("Calibri", 32)
        self.small_font = pygame.font.SysFont("Calibri", 24)

        self.play_button = pygame.Rect(320, 150, 150, 30)
        self.quit_button = pygame.Rect(320, 200, 150, 30)
        self.score_button = pygame.Rect(320, 250, 150, 30)
        self.back_button = pygame.Rect(700, 500, 60, 25)
        self.join_game_button = pygame.Rect(200, 300, 150, 30)
        self.new_game_button = pygame.Rect(600, 300, 150, 30)
        self.refresh_button = pygame.Rect(700, 150, 60, 25)

        self.current_screen = [self.menu_screen]  # is stack, so pop when go back, or append when go forward.
        self.switch_event = {self.menu_screen: self.menu_event, self.score_screen: self.score_event,
                             self.selection_screen: self.selection_event}
        self.game_running = False
        self.game = None
        self.state = None

        self.p_id = None
        self.db_sent = False
        self.scores = None

    ######## Network_connected Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Is called when the menu has successfully connected to the server
    ##########################
    def Network_connected(self, data):
        print("You are now connected to the server")

    ######## Network_room_full_disconnect Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Is called when the menu cannot connect to server due to the room being full. Will switch to the main menu
    # screen and sends a message to close the channel
    ##########################
    def Network_room_full_disconnect(self, data):
        self.current_screen = [self.menu_screen]
        connection.Send({"action": "room_full_close", "id": data["id"]})  # just to help server identify specific client

    ######## Network_get_id Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Called when server sends the id of client. Will send message back to indicate the client as from menu and
    # therefore requesting the score list
    ##########################
    def Network_get_id(self, data):
        self.p_id = data["id"]
        connection.Send({"action": "menu", "p_id": self.p_id})  # once id got, send message to send scores

    ######## Network_give_scores Method ########
    # Parameters:- data: dictionary
    # Return type:- n/a
    # Purpose: Gives the client the scores from the server to be displayed
    ##########################
    def Network_give_scores(self, data):
        self.scores = data["scores"]
        # display screen now we have scores

    ######## menu_server_conn Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Connects to the server, without initialising a game as the clients needs only to request scores.
    ##########################
    def menu_server_conn(self):
        port = 31425
        host = "localhost"

        self.Connect((host, port))

    ######## game_server_conn Method ########
    # Parameters:- conn_type: string
    # Return type:- n/a
    # Purpose: Connects to the server and starts a new game. Also switches screen to the game select screen
    ##########################
    def game_server_conn(self, conn_type):  # either join or new
        self.game = Game.Mazescape(screen)  # aggregation
        self.game_running = True
        self.game.server_conn(conn_type)

        self.select_game_screen()

    ######## menu_screen Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Draws and blits various rectangles and text to the screen
    ##########################
    def menu_screen(self):
        screen.fill(TEAL)
        title_text = self.big_font.render("Mazescape", 1, BLACK)
        start_game_text = self.normal_font.render("Start Game", 1, BLACK)
        quit_text = self.normal_font.render("Exit Game", 1, BLACK)
        score_text = self.normal_font.render("Scores", 1, BLACK)

        screen.blit(title_text, (275, 50))
        pygame.draw.rect(screen, LIME, self.play_button)
        screen.blit(start_game_text, (320, 150))
        pygame.draw.rect(screen, LIME, self.quit_button)
        screen.blit(quit_text, (320, 200))
        pygame.draw.rect(screen, LIME, self.score_button)
        screen.blit(score_text, (320, 250))

    ######## selection_screen Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Draws and blits rectangles and text to the screen
    ##########################
    def selection_screen(self):
        screen.fill(TEAL)
        join_game_text = self.normal_font.render("Join Game", 1, BLACK)
        create_new_game_text = self.normal_font.render("New Game", 1, BLACK)
        back_text = self.small_font.render("Back", 1, BLACK)

        pygame.draw.rect(screen, LIME, self.join_game_button)
        screen.blit(join_game_text, (200, 300))
        pygame.draw.rect(screen, LIME, self.new_game_button)
        screen.blit(create_new_game_text, (600, 300))
        pygame.draw.rect(screen, LIME, self.back_button)
        screen.blit(back_text, (700, 500))

    ######## score_screen Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Contains the draw and blit statements for buttons and text. Iterates through each score and draws
    ##########################
    def score_screen(self):
        screen.fill(TEAL)
        title = self.big_font.render("Scores", 1, BLACK)
        back_text = self.small_font.render("Back", 1, BLACK)
        refresh = self.small_font.render("Refresh", 1, BLACK)

        screen.blit(title, (300, 10))

        pygame.draw.rect(screen, LIME, self.back_button)
        screen.blit(back_text, (700, 500))
        pygame.draw.rect(screen, LIME, self.refresh_button)
        screen.blit(refresh, (700, 150))

        if self.scores is None:  # no scores in database
            no_scores = self.normal_font.render("No Scores available", 1, BLACK)
            screen.blit(no_scores, (300, 100))
        else:
            y = 50
            pos = 1
            for scores in self.scores:
                name = scores[0]
                score = scores[1]

                score = self.normal_font.render(str(pos) + ": " + name.upper() + ": " + str(score), 1, BLACK)
                screen.blit(score, (10, y))
                pos += 1
                y += 30

        connection.Pump()  # only check for messages during score screen, as networking is on used in this one location
        # for the menu code. Any other needs for calling pump are in the game.py code, so not here.
        self.Pump()

    ######## select_game_screen Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Switches screen to be displayed once state has changed in the game object. If none, we assume the game
    # has ended and we reset to menu screen.
    ##########################
    def select_game_screen(self):
        screen_selection = {"selection": self.game.selection_screen, "wait": self.game.wait_screen,
                            "game": self.game.game_screen, "finish": self.game.finish_screen,
                            "pending": self.game.waiting}

        if self.game.state is not None:
            # if the game state is any of the above
            next_screen = screen_selection[self.game.state]
            self.current_screen.append(next_screen)
            self.state = self.game.state  # keeps a holder for current game state so we can check each loop if changed
        else:  # else if the game is ended and there is no game state
            self.current_screen = [self.menu_screen]
            self.game = None
            self.game_running = False
            self.state = None

    ######## display_update Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Continuously called in main loop. Executes method on top of the stack, current screen, which draws
    # necessary images and text.
    ##########################
    def display_update(self):
        self.current_screen[-1]()
        pygame.display.flip()

    ######## event_loop Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: Will check for collisions between mouse clicks and back button, which is on all screens except main menu
    # screen. Will call specific event methods dependent on the screen displayed.
    ##########################
    def event_loop(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.switch_event[self.current_screen[-1]](mouse_pos)
                # switch statement, no need for loads of ifs to see what screen it is. Is marginally quicker.

                if self.back_button.collidepoint(*mouse_pos):  # back button is on many screens, we just call once.
                    if self.current_screen[-1] is not self.menu_screen:  # is no back button on main menu
                        if self.current_screen[-1] == self.score_screen:
                            connection.Send({"action": "disconnect", "id": self.p_id})  # we disconnect if on score screen
                        self.current_screen.pop()

    ######## menu_event Method ########
    # Parameters:- mouse_pos: tuple
    # Return type:- n/a
    # Purpose: Checks for collisions from mouse to the buttons seen on the menu screen. Resulting in either setting a
    # game, exiting the programme or accessing the score screen - connecting to server.
    ##########################
    def menu_event(self, mouse_pos):
        if self.play_button.collidepoint(*mouse_pos):  # mouse pos is a tuple. func needs 2 parameters. so
            self.current_screen.append(self.selection_screen)  # unpack the mouse pos tuple with *
        elif self.quit_button.collidepoint(*mouse_pos):
            self.running = False
        elif self.score_button.collidepoint(*mouse_pos):
            self.menu_server_conn()
            self.current_screen.append(self.score_screen)

    ######## selection_event Method ########
    # Parameters:- mouse_pos: tuple
    # Return type:- n/a
    # Purpose: Checks for collisions from mouse to buttons from the selection screen. Results in connection to server as
    # a joining game client or a new game client
    ##########################
    def selection_event(self, mouse_pos):
        if self.new_game_button.collidepoint(*mouse_pos):
            self.game_server_conn("new")
        elif self.join_game_button.collidepoint(*mouse_pos):
            self.game_server_conn("join")

    ######## score_event Method ########
    # Parameters:- mouse_pos: tuple
    # Return type:- n/a
    # Purpose: Checks for collisions between mouse and the refresh button on the menu
    ##########################
    def score_event(self, mouse_pos):
        if self.refresh_button.collidepoint(*mouse_pos):
            connection.Send({"action": "menu", "p_id": self.p_id})  # send message to get scores

    ######## loop Method ########
    # Parameters:- n/a
    # Return type:- n/a
    # Purpose: The top level loop. Everything client side called is ultimately from this loop. Runs event loops, the
    # game loop and the display update.
    ##########################
    def loop(self):
        while self.running:
            clock.tick(420)

            if self.game_running:
                self.game.loop()

                if self.game.state != self.state:  # avoids calling s.select_game_screen() each loop. will update screen
                    self.select_game_screen()      # only if game state changes, and if so we check for new state
            else:
                self.event_loop()  # use event loop of menu, not game, if game isn't running

            self.display_update()


######## main Function ########
# Parameters:- n/a
# Return type:- n/a
# Purpose: Creates a new object of menu and starts off the loop.
##########################
def main():
    menu = Menu()
    menu.loop()


if __name__ == "__main__":  # Only file needed to be run.
    main()
