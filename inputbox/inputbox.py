"""
by Timothy Downs, input_box written for my map editor

This program needs a little cleaning up
It ignores the shift key
And, for reasons of my own, this program converts "-" to "_"

A program to get user input, allowing backspace etc
shown in a box in the middle of the screen
"""


import pygame
from pygame.locals import *


def get_key():
    while True:
        event = pygame.event.poll()
        if event.type == KEYDOWN:
            return event.key
    else:
        pass


def display_box(screen, message, colour):
    # Print a message in a box in the middle of the screen
    font_object = pygame.font.Font(None,  25)
    pygame.draw.rect(screen, colour, ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10, 300, 20), 0)
    pygame.draw.rect(screen, (255, 255, 255), ((screen.get_width() / 2) - 102,
                                               (screen.get_height() / 2) - 12, 304, 24), 1)
    if len(message) != 0:
        screen.blit(font_object.render(message, 1, (255, 255, 255)), ((screen.get_width() / 2) - 100,
                                                                      (screen.get_height() / 2) - 10))
    pygame.display.flip()


def ask(screen, question, colour):
    # ask(screen, question) -> answer
    pygame.font.init()
    current_string = ""
    allowed_chars = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    display_box(screen, (question + ": "), colour)
    while True:
        key = get_key()
        if key == K_BACKSPACE:
            current_string = current_string[0:-1]
        elif key == K_RETURN:
            break
        elif key <= 127:
            if set(chr(key)).issubset(allowed_chars):
                current_string = current_string + (chr(key))
        display_box(screen, ((question + ":") + current_string), colour)
    return current_string


def main():
    screen = pygame.display.set_mode((320, 240))
    print(ask(screen, "Enter Name", (0, 100, 100)))


if __name__ == '__main__':
    main()
