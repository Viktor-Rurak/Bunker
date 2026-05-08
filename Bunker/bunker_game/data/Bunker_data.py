def get_size():
    size_choice = {
    "300 Квадратних метрів": {"area": 100, "capacity": 4},
    "200 Квадратних метрів": {"area": 70, "capacity": 3},
    "150 Квадратних метрів": {"area": 50, "capacity": 3},
    "100 Квадратних метрів": {"area": 30, "capacity": 2},
    "50 Квадратних метрів": {"area": 20, "capacity": 1},
    }
    return size_choice

def get_item():
    item_choice = {

    "Гідропонна ферма": {"base": 85, "tags": ["food", "agriculture", "energy_dependent"]},
}
    return item_choice

def get_time():
    time_choice = {
    "Два роки": 100,
    "Рік": 50,
    "6 місяців": 25,
    "3 місяця": 15
}
    return time_choice