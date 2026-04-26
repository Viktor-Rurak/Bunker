import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
import random, string, json

from Game import Game

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bunker-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Зберігаємо всі кімнати
rooms = {}

# Таблиця відкриттів характеристик
REVEAL_TABLE = {
    6:       [3, 3, 2],
    7:       [3, 2, 2, 1],
    8:       [3, 2, 2, 1],
    9:       [3, 2, 1, 1],
    10:      [3, 2, 1, 1],
    11:      [2, 2, 1, 1],
    12:      [2, 2, 1, 1],
    13:      [2, 1, 1, 1],
    14:      [2, 1, 1, 1],
    15:      [2, 1, 1, 1],
}

def get_reveals_for_round(player_count, round_index):
    table = REVEAL_TABLE.get(player_count, REVEAL_TABLE[6])
    if round_index < len(table):
        return table[round_index]
    # з 4-го раунду і далі — по 1 (якщо є в таблиці)
    if len(table) > 3:
        return 1
    return 0

def card_to_dict(card, player_id):
    """Конвертує картку гравця в словник"""
    (occ_name, occ_data), = card.occupation.items()
    (body_name, _), = card.body_constitution.items()
    (trait_name, _), = card.human_trait.items()
    (health_name, health_data), = card.health.items()
    (hobby_name, _), = card.hobby.items()
    (phobia_name, _), = card.phobia.items()
    (item_name, _), = card.item.items()
    (add_name, _), = card.additional_introduction.items()

    return {
        "player_id": player_id,
        "points": round(card.points, 2),
        "characteristics": [
            {"key": "occupation",    "label": "Професія",          "value": occ_name,    "icon": "💼"},
            {"key": "age",           "label": "Вік",               "value": f"{card.age['age']} років {'(батьківство)' if card.age['parenthood'] else ''}", "icon": "🎂"},
            {"key": "gender",        "label": "Стать",             "value": "Чоловік" if card.gender == "male" else "Жінка", "icon": "👤"},
            {"key": "body",          "label": "Тілобудова",        "value": body_name,   "icon": "🏃"},
            {"key": "trait",         "label": "Характер",          "value": trait_name,  "icon": "🧠"},
            {"key": "health",        "label": "Здоров'я",          "value": health_name, "icon": "❤️"},
            {"key": "hobby",         "label": "Хобі",              "value": hobby_name,  "icon": "🎯"},
            {"key": "phobia",        "label": "Фобія",             "value": phobia_name, "icon": "😨"},
            {"key": "item",          "label": "Предмет",           "value": item_name,   "icon": "🎒"},
            {"key": "additional",    "label": "Додаткова інфо",    "value": add_name,    "icon": "📋"},
        ]
    }

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/room/<code>')
def room(code):
    return render_template('game.html', room_code=code)

@app.route('/api/create_room', methods=['POST'])
def create_room():
    data = request.json
    name = data.get('name', 'Хост').strip()
    if not name:
        return jsonify({"error": "Введіть ім'я"}), 400

    code = generate_room_code()
    while code in rooms:
        code = generate_room_code()

    rooms[code] = {
        "host": None,  # буде встановлено при підключенні через сокет
        "host_name": name,
        "players": {},   # sid -> {name, card_dict, revealed: [], kicked: False}
        "game": None,
        "state": "lobby",  # lobby | playing | voting | result
        "round": 0,
        "votes": {},
        "kicked_players": [],
    }
    return jsonify({"code": code})

# ─── SOCKET EVENTS ───────────────────────────────────────────────────

@socketio.on('join_room')
def on_join(data):
    code = data.get('code', '').upper()
    name = data.get('name', '').strip()

    if code not in rooms:
        emit('error', {'msg': 'Кімнату не знайдено'})
        return
    if not name:
        emit('error', {'msg': 'Введіть ім\'я'})
        return

    room_data = rooms[code]

    if room_data['state'] != 'lobby':
        emit('error', {'msg': 'Гра вже почалась'})
        return

    sid = request.sid
    is_host = len(room_data['players']) == 0

    if is_host:
        room_data['host'] = sid

    room_data['players'][sid] = {
        'name': name,
        'card_dict': None,
        'revealed': [],
        'kicked': False,
        'is_host': is_host,
    }

    join_room(code)
    emit('joined', {
        'sid': sid,
        'is_host': is_host,
        'code': code,
        'name': name
    })
    emit('lobby_update', get_lobby_state(code), to=code)


