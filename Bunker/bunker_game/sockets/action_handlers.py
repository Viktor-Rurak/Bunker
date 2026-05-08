import random
from flask import session, request
from flask_socketio import emit
from config import socketio, rooms
from data.action_data import deal_elimination_card, get_action_cards

def _give_elimination_card(code, kicked_sid, room_data):
    sids = room_data.get('player_sids', list(room_data['players'].keys()))
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
        emit('join_error', {'msg': 'Карту не знайдено або вже використано'})
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
    sids = room_data.get('player_sids', list(room_data['players'].keys()))
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
    sids = room_data.get('player_sids', list(room_data['players'].keys()))
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
    sids = room_data.get('player_sids', list(room_data['players'].keys()))
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


