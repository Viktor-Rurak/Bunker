import random
from data.action_data import deal_action_cards, deal_elimination_card


class Bunker:
    def __init__(self, size_choice, item_choice, time_choice):
        self.size = {}
        self.item = {}
        self.time = {}
        self.points = 0
        self.size_choice(size_choice)
        self.item_choice(item_choice)
        self.time_choice(time_choice)

    def size_choice(self, size_choice):
        size_name = random.choice(list(size_choice.keys()))
        self.size = {"name": size_name, **size_choice[size_name]}
        self.points += size_choice[size_name]["area"]

    def item_choice(self, item_choice):
        item_quantity = self.size["capacity"]
        for i in range(item_quantity):
            item_name = random.choice(list(item_choice.keys()))
            self.item[item_name] = item_choice[item_name]
            self.points += item_choice[item_name]["base"]
            item_choice.pop(item_name)

    def time_choice(self, time_choice):
        time_name = random.choice(list(time_choice.keys()))
        self.time = {"name": time_name, "value": time_choice[time_name]}

    def show_bunker(self):
        print(self.size)
        print(self.item)
        print(self.time)
        print(self.points)

    def show_bunker_as_player(self):
        print(self.size["name"])
        for i in self.item.keys():
            print(i)
        print(self.time["name"])
        print(self.points)


class Catastrophe:
    def __init__(self):
        self.catastrophe = {}

    def show_catastrophe(self):
        print(self.catastrophe)

    def show_catastrophe_as_player(self):
        print(self.catastrophe["name"])
        print("Опис:")
        print(self.catastrophe["modifiers"]["description"])

    def get_catastrophe_modifiers(self):
        mods = self.catastrophe.get("modifiers", {}).copy()
        mods.pop("description", None)
        return mods

    def choice_catastrophe(self, catastrophe_modifiers):
        name = random.choice(list(catastrophe_modifiers.keys()))
        self.catastrophe = {
            "name": name,
            "modifiers": catastrophe_modifiers[name]
        }


