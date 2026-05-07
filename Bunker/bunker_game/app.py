import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
import random, string, json, threading
import urllib.request
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
        ],
        "action_cards": [
            dict(ac, used=False)
            for ac in card.action_cards
        ],
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
        # Спроба переп'єднання — шукаємо гравця з таким іменем
        print(f"[RECONNECT] Спроба: name={name!r}, new_sid={request.sid}")
        print(f"[RECONNECT] Гравці в кімнаті: {[(p['name'], s) for s,p in room_data['players'].items()]}")
        old_sid = next(
            (s for s, p in room_data['players'].items() if p['name'] == name),
            None
        )
        print(f"[RECONNECT] old_sid знайдено: {old_sid}")
        if not old_sid:
            emit('error', {'msg': 'Гра вже почалась'})
            return
        _reconnect_player(code, old_sid, request.sid, room_data)
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
    code = data.get('code', '').upper()
    if code not in rooms:
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
        room_data['players'][s]['action_cards'] = [
            dict(ac)
            for ac in room_data['players'][s]['card_dict']['action_cards']
        ]
        room_data['players'][s]['elimination_card'] = None
        room_data['players'][s]['alliances'] = []

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
    _give_elimination_card(code, kicked_sid, room_data)

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


# ── STORY GENERATION ──────────────────────────────────────────────────

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Замініть на свій ключ

def build_story_prompt(room_data):
    game     = room_data['game']
    cat_name = game.catastrophe.catastrophe['name']
    cat_desc = game.catastrophe.catastrophe['modifiers']['description']
    bunker   = game.to_dict()['bunker']

    sids     = list(room_data['players'].keys())
    survivors = []
    kicked    = []

    for i, (sid, p) in enumerate(room_data['players'].items()):
        card = game.cards[i] if i < len(game.cards) else None
        if not card:
            continue
        card_dict = p.get('card_dict', {})
        chars     = {c['key']: c['value'] for c in card_dict.get('characteristics', [])}

        info = {
            'name':       p['name'],
            'points':     round(card.points, 1),
            'profession': chars.get('occupation', '?'),
            'age':        chars.get('age', '?'),
            'health':     chars.get('health', '?'),
            'hobby':      chars.get('hobby', '?'),
            'item':       chars.get('item', '?'),
            'additional': chars.get('additional', '?'),
        }

        if p['kicked']:
            kicked.append(info)
        else:
            survivors.append(info)

    survived     = sum(s['points'] for s in survivors) >= bunker['points'] * 0.6
    outcome_text = "ВИЖИЛИ" if survived else "ЗАГИНУЛИ"

    lines = [
        f"Катастрофа: {cat_name}",
        f"Опис: {cat_desc}",
        f"",
        f"Бункер: {bunker['size']}, {', '.join(bunker['items'])}, запаси на {bunker['time']}",
        f"Поріг виживання: {bunker['points']} балів",
        f"",
        f"Гравці що потрапили в бункер ({outcome_text}):",
    ]
    for s in survivors:
        lines.append(
            f"- {s['name']}: {s['profession']}, {s['age']}, "
            f"здоров'я: {s['health']}, хобі: {s['hobby']}, "
            f"предмет: {s['item']}, {s['additional']} ({s['points']} балів)"
        )

    lines += ["", "Вигнані гравці:"]
    for k in kicked:
        lines.append(f"- {k['name']}: {k['profession']}, {k['age']} ({k['points']} балів)")

    lines += [
        "",
        f"Результат: команда {'вижила' if survived else 'не вижила'} після катастрофи.",
        "",
        "Напиши захоплюючу, деталізовану історію (400-500 слів) українською мовою про те, "
        "як ці люди провели час в бункері. Враховуй їхні професії, предмети та особливості. "
        "Якщо вижили — опиши як вони справились. Якщо ні — опиши трагічну розв'язку. "
        "Використовуй імена гравців. Стиль — пост-апокаліптична проза."
    ]

    return '\n'.join(lines)


def call_gemini(prompt):
    url  = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data['candidates'][0]['content']['parts'][0]['text']


@socketio.on('generate_story')
def on_generate_story(data):
    code = data.get('code', '').upper()
    if code not in rooms:
        return

    room_data = rooms[code]

    def generate():
        try:
            prompt = build_story_prompt(room_data)
            story  = call_gemini(prompt)
            socketio.emit('story_ready', {'story': story}, to=code)
        except Exception as e:
            socketio.emit('story_ready', {
                'story': f'Не вдалося згенерувати історію: {str(e)}'
            }, to=code)

    threading.Thread(target=generate, daemon=True).start()

