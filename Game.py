# Game.py
import random

from card_generator import Card, Bunker, Catastrophe
from data.card_data import (
    get_gender,
    get_body_constitution,
    get_occupation_choice,
    get_traits,
    get_choice_disease,
    get_hobbies_choice,
    get_choice_phobia,
    get_item_choice,
    get_additional_info
)
import data.Bunker_data as Bunker_data
import data.catastrophe_data as catastrophe_data


class Game:
    def __init__(self):
        self.cards = []
        self.bunker = None
        self.catastrophe = None
        self.c_tags = None  # модифікатори катастрофи

    # ------------------------------
    #   СТВОРЕННЯ КАТАСТРОФИ
    # ------------------------------
    def create_catastrophe(self):
        catastrophe_modifiers = catastrophe_data.get_catastrophe()
        self.catastrophe = Catastrophe()
        self.catastrophe.choice_catastrophe(catastrophe_modifiers)
        self.c_tags = self.catastrophe.get_catastrophe_modifiers()
        return self.catastrophe


    #   СТВОРЕННЯ БУНКЕРА
    def create_bunker(self):
        size_choice = Bunker_data.get_size()
        item_choice = Bunker_data.get_item()
        time_choice = Bunker_data.get_time()
        self.bunker = Bunker()
        self.bunker.size_choice(size_choice)
        self.bunker.item_choice(item_choice)
        self.bunker.time_choice(time_choice)
        return self.bunker


    #   СТВОРЕННЯ КАРТИ
    def create_card(self):
        card = Card()
        card.generate_card(
            body_constitution=get_body_constitution(),
            occupation_choice=get_occupation_choice(),
            gender=get_gender(),
            traits=get_traits(),
            choice_disease=get_choice_disease(),
            hobbies_choice=get_hobbies_choice(),
            choice_phobia=get_choice_phobia(),
            item_choice=get_item_choice(),
            additional_info=get_additional_info()
        )

        # якщо вже створена катастрофа — рахуємо пойнти
        if self.c_tags:
            card.card_calculation(self.c_tags)

        self.cards.append(card)
        return card


    #   СТВОРЕННЯ КІЛЬКОХ КАРТ
    def create_cards(self, amount):
        return [self.create_card() for _ in range(amount)]