class Card:
    def __init__(self):
        self.age = {}
        self.gender = None
        self.body_constitution = {}
        self.human_trait = {}
        self.occupation = {}
        self.health = {}
        self.hobby = {}
        self.phobia = {}
        self.item = {}
        self.additional_introduction = {}
        self.action_cards = []
        self.elimination_card = None
        self.tag_list = []
        self.points = 0

    def generate_card(
        self, body_constitution, occupation_choice, gender,
        traits, choice_disease, hobbies_choice,
        choice_phobia, item_choice, additional_info
    ):
        self.choice_age()
        self.choice_gender(gender)
        self.choice_body_constitution(body_constitution)
        self.choice_human_trait(traits)
        self.choice_occupation(occupation_choice)
        self.choice_health(choice_disease)
        self.choice_hobby(hobbies_choice)
        self.choice_phobia(choice_phobia)
        self.choice_item(item_choice)
        self.choice_additional_introduction(additional_info)
        self.action_cards = deal_action_cards(num_cards=2)

    def eliminate(self):
        self.elimination_card = deal_elimination_card()
        return self.elimination_card

    def show_card(self):
        print(self.age)
        print(self.gender)
        print(self.body_constitution)
        print(self.human_trait)
        print(self.occupation)
        print(self.health)
        print(self.hobby)
        print(self.phobia)
        print(self.item)
        print(self.additional_introduction)
        print(self.tag_list)
        print(self.points)
        print("Карти дій:")
        for ac in self.action_cards:
            char = ac.get("characteristic") or ""
            suffix = f" ({char})" if char else ""
            print(f"  [{ac['name']}{suffix}]")
        if self.elimination_card:
            name = self.elimination_card["name"]
            print(f"Карта помсти: [{name}]")

    def choice_age(self):
        age_ = random.randint(16, 85)
        if age_ < 30:
            prob = 80
        elif age_ < 40:
            prob = 50
        elif age_ < 50:
            prob = 20
        elif age_ < 60:
            prob = 10
        else:
            prob = 0
        parenthood = random.randint(1, 100) < prob
        self.age = {"age": age_, "parenthood": parenthood}

    def choice_gender(self, gender):
        self.gender = random.choice(gender)

    def choice_body_constitution(self, body_constitution):
        choice = random.choice(list(body_constitution.keys()))
        self.body_constitution[choice] = body_constitution[choice]

    def choice_occupation(self, occupation_choice):
        choice = random.choice(list(occupation_choice.keys()))
        self.occupation[choice] = occupation_choice[choice]
        self.tag_list.append(self.occupation[choice]["tags"])

    def choice_human_trait(self, traits):
        name, data = random.choice(list(traits.items()))
        self.human_trait[name] = data

    def choice_health(self, choice_disease):
        if random.randint(0, 100) < 50:
            weights = [
                100 - choice_disease[d]["type"][1]
                for d in choice_disease
            ]
            disease = random.choices(
                population=list(choice_disease.keys()),
                weights=weights,
                k=1
            )[0]
            self.health[disease] = choice_disease[disease]
        else:
            self.health = {
                "Ідеальнний стан": {"type": ["Ідеальний", 0]}
            }

    def choice_hobby(self, hobbies_choice):
        choice = random.choice(list(hobbies_choice.keys()))
        self.hobby[choice] = hobbies_choice[choice]

    def choice_phobia(self, choice_phobia):
        choice = random.choice(list(choice_phobia.keys()))
        self.phobia[choice] = choice_phobia[choice]

    def choice_item(self, item_choice):
        item = random.choice(list(item_choice.keys()))
        self.item[item] = item_choice[item]

    def choice_additional_introduction(self, additional_info):
        choice = random.choice(list(additional_info.keys()))
        self.additional_introduction[choice] = additional_info[choice]

    def card_calculation(self, c_tags):
        # Робота
        (occ_name, occ_data), = self.occupation.items()
        occ_base = float(occ_data["base"])
        occ_tags = occ_data.get("tags", [])
        occ_pts = tag_calculation(occ_base, occ_tags, c_tags)

        # Предмет
        (item_name, item_data), = self.item.items()
        item_base = float(item_data["base"])
        item_tags = item_data.get("tags", [])
        item_pts = tag_calculation(item_base, item_tags, c_tags)

        # Фобія
        (phobia_name, phobia_data), = self.phobia.items()
        phobia_tag = phobia_data["tag"]
        phobia_pts = c_tags.get(phobia_tag, 1)

        # Хобі
        (hobby_name, hobby_data), = self.hobby.items()
        hobby_base = float(hobby_data["base"])
        hobby_tags = hobby_data.get("tags", [])
        hobby_pts = tag_calculation(hobby_base, hobby_tags, c_tags)

        # Тіло і характер
        body_pts = only_value(self.body_constitution)
        trait_pts = only_value(self.human_trait)

        # Здоров'я
        (health_type, health_data), = self.health.items()
        health_base = float(health_data["type"][1])
        health_pts = 1 - (health_base / 100)

        # Додаткова інфо
        (add_name, add_data), = self.additional_introduction.items()
        add_tag = add_data.get("tag", "")
        add_pts = tag_calculation(1, [add_tag], c_tags)

        print(
            f"({add_pts} * {body_pts} * {trait_pts}"
            f" * {phobia_pts} * {health_pts})"
            f" * ({hobby_pts} + {occ_pts} + {item_pts})"
        )

        mult = body_pts * trait_pts * phobia_pts * health_pts * add_pts
        self.points = mult * (hobby_pts + occ_pts + item_pts)
        print(self.points)

    def __del__(self):
        print("Card was deleted")


def tag_calculation(base, tags, c_tags):
    multiply = 1
    for tag in tags:
        if tag in c_tags:
            multiply *= c_tags[tag]
    return base * multiply


def only_value(d, default=None):
    return next(iter(d.values()), default)
