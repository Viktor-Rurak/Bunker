import random


def get_rokirovka_characteristic():
    # Менша вага = рідше випадає = сильніша карта
    characteristics = {
        "hobby":                    30,
        "phobia":                   25,
        "additional":   25,
        "trait":        15,
        "body":         15,
        "item":                     10,
        "health":                    8,
        "occupation":                5,
    }
    population = list(characteristics.keys())
    weights = list(characteristics.values())
    return random.choices(population, weights=weights, k=1)[0]


def get_action_cards():
    action_cards = {

        # ─── Обмін / Маніпуляція ───────────────────────────────────────────────

        "Рокіровка": {
            "description": (
                "Характеристика для обміну визначається заздалегідь при роздачі карти. "
                "Гравець бачить яку характеристику він може поміняти, але не може її змінити. "
                "Сам обирає з ким міняється. Можна відмовитись від використання."
            ),
            "category": "swap",
            "target": "single_choice",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": True,
            "characteristic": None,  # визначається при генерації через get_rokirovka_characteristic()
        },

        "Переоцінка": {
            "description": (
                "Одна рандомна характеристика (однакова для всіх) перегенеровується заново "
                "у всіх гравців одночасно. Ніхто не знає що випаде."
            ),
            "category": "swap",
            "target": "all",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": False,
        },

        "Крадіжка": {
            "description": (
                "Гравець забирає собі будь-яку одну характеристику обраного гравця. "
                "Тому гравцю натомість генерується нова рандомна характеристика того ж типу."
            ),
            "category": "swap",
            "target": "single_choice",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": False,
        },

        "Маскарад": {
            "description": (
                "Гравець міняється своєю професією з будь-яким обраним гравцем. "
                "Обидва отримують нові бали відповідно до нової професії."
            ),
            "category": "swap",
            "target": "single_choice",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": False,
        },

        # ─── Розкриття інформації ──────────────────────────────────────────────

        "Детектив": {
            "description": (
                "Гравець примусово відкриває будь-яку одну приховану характеристику "
                "обраного суперника — всім гравцям."
            ),
            "category": "reveal",
            "target": "single_choice",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": False,
        },

        "Анонімне донесення": {
            "description": (
                "Гравець таємно переглядає всі закриті характеристики одного обраного гравця. "
                "Інші цього не бачать."
            ),
            "category": "reveal",
            "target": "single_choice",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": False,
        },

        "Скандал": {
            "description": (
                "Одна рандомна закрита характеристика обраного гравця розкривається всім."
            ),
            "category": "reveal",
            "target": "single_choice",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": False,
        },

        # ─── Захист ───────────────────────────────────────────────────────────

        "Імунітет": {
            "description": (
                "Одноразовий захист. Повністю блокує будь-яку карту дії, "
                "направлену проти цього гравця."
            ),
            "category": "protect",
            "target": "self",
            "timing": "reaction",
            "for_eliminated": False,
            "can_decline": True,
        },

        "Підміна": {
            "description": (
                "Якщо цього гравця намагаються виключити голосуванням — "
                "він перенаправляє голос на будь-якого іншого гравця на свій вибір."
            ),
            "category": "protect",
            "target": "self",
            "timing": "before_vote",
            "for_eliminated": False,
            "can_decline": True,
        },

        # ─── Підсилення ───────────────────────────────────────────────────────

        "Еволюція": {
            "description": (
                "Гравець обирає одну свою характеристику і отримує два нових варіанти на вибір. "
                "Залишає той що вигідніший, інший відкидається."
            ),
            "category": "boost",
            "target": "self",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": True,
        },

        "Симбіоз": {
            "description": (
                "Гравець укладає союз з одним обраним гравцем. Обидва отримують +10% до балів. "
                "Але надалі їх або виключають разом, або не виключають зовсім — "
                "голос проти одного автоматично стає голосом проти обох."
            ),
            "category": "boost",
            "target": "single_choice",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": True,
        },

        # ─── Хаос ─────────────────────────────────────────────────────────────

        "Лотерея долі": {
            "description": (
                "Одна рандомна характеристика перемішується між усіма гравцями випадково. "
                "Хто що отримає — невідомо заздалегідь."
            ),
            "category": "chaos",
            "target": "all",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": False,
        },

        "Апокаліпсис": {
            "description": (
                "Гравець додає новий тег до поточної катастрофи. "
                "Це змінює розрахунок балів для всіх гравців одразу."
            ),
            "category": "chaos",
            "target": "all",
            "timing": "any",
            "for_eliminated": False,
            "can_decline": False,
        },

        # ─── Помста (тільки для виключених) ───────────────────────────────────

        "Ворожий бункер": {
            "description": (
                "Використовується після виключення. Гравець переходить у «ворожий бункер» "
                "і атакує: його бали віднімаються від загального рахунку тих, хто пройшов. "
                "Чим сильніший виключений — тим більша шкода."
            ),
            "category": "revenge",
            "target": "all",
            "timing": "on_elimination",
            "for_eliminated": True,
            "can_decline": True,
        },

        "Прокляття": {
            "description": (
                "Використовується після виключення. Гравець знижує бали "
                "одного обраного гравця що залишився на 15%."
            ),
            "category": "revenge",
            "target": "single_choice",
            "timing": "on_elimination",
            "for_eliminated": True,
            "can_decline": True,
        },

        "Зрада": {
            "description": (
                "Використовується після виключення. Гравець розкриває всі "
                "приховані характеристики одного обраного суперника — всім гравцям."
            ),
            "category": "revenge",
            "target": "single_choice",
            "timing": "on_elimination",
            "for_eliminated": True,
            "can_decline": True,
        },
    }
    return action_cards


def get_action_card_weights():
    # Ймовірність випадання карти при роздачі (менша вага = рідкісніша карта)
    weights = {
        "Рокіровка":            20,
        "Переоцінка":           10,
        "Крадіжка":             12,
        "Маскарад":             10,
        "Детектив":             18,
        "Анонімне донесення":   15,
        "Скандал":              16,
        "Імунітет":              8,
        "Підміна":               8,
        "Еволюція":             14,
        "Симбіоз":               6,
        "Лотерея долі":          7,
        "Апокаліпсис":           4,
        "Ворожий бункер":       20,
        "Прокляття":            20,
        "Зрада":                20,
    }
    return weights


def deal_action_cards(num_cards=2):
    """
    Роздає гравцю num_cards карт дії.
    Карти помсти (for_eliminated=True) в звичайну роздачу не потрапляють —
    вони активуються окремо при виключенні.
    """
    action_cards = get_action_cards()
    weights = get_action_card_weights()

    regular_cards = {k: v for k, v in action_cards.items() if not v["for_eliminated"]}
    regular_weights = [weights[k] for k in regular_cards]

    chosen_names = random.choices(
        population=list(regular_cards.keys()),
        weights=regular_weights,
        k=num_cards
    )

    dealt = []
    for name in chosen_names:
        card = action_cards[name].copy()
        card["name"] = name
        if name == "Рокіровка":
            card["characteristic"] = get_rokirovka_characteristic()
        dealt.append(card)

    return dealt


def deal_elimination_card():
    """
    Видає виключеному гравцю одну карту помсти.
    """
    action_cards = get_action_cards()
    weights = get_action_card_weights()

    revenge_cards = {k: v for k, v in action_cards.items() if v["for_eliminated"]}
    revenge_weights = [weights[k] for k in revenge_cards]

    chosen_name = random.choices(
        population=list(revenge_cards.keys()),
        weights=revenge_weights,
        k=1
    )[0]

    card = action_cards[chosen_name].copy()
    card["name"] = chosen_name
    return card
