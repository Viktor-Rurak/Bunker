import random, json, os
import urllib.request
from config import rooms, socketio
from helpers import get_reveals_for_round, get_all_players_state


def check_round_complete(code):
    rd = rooms[code]
    if rd['state'] != 'playing':
        return
    active = [p for p in rd['players'].values() if not p['kicked']]
    # Не чекаємо відключених гравців — вони не можуть розкривати
    connected_active = [p for p in active if not p.get('disconnected')]
    if not connected_active:
        return
    reveals_needed = get_reveals_for_round(len(active), rd['round'])
    all_done = all(
        len(p.get('revealed_this_round', [])) >= reveals_needed
        for p in connected_active
    )
    if not all_done:
        return
    rd['state'] = 'voting'
    active_list = [
        {'sid': s, 'name': p['name']}
        for s, p in rd['players'].items() if not p['kicked']
    ]
    socketio.emit('voting_started', {
        'players': active_list,
        'round':   rd['round'] + 1,
    }, to=code)


def finish_voting(code):
    from action_handlers import _give_elimination_card
    rd    = rooms[code]
    votes = rd['votes']
    tally = {}
    for target in votes.values():
        tally[target] = tally.get(target, 0) + 1
    if not tally:
        return
    max_v = max(tally.values())
    top   = [s for s, v in tally.items() if v == max_v]
    kicked_sid  = random.choice(top)
    rd['players'][kicked_sid]['kicked'] = True
    kicked_name = rd['players'][kicked_sid]['name']
    tally_named = {
        rd['players'][s]['name']: v
        for s, v in tally.items()
        if s in rd['players']
    }
    socketio.emit('player_kicked', {
        'sid':   kicked_sid,
        'name':  kicked_name,
        'tally': tally_named,
    }, to=code)
    _give_elimination_card(code, kicked_sid, rd)
    rd['votes'] = {}
    active = [p for p in rd['players'].values() if not p['kicked']]
    bunker_spots = rd.get('initial_player_count', len(rd['players'])) // 2
    if len(active) <= bunker_spots:
        end_game(code)
        return
    rd['state'] = 'playing'
    rd['round'] += 1
    for p in rd['players'].values():
        p['revealed_this_round'] = []
    new_reveals = get_reveals_for_round(len(active), rd['round'])
    for s in rd['players']:
        socketio.emit('new_round', {
            'round':              rd['round'],
            'reveals_this_round': new_reveals,
            'all_players':        get_all_players_state(code, s),
        }, to=s)


def end_game(code):
    rd = rooms[code]
    rd['state'] = 'result'

    survivors = [
        {'sid': s, 'name': p['name'], 'points': round(p['card_dict']['points'], 2)}
        for s, p in rd['players'].items() if not p['kicked']
    ]

    total_player_pts = sum(s['points'] for s in survivors)
    bunker_pts       = round(rd['game'].bunker.points, 2)
    total_pts        = round(total_player_pts + bunker_pts, 2)
    threshold        = rd.get('initial_player_count', len(rd['players'])) * 65
    survived         = total_pts >= threshold
    rd['survived']   = survived

    bunker_spots = rd.get('initial_player_count', len(rd['players'])) // 2
    socketio.emit('game_over', {
        'survivors':     survivors,
        'total_points':  total_pts,
        'bunker_points': bunker_pts,
        'threshold':     threshold,
        'survived':      survived,
        'bunker_spots':  bunker_spots,
    }, to=code)

    import threading
    def _cleanup():
        import time
        time.sleep(600)
        rooms.pop(code, None)
    threading.Thread(target=_cleanup, daemon=True).start()


# ── ДОПОМІЖНА ФУНКЦІЯ ──────────────────────────────────────────────────

def card_dict_to_text(name, card_dict):
    chars = {c['key']: c['value'] for c in card_dict['characteristics']}
    return (
        f"Гравець: {name}. "
        f"Вік: {chars.get('age', '?')}. "
        f"Стать: {chars.get('gender', '?')}. "
        f"Тілобудова: {chars.get('body', '?')}. "
        f"Характер: {chars.get('trait', '?')}. "
        f"Професія: {chars.get('occupation', '?')}. "
        f"Здоров'я: {chars.get('health', '?')}. "
        f"Хобі: {chars.get('hobby', '?')}. "
        f"Фобія: {chars.get('phobia', '?')}. "
        f"Предмет: {chars.get('item', '?')}. "
        f"Додатково: {chars.get('additional', '?')}."
    )


# ── ГЕНЕРАЦІЯ ПРОМПТУ ──────────────────────────────────────────────────

def build_story_prompt(room_data):
    cat  = room_data['game'].to_dict()['catastrophe']
    bunk = room_data['game'].to_dict()['bunker']
    survived = room_data.get('survived', True)

    survivors = [p for p in room_data['players'].values() if not p['kicked']]
    kicked    = [p for p in room_data['players'].values() if p['kicked']]

    survivor_texts = [card_dict_to_text(p['name'], p['card_dict']) for p in survivors]
    kicked_texts   = [card_dict_to_text(p['name'], p['card_dict']) for p in kicked]

    result_line = "Гравці ЗМОГЛИ вижити." if survived else "Гравці НЕ ЗМОГЛИ вижити."

    prompt = (
        "Ти — оповідач постапокаліптичної гри «Бункер». "
        "Напиши коротку художню історію (150–200 слів) українською мовою від третьої особи "
        "про те, як обрані гравці виживали в бункері після катастрофи. "
        "Використай характеристики персонажів — їхні професії, хобі, фобії та предмети — "
        "щоб показати чому саме ці люди вижили, а інші ні. "
        "Зроби акцент на атмосфері виживання та долях персонажів.\n\n"
        f"КАТАСТРОФА: {cat['name']}\n"
        f"{cat['description']}\n\n"
        f"БУНКЕР: {bunk['size']}, запаси: {', '.join(bunk['items'])}, "
        f"розрахований на {bunk['time']}.\n\n"
        "ХТО ПОТРАПИВ У БУНКЕР:\n"
        + "\n".join(f"  - {t}" for t in survivor_texts)
        + "\n\n"
        "ХТО НЕ ПОТРАПИВ:\n"
        + "\n".join(f"  - {t}" for t in kicked_texts)
        + "\n\n"
        f"{result_line}\n\n"
        "Напиши лише саму історію, без заголовків і пояснень."
    )
    return prompt


# ── ВИКЛИК GEMINI ──────────────────────────────────────────────────────

def call_gemini(prompt):
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return "[ API ключ не налаштовано ]"
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"[ Помилка генерації: {e} ]"
