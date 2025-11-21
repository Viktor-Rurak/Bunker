
def get_gender():
    gender = ["male", "female"]
    return gender


def get_body_constitution():
    body_constitution = {
    "Анарексія": 0.6,
    "Худе тіло": 0.9,
    "Нормальне тіло": 1,
    "Атлетичне тіло": 1.5,
    "Крепке тіло": 1.3,
    "Надмірна вага": 0.9,
    "Легке ожиріння": 0.7,
    "Серйозне ожиріння": 0.6
}
    return body_constitution


def get_occupation_choice():
    occupation_choice = {
        "Лікар-хірург": {"base": 100, "tags": ["medical"]},
        "Фермер-агроном": {"base": 50, "tags": [""]},
        "Інженер-механік": {"base": 60, "tags": ["engineering"]},
        "Пожежник-рятувальник": {"base": 20, "tags": ["engineering", "medical"]},
        "Програміст": {"base": 25, "tags": ["engineering", "technology"]},
        "Військовий розвідник": {"base": 25, "tags": ["surviving", "weapons"]},
        "Біолог-мікробіолог": {"base": 80, "tags": ["medical", "quarantine"]},
        "Психолог": {"base": 40, "tags": ["psychology "]},
        "Будівельник": {"base": 25, "tags": ["shielding"]},
        "Кухар": {"base": 30, "tags": [""]},
        "Медсестра/фельдшер": {"base": 30, "tags": ["medical"]},
        "Вчитель історії": {"base": 20, "tags": ["history"]},
        "Священник": {"base": 20, "tags": ["psychology ", "religion"]},
        "Електрик": {"base": 40, "tags": ["engineering"]},
        "Мисливець": {"base": 25, "tags": ["surviving", "weapons"]},
        "Пілот вертольота": {"base": 20, "tags": ["helicopter", "fuel"]},
        "Актор": {"base": 20, "tags": [" "]},
        "Археолог": {"base": 20, "tags": ["history"]},
        "Юрист": {"base": 20, "tags": [""]},
        "Хакер": {"base": 30, "tags": ["engineering", "technology"]},
        "інженер з робототехніки": {"base": 50, "tags": ["engineering", "technology"]},
        "Фізик-ядерник": {"base": 40, "tags": ["radiation_gear", "engineering"]},
        "Ветеринар": {"base": 20, "tags": ["animals"]},
        "Бармен": {"base": 20, "tags": ["alcohol"]},
        "Фітнес-тренер": {"base": 20, "tags": [""]},
        "Cтоляр": {"base": 20, "tags": ["shielding"]},
        "Журналіст": {"base": 20, "tags": [""]},
        "Шахтар": {"base": 20, "tags": [""]},
        "Продавець-консультант": {"base": 20, "tags": [""]},
        "Офіціант": {"base": 20, "tags": [""]},
        "Прибиральник": {"base": 20, "tags": [""]},
        "Водій": {"base": 20, "tags": [""]},
        "Охоронець": {"base": 20, "tags": ["weapons"]},
        "Касир": {"base": 20, "tags": [""]},
        "Кур’єр": {"base": 20, "tags": [""]},
    }
    return occupation_choice


def get_traits():
    traits = {
        "Самозакоханий": 0.95,
        "Працьовитий": 1.15,
        "Комунікабельний": 1.05,
        "Безпринципний": 1.05,
        "Вразливий": 0.95,
        "Життєрадісний": 1.05,
        "Імпульсивний": 0.95,
        "Беземоційний": 1.00,
        "Цілеспрямований": 1.05,
        "Рішучий": 1.15,
        "Невпевнений": 0.90,
        "Боягузливий": 0.85,
        "Розсудливий": 1.05,
        "Дурний": 0.75,
        "Винахідливий": 1.05,
        "Мудрий": 1.05,
        "Жорстокий": 1.00,
        "Добрий": 1.00,
        "Чуйний": 1.00,
        "Чесний": 1.05,
    }
    return traits


