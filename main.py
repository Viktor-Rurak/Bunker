import telebot
import openai
import random
import card_generator as cg
import Game

game = Game.Game()
game.create_cards(5)
game.show_game()