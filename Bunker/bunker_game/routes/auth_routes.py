from flask import request, jsonify, session, redirect, url_for
from config import app
from database import register_user, login_user, get_user, set_user_game


def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return get_user(uid)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth_page'))
        return f(*args, **kwargs)
    return decorated


@app.route('/auth')
def auth_page():
    if session.get('user_id'):
        return redirect(url_for('index'))
    from flask import render_template
    return render_template('auth.html')


@app.route('/api/register', methods=['POST'])
def api_register():
    import traceback
    data = request.json or {}
    username = data.get('username', '').strip()[:32]
    password = data.get('password', '').strip()[:64]
    if not username or not password:
        return jsonify({'error': "Введіть нікнейм і пароль"}), 400
    if len(username) < 2:
        return jsonify({'error': "Нікнейм мінімум 2 символи"}), 400
    if len(password) < 4:
        return jsonify({'error': "Пароль мінімум 4 символи"}), 400
    try:
        user = register_user(username, password)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f"DB error: {e}"}), 500
    if not user:
        return jsonify({'error': "Цей нікнейм вже зайнятий"}), 409
    session['user_id']  = user['id']
    session['username'] = user['username']
    return jsonify({'ok': True})


@app.route('/api/login', methods=['POST'])
def api_login():
    import traceback
    data = request.json or {}
    username = data.get('username', '').strip()[:32]
    password = data.get('password', '').strip()[:64]
    if not username or not password:
        return jsonify({'error': "Введіть нікнейм і пароль"}), 400
    try:
        user = login_user(username, password)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f"DB error: {e}"}), 500
    if not user:
        return jsonify({'error': "Невірний нікнейм або пароль"}), 401
    session['user_id']  = user['id']
    session['username'] = user['username']
    return jsonify({'ok': True, 'current_game': user['current_game_code']})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    uid = session.get('user_id')
    if uid:
        set_user_game(uid, None)
    session.clear()
    return jsonify({'ok': True})