@socketio.on('start_game')
def on_start(data):
    print("=== START GAME CALLED ===", data)  # ← додай
    code = data.get('code', '').upper()
    if code not in rooms:
        print("Room not found:", code, "Rooms:", list(rooms.keys()))  # ← додай
        return

    room_data = rooms[code]
    sid = request.sid

    if room_data['host'] != sid:
        emit('error', {'msg': 'Тільки хост може почати гру'})
        return

    player_count = len(room_data['players'])
    if player_count < 2:
        emit('error', {'msg': 'Потрібно мінімум 2 гравці'})
        return

    # Генеруємо гру
    game = Game()
    game.create_cards(player_count)
    room_data['game'] = game
    room_data['state'] = 'playing'
    room_data['round'] = 0

    # Роздаємо картки гравцям
    sids = list(room_data['players'].keys())
    for i, s in enumerate(sids):
        card = game.cards[i]
        room_data['players'][s]['card_dict'] = card_to_dict(card, s)
        room_data['players'][s]['revealed'] = []

    game_info = game.to_dict()

    # Кожному гравцю відправляємо його картку
    for s in sids:
        socketio.emit('game_started', {
            'game_info': game_info,
            'my_card': room_data['players'][s]['card_dict'],
            'round': 0,
            'reveals_this_round': get_reveals_for_round(player_count, 0),
            'all_players': get_all_players_state(code, s)
        }, to=s)


@socketio.on('reveal_characteristic')
def on_reveal(data):
    code = data.get('code', '').upper()
    key = data.get('key')
    sid = request.sid

    if code not in rooms:
        return

    room_data = rooms[code]
    player = room_data['players'].get(sid)
    if not player or player['kicked']:
        return

    player_count = len([p for p in room_data['players'].values() if not p['kicked']])
    round_idx = room_data['round']
    reveals_allowed = get_reveals_for_round(player_count, round_idx)

    # Скільки вже відкрито в цьому раунді
    already_revealed_this_round = len([k for k in player['revealed']
                                       if k in get_round_keys(round_idx, reveals_allowed, player['revealed'])])

    revealed_in_round = player.get('revealed_this_round', [])

    if key in player['revealed']:
        emit('error', {'msg': 'Вже відкрито'})
        return
    if len(revealed_in_round) >= reveals_allowed:
        emit('error', {'msg': f'В цьому раунді можна відкрити лише {reveals_allowed} характеристики'})
        return

    player['revealed'].append(key)
    if 'revealed_this_round' not in player:
        player['revealed_this_round'] = []
    player['revealed_this_round'].append(key)

    # Розсилаємо всім оновлений стан гравця
    socketio.emit('player_revealed', {
        'sid': sid,
        'name': player['name'],
        'key': key,
        'value': next((c['value'] for c in player['card_dict']['characteristics'] if c['key'] == key), '?'),
        'label': next((c['label'] for c in player['card_dict']['characteristics'] if c['key'] == key), '?'),
        'icon': next((c['icon'] for c in player['card_dict']['characteristics'] if c['key'] == key), ''),
    }, to=code)

    # Перевіряємо чи всі відкрили потрібну кількість
    check_round_complete(code)


@socketio.on('vote')
def on_vote(data):
    code = data.get('code', '').upper()
    target_sid = data.get('target')
    sid = request.sid

    if code not in rooms:
        return

    room_data = rooms[code]
    if room_data['state'] != 'voting':
        return

    room_data['votes'][sid] = target_sid
    active_players = [s for s, p in room_data['players'].items() if not p['kicked']]

    socketio.emit('vote_update', {
        'votes_cast': len(room_data['votes']),
        'votes_needed': len(active_players)
    }, to=code)

    # Якщо всі проголосували
    if len(room_data['votes']) >= len(active_players):
        finish_voting(code)


@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    for code, room_data in rooms.items():
        if sid in room_data['players']:
            room_data['players'][sid]['disconnected'] = True
            name = room_data['players'][sid]['name']
            socketio.emit('player_left', {'sid': sid, 'name': name}, to=code)
            break


# ─── HELPERS ────────────────────────────────────────────────────────

def get_lobby_state(code):
    room_data = rooms[code]
    return {
        'players': [
            {'sid': s, 'name': p['name'], 'is_host': p['is_host']}
            for s, p in room_data['players'].items()
        ]
    }

