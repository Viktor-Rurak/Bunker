import random


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
        catastrophe_name = random.choice(list(catastrophe_modifiers.keys()))
        self.catastrophe = {"name": catastrophe_name, "modifiers": catastrophe_modifiers[catastrophe_name]}





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
        self.special_ability = ""
        self.tag_list = []
        self.points = 0
    def generate_card(self, body_constitution, occupation_choice, gender, traits, choice_disease, hobbies_choice, choice_phobia, item_choice, additional_info):
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

    def choice_age(self):
        age_ = random.randint(16, 85)
        parenthood = random.random() < (0.6 if age_ < 55 else 0.2)
        self.age = {"age": age_, "parenthood": parenthood}

    def choice_gender(self, gender):
        self.gender = random.choice(gender)

    def choice_body_constitution(self, body_constitution): #max 50
        body_constitution_choice = random.choice(list(body_constitution.keys()))
        self.body_constitution[body_constitution_choice] = body_constitution[body_constitution_choice]


    def choice_occupation(self, occupation_choice):

        choice_the_occupation = random.choice(list(occupation_choice.keys()))
        self.occupation[choice_the_occupation] = occupation_choice[choice_the_occupation]

        self.tag_list.append(self.occupation[choice_the_occupation]["tags"])

    def choice_human_trait(self, traits):
        name, data = random.choice(list(traits.items()))
        self.human_trait[name] = data

    def choice_health(self, choice_disease):
        if random.randint(0,100) < 50:
            disease = random.choices(
                population=list(choice_disease.keys()),
                weights=[100 - choice_disease[d]["type"][1] for d in choice_disease],
                k=1
            )[0]
            self.health[disease] = choice_disease[disease]
        else:
            self.health = {"Ідеальнний стан": {"type": ["Ідеальний", 0]}}


    def choice_hobby(self, hobbies_choice):
        choice_hobby = random.choice(list(hobbies_choice.keys()))
        self.hobby[choice_hobby] = hobbies_choice[choice_hobby]


    def choice_phobia(self, choice_phobia):
        choice_the_phobia = random.choice(list(choice_phobia.keys()))
        self.phobia[choice_the_phobia] = choice_phobia[choice_the_phobia]

    def choice_item(self, item_choice):
        item = random.choice(list(item_choice.keys()))
        self.item[item] = item_choice[item]

    def choice_additional_introduction(self, additional_info):
        choice_additional_introduction = random.choice(list(additional_info.keys()))
        self.additional_introduction[choice_additional_introduction] = additional_info[choice_additional_introduction]



    def card_calculation(self, c_tags):

        #Розрахунок пойнтів за роботу
        (occupation_name, occupation_data), = self.occupation.items()
        occupation_base = float(occupation_data["base"])
        occupation_tags = occupation_data.get("tags", [])
        occupation_points = tag_calculation(occupation_base, occupation_tags, c_tags)

        #Розрахунок пойнтів за предмет
        (item_name, item_data), = self.item.items()
        item_base = float(item_data["base"])
        item_tags = item_data.get("tags", [])
        item_points = tag_calculation(item_base, item_tags, c_tags)

        #Получаємо множник за тег фобії
        (phobia_name, phobia_data), = self.phobia.items()
        phobia_tag = phobia_data["tag"]
        if phobia_tag in c_tags:
            phobia_points = c_tags[phobia_tag]

        else: phobia_points = 1

        # Розрахунок пойнтів за хобі
        (hobby_name, hobby_data), = self.hobby.items()
        hobby_base = float(hobby_data["base"])
        hobby_tags = hobby_data.get("tags", [])
        hobby_points = tag_calculation(hobby_base, hobby_tags, c_tags)

        # Розрахунок множника за тіло і характер
        body_points = only_value(self.body_constitution)
        human_trait_points = only_value(self.human_trait)

        #Получаємо множник за здоров'я
        (health_type, health_data), = self.health.items()
        health_base = float(health_data["type"][1])
        health_points = 1 - (health_base / 100)
        print(f"({body_points} * {human_trait_points} * {phobia_points} * {health_points}) * ({hobby_points} + {occupation_points} + {item_points})")
        self.points = (body_points * human_trait_points * phobia_points * health_points) * (hobby_points + occupation_points + item_points)
        print(self.points)


#Перемноження значень тегів і тегів катастрофи
def tag_calculation(base, tags, c_tags):
    multiply = 1
    for tag in tags:
        if tag in c_tags:
            multiply *= c_tags[tag]

    return base * multiply

#Дістає значення з однозначної характеристики
def only_value(d, default=None):
    return next(iter(d.values()), default)