# ─── ACTION CARDS ─────────────────────────────────────────────────────────────

def _give_elimination_card(code, kicked_sid, room_data):
    sids = list(room_data['players'].keys())
    if kicked_sid not in sids:
        return
    idx = sids.index(kicked_sid)
    game = room_data['game']
    if idx >= len(game.cards):
        return
    elim = game.cards[idx].eliminate()
    elim_dict = dict(elim, used=False)
    room_data['players'][kicked_sid]['elimination_card'] = elim_dict
    socketio.emit('got_elimination_card', {'card': elim_dict}, to=kicked_sid)


def _find_action_card(player, card_name, is_elim):
    if is_elim:
        ec = player.get('elimination_card')
        if ec and not ec.get('used') and ec['name'] == card_name:
            return ec
        return None
    for ac in player.get('action_cards', []):
        if ac['name'] == card_name and not ac.get('used'):
            return ac
    return None


def _check_immunity(room_data, target_sid):
    target = room_data['players'].get(target_sid, {})
    for ac in target.get('action_cards', []):
        if ac['name'] == 'Імунітет' and not ac.get('used'):
            ac['used'] = True
            socketio.emit('immunity_triggered', {}, to=target_sid)
            return True
    return False


@socketio.on('use_action_card')
def on_use_action_card(data):
    code     = data.get('code', '').upper()
    name     = data.get('card_name')
    target   = data.get('target_sid')
    char_key = data.get('characteristic_key')
    is_elim  = data.get('is_elimination', False)
    sid      = request.sid

    if code not in rooms:
        return
    room_data = rooms[code]
    player = room_data['players'].get(sid)
    if not player:
        return

    ac = _find_action_card(player, name, is_elim)
    if not ac:
        emit('error', {'msg': 'Карту не знайдено або вже використано'})
        return

    # Перевірка Імунітету (тільки для карт з ціллю)
    if target and not is_elim:
        if _check_immunity(room_data, target):
            ac['used'] = True
            t_name = room_data['players'].get(target, {}).get('name', '?')
            socketio.emit('action_blocked', {
                'card_name': name,
                'user_name': player['name'],
                'blocker_name': t_name,
            }, to=code)
            return

    effect = _apply_effect(code, sid, ac, target, char_key, room_data)
    ac['used'] = True

    socketio.emit('action_card_result', {
        'card_name':    name,
        'user_name':    player['name'],
        'is_elimination': is_elim,
        'effect':       effect,
    }, to=code)

    if effect.get('_private_to'):
        socketio.emit('action_card_private',
                      effect.get('_private_data', {}),
                      to=effect['_private_to'])


def _apply_effect(code, user_sid, ac, target_sid, char_key, room_data):
    name = ac['name']
    if name == 'Детектив':
        return _fx_detective(code, target_sid, char_key, room_data)
    if name == 'Скандал':
        return _fx_scandal(code, target_sid, room_data)
    if name == 'Анонімне донесення':
        return _fx_anonymous(user_sid, target_sid, room_data)
    if name == 'Ворожий бункер':
        return _fx_enemy_bunker(code, user_sid, room_data)
    if name == 'Прокляття':
        return _fx_curse(code, target_sid, room_data)
    if name == 'Зрада':
        return _fx_betrayal(code, target_sid, room_data)
    if name == 'Рокіровка':
        return _fx_swap(code, user_sid, target_sid, ac, room_data)
    if name == 'Маскарад':
        return _fx_masquerade(code, user_sid, target_sid, room_data)
    if name == 'Симбіоз':
        return _fx_symbiosis(code, user_sid, target_sid, room_data)
    if name == 'Еволюція':
        return _fx_evolution(code, user_sid, char_key, room_data)
    return {'type': name.lower().replace(' ', '_')}


# ── Детектив ──
def _fx_detective(code, target_sid, char_key, room_data):
    target = room_data['players'].get(target_sid)
    if not target or not char_key:
        return {'type': 'error'}
    char = next(
        (c for c in target['card_dict']['characteristics']
         if c['key'] == char_key), None
    )
    if not char:
        return {'type': 'error'}
    if char_key not in target['revealed']:
        target['revealed'].append(char_key)
    socketio.emit('player_revealed', {
        'sid': target_sid, 'name': target['name'],
        'key': char_key, 'value': char['value'],
        'label': char['label'], 'icon': char['icon'],
    }, to=code)
    return {'type': 'reveal',
            'target_name': target['name'],
            'char_label': char['label'],
            'char_value': char['value']}


