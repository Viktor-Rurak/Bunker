import random, string
from config import rooms, REVEAL_TABLE
from Game import Game


def get_reveals_for_round(player_count, round_index):
    table = REVEAL_TABLE.get(player_count, REVEAL_TABLE[6])
    if round_index < len(table):
        return table[round_index]
    if len(table) > 3:
        return 1
    return 0


def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def card_to_dict(card, player_id):
    (occ_name, occ_data), = card.occupation.items()
    (body_name, _),       = card.body_constitution.items()
    (trait_name, _),      = card.human_trait.items()
    (health_name, _),     = card.health.items()
    (hobby_name, _),      = card.hobby.items()
    (phobia_name, _),     = card.phobia.items()
    (item_name, _),       = card.item.items()
    (add_name, _),        = card.additional_introduction.items()
    return {
        "player_id": player_id,
        "points": round(card.points, 2),
        "characteristics": [
            {"key": "occupation", "label": "Професія",
             "value": occ_name,    "icon": "💼"},
            {"key": "age",        "label": "Вік",
             "value": f"{card.age['age']} років "
                      f"{'(батьківство)' if card.age['parenthood'] else ''}",
             "icon": "🎂"},
            {"key": "gender",     "label": "Стать",
             "value": "Чоловік" if card.gender == "male" else "Жінка",
             "icon": "👤"},
            {"key": "body",       "label": "Тілобудова",
             "value": body_name,   "icon": "🏃"},
            {"key": "trait",      "label": "Характер",
             "value": trait_name,  "icon": "🧠"},
            {"key": "health",     "label": "Здоров'я",
             "value": health_name, "icon": "❤️"},
            {"key": "hobby",      "label": "Хобі",
             "value": hobby_name,  "icon": "🎯"},
            {"key": "phobia",     "label": "Фобія",
             "value": phobia_name, "icon": "😨"},
            {"key": "item",       "label": "Предмет",
             "value": item_name,   "icon": "🎒"},
            {"key": "additional", "label": "Додаткова інфо",
             "value": add_name,    "icon": "📋"},
        ],
        "action_cards": [dict(ac, used=False) for ac in card.action_cards],
    }


def get_lobby_state(code):
    rd = rooms[code]
    return {
        'players': [
            {'sid': s, 'name': p['name'], 'is_host': p['is_host']}
            for s, p in rd['players'].items()
        ]
    }


def get_all_players_state(code, my_sid):
    rd = rooms[code]
    result = []
    for s, p in rd['players'].items():
        revealed = [
            c for c in p.get('card_dict', {}).get('characteristics', [])
            if c['key'] in p.get('revealed', [])
        ]
        total = len(p.get('card_dict', {}).get('characteristics', []))
        result.append({
            'sid':                s,
            'name':               p['name'],
            'is_me':              s == my_sid,
            'is_host':            p.get('is_host', False),
            'kicked':             p['kicked'],
            'revealed':           revealed,
            'total_characteristics': total,
            'hidden_count':       total - len(revealed),
        })
    return result


def get_round_keys(round_idx, reveals_allowed, all_revealed):
    return all_revealed[
        round_idx * reveals_allowed:(round_idx + 1) * reveals_allowed
    ]
