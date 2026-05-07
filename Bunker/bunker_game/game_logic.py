import random, json, threading
import urllib.request
from config import rooms, socketio
from helpers import get_reveals_for_round, get_all_players_state


def check_round_complete(code):
    rd = rooms[code]
    if rd['state'] != 'playing':
        return
    active = [p for p in rd['players'].values() if not p['kicked']]
    reveals_needed = get_reveals_for_round(len(active), rd['round'])
    all_done = all(
        len(p.get('revealed_this_round', [])) >= reveals_needed
        for p in active
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
    socketio.emit('player_kicked', {
        'sid':   kicked_sid,
        'name':  kicked_name,
        'tally': tally,
    }, to=code)
    _give_elimination_card(code, kicked_sid, rd)
    rd['votes'] = {}
    active = [p for p in rd['players'].values() if not p['kicked']]
    bunker_cap = rd['game'].bunker.size.get('capacity', 2)
    if len(active) <= bunker_cap:
        end_game(code)
        return
    rd['state'] = 'playing'
    rd['round'] += 1
    for p in rd['players'].values():
        p['revealed_this_round'] = []
    new_reveals = get_reveals_for_round(len(active), rd['round'])
    socketio.emit('new_round', {
        'round':             rd['round'],
        'reveals_this_round': new_reveals,
        'all_players': get_all_players_state(
            code, next(iter(rd['players']))
        ),
    }, to=code)


def end_game(code):
    rd = rooms[code]
    rd['state'] = 'result'
    survivors = [
        {'sid': s, 'name': p['name'], 'points': p['card_dict']['points']}
        for s, p in rd['players'].items() if not p['kicked']
    ]
    socketio.emit('game_over', {'survivors': survivors}, to=code)


# ── STORY ──────────────────────────────────────────────────────────────

def build_story_prompt(room_data):
    cat  = room_data['game'].to_dict()['catastrophe']
    bunk = room_data['game'].to_dict()['bunker']
    survivors = [
        p for p in room_data['players'].values() if not p['kicked']
    ]
    kicked = [
        p for p in room_data['players'].values() if p['kicked']
    ]
    lines = [
        "Напиши коротку (150-200 слів) постапокаліптичну історію на основі гри в Бункер.",
        f"Катастрофа: {cat['name']}. {cat['description']}",
        f"Бункер: {bunk['size']}, {', '.join(bunk['items'])}, запаси на {bunk['time']}",
        "Вижили:",
    ]
    for p in survivors:
        cd = p['card_dict']
        chars = {c['key']: c['value'] for c in cd['characteristics']}
        lines.append(
            f"  {p['name']}: {chars.get('occupation','?')}, "
            f"{chars.get('age','?')}, {chars.get('hobby','?')}"
        )
    lines.append("Не потрапили в бункер:")
    for p in kicked:
        cd = p['card_dict']
        chars = {c['key']: c['value'] for c in cd['characteristics']}
        lines.append(
            f"  {p['name']}: {chars.get('occupation','?')}, "
            f"{chars.get('age','?')}"
        )
    lines.append(
        "Пиши від третьої особи, укр. мовою. "
        "Зроби акцент на долях персонажів та атмосфері виживання."
    )
    return '\n'.join(lines)


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
            return (data['candidates'][0]['content']['parts'][0]['text'])
    except Exception as e:
        return f"[ Помилка генерації: {e} ]"


import os