# ── Скандал ──
def _fx_scandal(code, target_sid, room_data):
    target = room_data['players'].get(target_sid)
    if not target:
        return {'type': 'error'}
    hidden = [
        c for c in target['card_dict']['characteristics']
        if c['key'] not in target['revealed']
    ]
    if not hidden:
        return {'type': 'already_revealed', 'target_name': target['name']}
    char = random.choice(hidden)
    target['revealed'].append(char['key'])
    socketio.emit('player_revealed', {
        'sid': target_sid, 'name': target['name'],
        'key': char['key'], 'value': char['value'],
        'label': char['label'], 'icon': char['icon'],
    }, to=code)
    return {'type': 'reveal',
            'target_name': target['name'],
            'char_label': char['label'],
            'char_value': char['value']}


# ── Анонімне донесення ──
def _fx_anonymous(user_sid, target_sid, room_data):
    target = room_data['players'].get(target_sid)
    if not target:
        return {'type': 'error'}
    hidden = [
        c for c in target['card_dict']['characteristics']
        if c['key'] not in target['revealed']
    ]
    return {
        'type': 'anonymous_report',
        'target_name': target['name'],
        '_private_to': user_sid,
        '_private_data': {
            'type': 'anonymous_report',
            'target_name': target['name'],
            'hidden_chars': hidden,
        },
    }


# ── Ворожий бункер ──
def _fx_enemy_bunker(code, user_sid, room_data):
    sids = list(room_data['players'].keys())
    if user_sid not in sids:
        return {'type': 'error'}
    game = room_data['game']
    u_idx = sids.index(user_sid)
    if u_idx >= len(game.cards):
        return {'type': 'error'}
    penalty = round(game.cards[u_idx].points * 0.3, 2)
    active = [(s, p) for s, p in room_data['players'].items()
              if not p['kicked']]
    for s, p in active:
        idx = sids.index(s)
        if idx < len(game.cards):
            game.cards[idx].points = max(0, game.cards[idx].points - penalty)
            p['card_dict']['points'] = round(game.cards[idx].points, 2)
    return {
        'type': 'enemy_bunker',
        'penalty': penalty,
        'attacker_name': room_data['players'][user_sid]['name'],
    }


# ── Прокляття ──
def _fx_curse(code, target_sid, room_data):
    target = room_data['players'].get(target_sid)
    if not target or target['kicked']:
        return {'type': 'error'}
    sids = list(room_data['players'].keys())
    if target_sid not in sids:
        return {'type': 'error'}
    game = room_data['game']
    idx  = sids.index(target_sid)
    if idx < len(game.cards):
        game.cards[idx].points *= 0.85
        target['card_dict']['points'] = round(game.cards[idx].points, 2)
    return {
        'type': 'curse',
        'target_name': target['name'],
        'new_points': target['card_dict']['points'],
    }


# ── Зрада ──
def _fx_betrayal(code, target_sid, room_data):
    target = room_data['players'].get(target_sid)
    if not target:
        return {'type': 'error'}
    count = 0
    for char in target['card_dict']['characteristics']:
        if char['key'] not in target['revealed']:
            target['revealed'].append(char['key'])
            socketio.emit('player_revealed', {
                'sid': target_sid, 'name': target['name'],
                'key': char['key'], 'value': char['value'],
                'label': char['label'], 'icon': char['icon'],
            }, to=code)
            count += 1
    return {'type': 'betrayal',
            'target_name': target['name'],
            'revealed_count': count}


# ── Рокіровка ──
def _fx_swap(code, user_sid, target_sid, ac, room_data):
    char_key = ac.get('characteristic')
    if not char_key:
        return {'type': 'error'}
    user   = room_data['players'][user_sid]
    target = room_data['players'].get(target_sid)
    if not target:
        return {'type': 'error'}
    uc = next((c for c in user['card_dict']['characteristics']
               if c['key'] == char_key), None)
    tc = next((c for c in target['card_dict']['characteristics']
               if c['key'] == char_key), None)
    if not uc or not tc:
        return {'type': 'error'}
    uc['value'], tc['value'] = tc['value'], uc['value']
    return {'type': 'swap',
            'char_key': char_key,
            'char_label': uc['label'],
            'user_name': user['name'],
            'target_name': target['name']}


# ── Маскарад ──
def _fx_masquerade(code, user_sid, target_sid, room_data):
    return _fx_swap(code, user_sid, target_sid,
                    {'characteristic': 'occupation'}, room_data)


