import random
from card_generator import Card, Bunker, Catastrophe
from data.card_data import (
    get_gender, get_body_constitution, get_occupation_choice,
    get_traits, get_choice_disease, get_hobbies_choice,
    get_choice_phobia, get_item_choice, get_additional_info
)
import data.Bunker_data as Bunker_data
import data.catastrophe_data as catastrophe_data


class Game:
    def __init__(self):
        self.cards = []
        self.catastrophe = self.create_catastrophe()
        self.bunker = self.create_bunker()

    def create_catastrophe(self):
        catastrophe_modifiers = catastrophe_data.get_catastrophe()
        self.catastrophe = Catastrophe()
        self.catastrophe.choice_catastrophe(catastrophe_modifiers)
        self.c_tags = self.catastrophe.get_catastrophe_modifiers()
        return self.catastrophe

    def create_bunker(self):
        size_choice = Bunker_data.get_size()
        item_choice = Bunker_data.get_item()
        time_choice = Bunker_data.get_time()
        self.bunker = Bunker(size_choice, item_choice, time_choice)
        return self.bunker

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
            additional_info=get_additional_info(),
        )
        if self.c_tags:
            card.card_calculation(self.c_tags)
        self.cards.append(card)
        return card

    def create_cards(self, amount):
        return [self.create_card() for _ in range(amount)]

    def to_dict(self):
        return {
            "catastrophe": {
                "name": self.catastrophe.catastrophe["name"],
                "description": self.catastrophe.catastrophe["modifiers"]["description"]
            },
            "bunker": {
                "size": self.bunker.size["name"],
                "items": list(self.bunker.item.keys()),
                "time": self.bunker.time["name"],
                "points": self.bunker.points
            }
        }

    def show_game(self):
        print("Катастрофа:")
        self.catastrophe.show_catastrophe_as_player()
        print("\n\nБункер:")
        self.bunker.show_bunker_as_player()
        for i in self.cards:
            print()
            i.show_card()