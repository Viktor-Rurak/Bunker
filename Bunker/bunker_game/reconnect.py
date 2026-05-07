from flask_socketio import join_room
from config import socketio, rooms
from helpers import get_reveals_for_round, get_all_players_state


def _reconnect_player(code, old_sid, new_sid, room_data):
    p = room_data['players'].pop(old_sid)
    room_data['players'][new_sid] = p

    if room_data['host'] == old_sid:
        room_data['host'] = new_sid
    if old_sid in room_data.get('votes', {}):
        room_data['votes'][new_sid] = room_data['votes'].pop(old_sid)

    join_room(code)

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
            'player_reconnected',
            {'sid': new_sid, 'name': p['name']},
            to=code
        )
        return

    game = room_data['game']
    active = [
        pl for pl in room_data['players'].values() if not pl['kicked']
    ]
    reveals_allowed = get_reveals_for_round(
        len(active), room_data['round']
    )
    reveals_done = len(p.get('revealed_this_round', []))

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
        'player_reconnected',
        {'sid': new_sid, 'name': p['name']},
        to=code
    )


if __name__ == '__main__':
    socketio.run(app, debug=True)