# ── Симбіоз ──
def _fx_symbiosis(code, user_sid, target_sid, room_data):
    user   = room_data['players'][user_sid]
    target = room_data['players'].get(target_sid)
    if not target:
        return {'type': 'error'}
    user.setdefault('alliances', []).append(target_sid)
    target.setdefault('alliances', []).append(user_sid)
    sids = list(room_data['players'].keys())
    game = room_data['game']
    for sid in (user_sid, target_sid):
        if sid in sids:
            idx = sids.index(sid)
            if idx < len(game.cards):
                game.cards[idx].points *= 1.1
                room_data['players'][sid]['card_dict']['points'] = round(
                    game.cards[idx].points, 2
                )
    return {'type': 'symbiosis',
            'user_name': user['name'],
            'target_name': target['name']}


# ── Еволюція ──
def _fx_evolution(code, user_sid, char_key, room_data):
    if not char_key:
        return {'type': 'error'}
    from data.card_data import (
        get_body_constitution, get_occupation_choice, get_traits,
        get_choice_disease, get_hobbies_choice, get_choice_phobia,
        get_item_choice, get_additional_info,
    )
    import random as _r
    pool_map = {
        'body':       lambda: _r.choice(list(get_body_constitution().keys())),
        'occupation': lambda: _r.choice(list(get_occupation_choice().keys())),
        'trait':      lambda: _r.choice(list(get_traits().keys())),
        'health':     lambda: _r.choice(list(get_choice_disease().keys())),
        'hobby':      lambda: _r.choice(list(get_hobbies_choice().keys())),
        'phobia':     lambda: _r.choice(list(get_choice_phobia().keys())),
        'item':       lambda: _r.choice(list(get_item_choice().keys())),
        'additional': lambda: _r.choice(list(get_additional_info().keys())),
    }
    gen = pool_map.get(char_key)
    if not gen:
        return {'type': 'error'}
    new_val = gen()
    player = room_data['players'][user_sid]
    char = next(
        (c for c in player['card_dict']['characteristics']
         if c['key'] == char_key), None
    )
    if not char:
        return {'type': 'error'}
    char['value'] = new_val
    return {'type': 'evolution',
            'char_label': char['label'],
            'new_value': new_val}


# ─── RECONNECT ────────────────────────────────────────────────────────────────

def _reconnect_player(code, old_sid, new_sid, room_data):
    print(f"[RECONNECT] _reconnect_player: {old_sid} -> {new_sid}")
    p = room_data['players'].pop(old_sid)
    room_data['players'][new_sid] = p

    if room_data['host'] == old_sid:
        room_data['host'] = new_sid
    if old_sid in room_data.get('votes', {}):
        room_data['votes'][new_sid] = room_data['votes'].pop(old_sid)

    join_room(code)

    print(f"[RECONNECT] Sending 'joined' to {new_sid}")
    # Всі особисті emit йдуть явно через to=new_sid
    socketio.emit('joined', {
        'sid': new_sid,
        'is_host': p['is_host'],
        'code': code,
        'name': p['name'],
    }, to=new_sid)

    if p['kicked']:
        if p.get('elimination_card'):
            socketio.emit(
                'got_elimination_card',
                {'card': p['elimination_card']},
                to=new_sid
            )
        socketio.emit(
            'player_reconnected', {'sid': new_sid, 'name': p['name']}, to=code
        )
        return

    game = room_data['game']
    active = [pl for pl in room_data['players'].values() if not pl['kicked']]
    reveals_allowed = get_reveals_for_round(len(active), room_data['round'])
    reveals_done = len(p.get('revealed_this_round', []))

    print(f"[RECONNECT] Sending 'game_started' to {new_sid}, card_dict is None: {p['card_dict'] is None}")
    socketio.emit('game_started', {
        'game_info': game.to_dict(),
        'my_card': p['card_dict'],
        'round': room_data['round'],
        'reveals_this_round': reveals_allowed,
        'all_players': get_all_players_state(code, new_sid),
        'previously_revealed': p['revealed'],
        'reveals_done_this_round': reveals_done,
    }, to=new_sid)

    if room_data['state'] == 'voting':
        active_list = [
            {'sid': s, 'name': pl['name']}

            for s, pl in room_data['players'].items()
            if not pl['kicked']
        ]
        socketio.emit('voting_started', {
            'players': active_list,
            'round': room_data['round'] + 1,
        }, to=new_sid)

    if p.get('elimination_card'):
        socketio.emit(
            'got_elimination_card',
            {'card': p['elimination_card']},
            to=new_sid
        )

    socketio.emit(
        'player_reconnected', {'sid': new_sid, 'name': p['name']}, to=code
    )
