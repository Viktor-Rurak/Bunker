def get_size():
    size_choice = {
    "300 Квадратних метрів": {"area": 300, "capacity": 4},
    "200 Квадратних метрів": {"area": 200, "capacity": 3},
    "150 Квадратних метрів": {"area": 150, "capacity": 3},
    "100 Квадратних метрів": {"area": 100, "capacity": 2},
    "50 Квадратних метрів": {"area": 50, "capacity": 1},
    "30 Квадратних метрів": {"area": 30, "capacity": 1}
    }
    return size_choice

def get_item():
    item_choice = {
        "Склад зброї": {"base": 300, "tags": ["weapons", "security"]},
        "Сонячні панелі": {"base": 300, "tags": ["energy", "renewable"]},
        "Запас питної води на два роки": {"base": 150, "tags": ["water", "sustenance"]},
        "Медичний центр": {"base": 300, "tags": ["medical", "facility"]},
        "Гідропонна ферма": {"base": 250, "tags": ["food", "agriculture", "energy_dependent"]},
        "Система очищення повітря": {"base": 200, "tags": ["air", "medical", "quarantine"]},
        "Генератор біогазу": {"base": 180, "tags": ["energy", "renewable", "agriculture"]},
        "Система відеоспостереження": {"base": 120, "tags": ["security", "technology", "communication"]},
        "Лабораторний набір": {"base": 200, "tags": ["medical", "science", "quarantine", "engineering"]},
        "Запас насіння на 5 років": {"base": 150, "tags": ["agriculture", "food", "renewable"]},
    }

    return item_choice

def get_time():
    time_choice = {
    "Два роки": 300,
    "Рік": 150,
    "6 місяців": 75,
    "3 місяця": 40
}
    return time_choice