def get_choice_disease():
    choice_disease = {
        # 🦠 Вірусні
        "Covid-19": {"type": ["Вірусна", 65]},
        "Грип": {"type": ["Вірусна", 25]},
        "ВІЛ": {"type": ["Вірусна", 85]},
        "Гепатит B": {"type": ["Вірусна", 70]},
        "Гепатит C": {"type": ["Вірусна", 75]},
        "Герпес": {"type": ["Вірусна", 15]},
        "Віспа": {"type": ["Вірусна", 90]},
        "Кір": {"type": ["Вірусна", 50]},

        # 🧬 Неінфекційні
        "Рак легенів": {"type": ["Неінфекційна", 95]},
        "Діабет": {"type": ["Неінфекційна", 60]},
        "Гіпертонія": {"type": ["Неінфекційна", 50]},
        "Бронхіальна астма": {"type": ["Неінфекційна", 55]},
        "Булимія": {"type": ["Неінфекційна", 45]},  # вічно голодний
        "Анемія": {"type": ["Неінфекційна", 35]},  # біда з гемоглобіном, блідий і ніякий
        "Ниркова недостатність": {"type": ["Неінфекційна", 85]},
        "Інфаркт": {"type": ["Неінфекційна", 80]},

        # 🧠 Психологічні
        "Шизофренія": {"type": ["Психологічна", 85]},
        "Депресія": {"type": ["Психологічна", 60]},
        "Психоз": {"type": ["Психологічна", 50]},
        "Манія величі": {"type": ["Психологічна", 30]},
        "Порушення концентрації": {"type": ["Психологічна", 25]},
        "Панічні атаки": {"type": ["Психологічна", 20]},
        "Біполярний розлад": {"type": ["Психологічна", 65]},
        "Нарцисизм": {"type": ["Психологічна", 15]},

        # 💪 Фізичні
        "Плоскостопість": {"type": ["Фізична", 10]},
        "Синдром хрустальної людини": {"type": ["Фізична", 95]},
        "Рахіт": {"type": ["Фізична", 35]},
        "Альбінізм": {"type": ["Фізична", 10]},
        "Скалічення руки": {"type": ["Фізична", 45]},
        "Кульгавість": {"type": ["Фізична", 30]},
        "Глухота": {"type": ["Фізична", 55]},
        "Сліпота": {"type": ["Фізична", 65]},
    }
    return choice_disease


def get_hobbies_choice():
    hobbies_choice = {
        "Туризм": {"base": 10, "tags": ["surviving", "navigation", "fire"]},
        "Кемпінг": {"base": 25, "tags": ["surviving", "shelter", "fire"]},
        "Рибальство": {"base": 20, "tags": ["food", "fishing", "water"]},
        "Полювання": {"base": 20, "tags": ["food", "weapons", "tracking"]},
        "Городництво": {"base": 20, "tags": ["food", "gardening", "seeds"]},
        "Пасічництво": {"base": 15, "tags": ["food", "beekeeping"]},
        "Грибництво": {"base": 20, "tags": ["food", "foraging", "toxicology"]},
        "Травництво": {"base": 20, "tags": ["herbalism"]},
        "Консервація та ферментація": {"base": 15, "tags": ["cooking", "preservation", "sanitation"]},
        "Кулінарія": {"base": 15, "tags": ["cooking", "food"]},
        "Сироробство": {"base": 10, "tags": ["food", "preservation", "dairy"]},
        "М’ясництв)": {"base": 15, "tags": ["food", "butchery", "hygiene"]},
        "Столярство": {"base": 10, "tags": ["woodworking", "shielding", "repair"]},
        "Ковальство": {"base": 10, "tags": ["blacksmithing", "tools", "weapons"]},
        "Ремонт електроніки": {"base": 15, "tags": ["electronics", "repair"]},
        "Шиття та латання одягу": {"base": 10, "tags": ["sewing", "textiles", "repair"]},
        "В’язання": {"base": 10, "tags": ["textiles", "warmth"]},
        "Плетіння мотузок і в'язання вузлів": {"base": 15, "tags": ["rope", "knots", "surviving"]},
        "Гончарство": {"base": 10, "tags": ["pottery", "cookware", "water"]},
        "Плетіння кошиків": {"base": 10, "tags": ["basketry", "storage"]},
        "Картографія та орієнтування": {"base": 20, "tags": ["mapping", "navigation"]},
        "Йога": {"base": 5, "tags": ["fitness", "morale"]},
        "Бойові мистецтва": {"base": 15, "tags": ["combat", "discipline"]},
        "Альпінізм": {"base": 15, "tags": ["climbing", "rescue", "surviving"]},
        "Катання на велосипеді": {"base": 5, "tags": ["transport", "bicycle", "repair"]},
        "Автомеханіка (гаражний рівень)": {"base": 10, "tags": ["mechanics", "car", "repair"]},
        "Домашнє пивоваріння": {"base": 10, "tags": ["brewing", "morale", "sanitation"]},
        "Коучинг": {"base": 5, "tags": ["psychology ", "morale"]},
        "Вивчення іноземних мов": {"base": 10, "tags": ["languages", "negotiation", "communication"]},
        "Малювання": {"base": 3, "tags": ["design", "morale", "education"]},
        "Репетиторство": {"base": 5, "tags": ["teaching", "education", "child_care"]},
        "Стрільба з лука": {"base": 20, "tags": ["weapons", "hunting", "silent"]},
        "Виготовлення свічок і мила": {"base": 10, "tags": ["sanitation", "light", "craft"]},
    }
    return hobbies_choice


def get_choice_phobia():
    choice_phobia = {
        "арахнофобія": {"tag": "spiders"},
        "клаустрофобія": {"tag": "closed_spaces"},
        "акрофобія": {"tag": "heights"},
        "ніктофобія": {"tag": "darkness"},
        "офідіофобія": {"tag": "snakes"},
        "трипофобія": {"tag": "holes"},
        "гемофобія": {"tag": "blood"},
        "токофобія": {"tag": "pregnancy"},
        "танатофобія": {"tag": "death"},
        "авіафобія": {"tag": "flying"},
        "дентофобія": {"tag": "dentists"},
        "аквафобія": {"tag": "deep_water"},
        "ентомофобія": {"tag": "insects"},
        "карцинофобія": {"tag": "cancer"},
        "соціофобія": {"tag": "social_situations"},
        "пірофобія": {"tag": "fire"},
        "мізофобія": {"tag": "germs"}
    }
    return choice_phobia


