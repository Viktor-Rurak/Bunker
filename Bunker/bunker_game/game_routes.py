from flask import request, jsonify, session, redirect, url_for, render_template
from config import app, rooms
from database import set_user_game
from auth_routes import current_user, login_required
from helpers import generate_room_code


@app.route('/')
@login_required
def index():
    user = current_user()
    code = user.get('current_game_code')
    if code and code in rooms:
        return redirect(url_for('room', code=code))
    if code:
        set_user_game(user['id'], None)
        session.pop('current_game_code', None)
    return render_template('index.html', username=user['username'])


@app.route('/room/<code>')
@login_required
def room(code):
    code = code.upper()
    if code not in rooms:
        return redirect(url_for('index'))
    user = current_user()
    if user['current_game_code'] != code:
        set_user_game(user['id'], code)
        session['current_game_code'] = code
    return render_template('game.html', room_code=code,
                           username=user['username'])


@app.route('/api/create_room', methods=['POST'])
@login_required
def create_room():
    user = current_user()
    code = generate_room_code()
    while code in rooms:
        code = generate_room_code()
    rooms[code] = {
        "host":         None,
        "host_user_id": user['id'],
        "players":      {},
        "game":         None,
        "state":        "lobby",
        "round":        0,
        "votes":        {},
        "kicked_players": [],
    }
    set_user_game(user['id'], code)
    session['current_game_code'] = code
    return jsonify({"code": code})


@app.route('/api/leave_game', methods=['POST'])
@login_required
def api_leave_game():
    uid  = session['user_id']
    code = session.get('current_game_code')
    if code and code in rooms:
        rd = rooms[code]
        sid_to_remove = next(
            (s for s, p in rd['players'].items()
             if p.get('user_id') == uid), None
        )
        if sid_to_remove and rd['state'] == 'lobby':
            rd['players'].pop(sid_to_remove, None)
    set_user_game(uid, None)
    session.pop('current_game_code', None)
    return jsonify({'ok': True})