def get_all_players_state(code, my_sid):
    room_data = rooms[code]
    result = []
    for s, p in room_data['players'].items():
        if p['kicked']:
            continue
        revealed_chars = []
        for key in p['revealed']:
            char = next((c for c in p['card_dict']['characteristics'] if c['key'] == key), None)
            if char:
                revealed_chars.append(char)
        result.append({
            'sid': s,
            'name': p['name'],
            'is_me': s == my_sid,
            'is_host': p['is_host'],
            'revealed': revealed_chars,
            'total_characteristics': len(p['card_dict']['characteristics']) if p['card_dict'] else 10,
        })
    return result

def get_round_keys(round_idx, reveals_allowed, all_revealed):
    # повертає ключі відкриті саме в цьому раунді
    return all_revealed[-(reveals_allowed):]

def check_round_complete(code):
    room_data = rooms[code]
    if room_data['state'] != 'playing':
        return

    active_players = [p for p in room_data['players'].values() if not p['kicked']]
    player_count = len(active_players)
    round_idx = room_data['round']
    reveals_needed = get_reveals_for_round(player_count, round_idx)

    if reveals_needed == 0:
        return

    all_done = all(
        len(p.get('revealed_this_round', [])) >= reveals_needed
        for p in active_players
    )

    if all_done:
        # Починаємо голосування
        room_data['state'] = 'voting'
        room_data['votes'] = {}
        active_list = [
            {'sid': s, 'name': p['name']}
            for s, p in room_data['players'].items()
            if not p['kicked']
        ]
        socketio.emit('voting_started', {
            'players': active_list,
            'round': round_idx + 1
        }, to=code)


def finish_voting(code):
    room_data = rooms[code]
    votes = room_data['votes']

    # Рахуємо голоси
    tally = {}
    for voter, target in votes.items():
        tally[target] = tally.get(target, 0) + 1

    if not tally:
        return

    max_votes = max(tally.values())
    kicked_candidates = [s for s, v in tally.items() if v == max_votes]
    kicked_sid = random.choice(kicked_candidates)  # при рівності — рандом

    kicked_name = room_data['players'][kicked_sid]['name']
    room_data['players'][kicked_sid]['kicked'] = True
    room_data['kicked_players'].append({'sid': kicked_sid, 'name': kicked_name})

    socketio.emit('player_kicked', {
        'sid': kicked_sid,
        'name': kicked_name,
        'tally': {room_data['players'][s]['name']: v for s, v in tally.items() if s in room_data['players']}
    }, to=code)

    # Перевіряємо чи гра закінчена
    active_players = [s for s, p in room_data['players'].items() if not p['kicked']]
    player_count_remaining = len(active_players)

    # Якщо залишилось мало гравців або раунди закінчились
    next_round = room_data['round'] + 1
    next_reveals = get_reveals_for_round(player_count_remaining, next_round)

    if player_count_remaining <= 1 or next_reveals == 0:
        end_game(code)
        return

    # Наступний раунд
    room_data['round'] = next_round
    room_data['state'] = 'playing'
    for p in room_data['players'].values():
        p['revealed_this_round'] = []

    socketio.emit('next_round', {
        'round': next_round,
        'reveals_this_round': next_reveals,
        'all_players': {
            s: get_all_players_state(code, s)
            for s in active_players
        }
    }, to=code)

    # Персональні оновлення
    for s in active_players:
        socketio.emit('round_update', {
            'round': next_round,
            'reveals_this_round': next_reveals,
            'all_players': get_all_players_state(code, s)
        }, to=s)


def end_game(code):
    room_data = rooms[code]
    room_data['state'] = 'result'

    # Рахуємо фінальні очки
    survivors = []
    for s, p in room_data['players'].items():
        if not p['kicked'] and p['card_dict']:
            card = room_data['game'].cards[list(room_data['players'].keys()).index(s)]
            survivors.append({
                'sid': s,
                'name': p['name'],
                'points': round(card.points, 2),
                'card': p['card_dict']
            })

    survivors.sort(key=lambda x: x['points'], reverse=True)

    bunker_points = room_data['game'].bunker.points
    total_survivor_points = sum(s['points'] for s in survivors)
    survived = total_survivor_points >= bunker_points * 0.6

    socketio.emit('game_over', {
        'survivors': survivors,
        'kicked': room_data['kicked_players'],
        'bunker_points': bunker_points,
        'total_points': round(total_survivor_points, 2),
        'survived': survived
    }, to=code)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