def get_item_choice():
    item_choice = {
        "Аптечка": {"base": 10, "tags": ["medical"]},
        "Ніж": {"base": 10, "tags": ["weapons"]},
        "Ліхтарик": {"base": 5, "tags": ["energy"]},
        "Сірники": {"base": 5, "tags": ["energy"]},
        "Запальничка": {"base": 10, "tags": ["energy"]},
        "Фільтр для води": {"base": 25, "tags": ["food"]},
        "Пляшка води": {"base": 5, "tags": ["food"]},
        "Консерви": {"base": 10, "tags": ["food"]},
        "Радіоприймач": {"base": 25, "tags": ["communication"]},
        "Палиця": {"base": 5, "tags": ["weapons"]},
        "Медичний набір": {"base": 15, "tags": ["medical"]},
        "Генератор": {"base": 50, "tags": ["energy"]},
        "Карта місцевості": {"base": 10, "tags": ["security"]},
        "Компас": {"base": 10, "tags": ["security"]},
        "Спальний мішок": {"base": 10, "tags": ["none"]},
        "Палатка": {"base": 15, "tags": ["shelter"]},
        "Мотузка": {"base": 10, "tags": ["engineering"]},
        "Набір інструментів": {"base": 20, "tags": ["engineering"]},
        "Ноутбук": {"base": 20, "tags": ["technology"]},
        "Книга з виживання": {"base": 15, "tags": ["knowledge"]},
        "Вогнепальна зброя": {"base": 40, "tags": ["weapons"]},
        "Патрони": {"base": 25, "tags": ["weapons"]},
        "Мобільний телефон": {"base": 10, "tags": ["communication"]},
        "Сонячна панель": {"base": 40, "tags": ["renewable"]},
        "Газовий балон": {"base": 15, "tags": ["energy"]},
        "Каструля": {"base": 10, "tags": ["food"]},
        "Лопата": {"base": 15, "tags": ["engineering"]},
        "Аптечка першої допомоги": {"base": 15, "tags": ["medical"]},
        "Антибіотики": {"base": 25, "tags": ["medical"]},
        "Теплий одяг": {"base": 20, "tags": ["shielding"]},
        "Респіратор": {"base": 20, "tags": ["radiation_gear"]},
        "Книга по механіці": {"base": 15, "tags": ["engineering"]},
        "Провід електричний": {"base": 5, "tags": ["engineering"]},
        "Годинник": {"base": 10, "tags": ["none"]},
        "Набір насіння": {"base": 15, "tags": ["agriculture"]},
        "Сокира": {"base": 15, "tags": ["weapons"]},
        "Бінокль": {"base": 15, "tags": ["security"]},
        "Аптечка від опіків": {"base": 20, "tags": ["medical"]},
        "Вітаміни": {"base": 15, "tags": ["medical"]},
        "Книга по психології": {"base": 15, "tags": ["psychology"]}
    }
    return item_choice

def get_additional_info():
    additional_info = {
        "Любить гуляти під дощем": {"tag": "personality"},
        "Має два вищих освіти": {"tag": "education"},
        "Колись врятував людину з пожежі": {"tag": "heroism"},
        "Був у зоні бойових дій": {"tag": "military"},
        "Має залежність від кави": {"tag": "habit"},
        "У дитинстві пережив аварію": {"tag": "trauma"},
        "Колись крав у магазині": {"tag": "crime"},
        "Має психічний розлад, але приховує це": {"tag": "mental_health"},
        "Є відеоблогером із великою аудиторією": {"tag": "media"},
        "Володіє технікою медитації": {"tag": "spirituality"},
        "Є фанатом змови про інопланетян": {"tag": "conspiracy"},
        "Має надзвичайно розвинену інтуїцію": {"tag": "intuition"},
        "У минулому — співробітник спецслужб": {"tag": "intelligence"},
        "Має родича в іншому бункері": {"tag": "connection"},
        "Є у відносинах із іншим гравцем": {"tag": "relationship"},
        "Пише книги у жанрі антиутопії": {"tag": "creative"},
        "Має сертифікат психолога": {"tag": "education"},
        "Ненавидить зброю після військових подій": {"tag": "belief"},
        "Колись створив штучний інтелект, який вийшов з-під контролю": {"tag": "science"},
        "Потайки має дитину за межами бункера": {"tag": "family"},
        "Займається чорної магією або ритуалами": {"tag": "occult"},
        "Має фобію темряви": {"tag": "phobia"},
        "Може гіпнотизувати людей": {"tag": "mystic"},
        "Був засуджений, але виправданий": {"tag": "justice"},
        "Страждає на безсоння, але через це має високу концентрацію вночі": {"tag": "condition"}
    }
    return additional_info
