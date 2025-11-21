import telebot
import openai
import random
import card_generator as cg


Catastrophe = cg.Catastrophe()
Catastrophe.generate_catastrophe()
Catastrophe.show_catastrophe()
card = cg.Card()
card.generate_card()
card.show_card()