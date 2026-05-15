from flask import session, request
from flask_socketio import join_room, emit
from config import app, socketio, rooms
from helpers import (card_to_dict, get_lobby_state, get_all_players_state,
                     get_reveals_for_round)
from game_logic import check_round_complete, finish_voting, build_story_prompt, call_gemini
from Game import Game
import threading


@socketio.on('join_room')
def on_join(data):
    code     = data.get('code', '').upper()
    uid      = session.get('user_id')
    username = session.get('username')

    if not uid:
        emit('join_error', {'msg': 'Не авторизовано. Оновіть сторінку та увійдіть знову.'})
        return
    if code not in rooms:
        emit('join_error', {'msg': 'Кімнату не знайдено'})
        return

    rd = rooms[code]

    if rd['state'] != 'lobby':
        from reconnect import _reconnect_player
        old_sid = next(
            (s for s, p in rd['players'].items()
             if p.get('user_id') == uid), None
        )
        if not old_sid:
            emit('join_error', {'msg': 'Гра вже почалась'})
            return
        _reconnect_player(code, old_sid, request.sid, rd)
        return

    sid = request.sid
    old = next((s for s, p in rd['players'].items()
                if p.get('user_id') == uid), None)
    if old and old != sid:
        rd['players'].pop(old)

    is_host = (uid == rd.get('host_user_id'))
    if is_host:
        rd['host'] = sid

    rd['players'][sid] = {
        'user_id':  uid,
        'name':     username,
        'card_dict': None,
        'revealed': [],
        'kicked':   False,
        'is_host':  is_host,
    }
    join_room(code)
    emit('joined', {'sid': sid, 'is_host': is_host,
                    'code': code, 'name': username})
    emit('lobby_update', get_lobby_state(code), to=code)


@socketio.on('start_game')
def on_start(data):
    code = data.get('code', '').upper()
    if code not in rooms:
        return
    rd  = rooms[code]
    sid = request.sid
    if rd['host'] != sid:
        emit('join_error', {'msg': 'Тільки хост може почати гру'})
        return
    player_count = len(rd['players'])
    if player_count < 6:
        emit('join_error', {'msg': 'Потрібно мінімум 6 гравців'})
        return
    game = Game()
    game.create_cards(player_count)
    rd['game']                 = game
    rd['state']                = 'playing'
    rd['round']                = 0
    rd['initial_player_count'] = player_count
    sids = list(rd['players'].keys())
    rd['player_sids'] = sids[:]
    for i, s in enumerate(sids):
        card = game.cards[i]
        rd['players'][s]['card_dict'] = card_to_dict(card, s)
        rd['players'][s]['revealed']  = []
        rd['players'][s]['action_cards'] = [
            dict(ac) for ac in rd['players'][s]['card_dict']['action_cards']
        ]
        rd['players'][s]['elimination_card'] = None
    game_info    = game.to_dict()
    bunker_spots = player_count // 2
    for s in sids:
        socketio.emit('game_started', {
            'game_info':          game_info,
            'my_card':            rd['players'][s]['card_dict'],
            'round':              0,
            'reveals_this_round': get_reveals_for_round(player_count, 0),
            'all_players':        get_all_players_state(code, s),
            'bunker_spots':       bunker_spots,
        }, to=s)


@socketio.on('reveal_characteristic')
def on_reveal(data):
    code = data.get('code', '').upper()
    key  = data.get('key')
    sid  = request.sid
    if code not in rooms:
        return
    rd     = rooms[code]
    player = rd['players'].get(sid)
    if not player or player['kicked']:
        return
    if rd['state'] != 'playing':
        return
    active_count    = len([p for p in rd['players'].values() if not p['kicked']])
    reveals_allowed = get_reveals_for_round(active_count, rd['round'])
    revealed_round  = player.get('revealed_this_round', [])
    if key in player['revealed']:
        emit('join_error', {'msg': 'Вже відкрито'})
        return
    if len(revealed_round) >= reveals_allowed:
        emit('join_error', {'msg': f'Можна відкрити лише {reveals_allowed} характеристики'})
        return
    player['revealed'].append(key)
    player.setdefault('revealed_this_round', []).append(key)
    char = next((c for c in player['card_dict']['characteristics']
                 if c['key'] == key), None)
    socketio.emit('player_revealed', {
        'sid':   sid,
        'name':  player['name'],
        'key':   key,
        'value': char['value'] if char else '?',
        'label': char['label'] if char else '?',
        'icon':  char['icon']  if char else '',
    }, to=code)
    check_round_complete(code)


@socketio.on('vote')
def on_vote(data):
    code       = data.get('code', '').upper()
    target_sid = data.get('target')
    voter_sid  = request.sid
    if code not in rooms:
        return
    rd = rooms[code]
    if rd['state'] != 'voting':
        return
    if voter_sid not in rd['players'] or rd['players'][voter_sid]['kicked']:
        return
    rd['votes'][voter_sid] = target_sid
    active = [s for s, p in rd['players'].items()
              if not p['kicked'] and not p.get('disconnected')]
    socketio.emit('vote_update', {
        'votes_cast':   len(rd['votes']),
        'votes_needed': len(active),
    }, to=code)
    if len(rd['votes']) >= len(active):
        finish_voting(code)


@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    for code, rd in rooms.items():
        if sid not in rd['players']:
            continue
        name = rd['players'][sid]['name']
        if rd['state'] == 'lobby':
            rd['players'].pop(sid)
        else:
            rd['players'][sid]['disconnected'] = True
        socketio.emit('player_left', {'sid': sid, 'name': name}, to=code)
        break


@socketio.on('generate_story')
def on_generate_story(data):
    code = data.get('code', '').upper()
    if code not in rooms:
        return
    rd = rooms[code]
    def generate():
        prompt = build_story_prompt(rd)
        story  = call_gemini(prompt)
        socketio.emit('story_ready', {'story': story}, to=code)
    threading.Thread(target=generate, daemon=True).start()
