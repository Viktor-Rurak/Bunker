"""
dev_routes.py — одноразові токени для автоматичного логіну під час тестування.

Захищено DEV_SECRET — без нього всі ендпоінти повертають 403.
Щоб увімкнути: додай DEV_SECRET=будь-який-рядок в Railway Variables.
"""
import os
import secrets
import time

from flask import request, jsonify, session, redirect
from config import app
from database import login_user

_tokens: dict = {}   # token -> {'user': {...}, 'exp': float}


def _authorized():
    dev_secret = os.environ.get('DEV_SECRET', '')
    return dev_secret and request.headers.get('X-Dev-Secret') == dev_secret


@app.route('/api/dev/token', methods=['POST'])
def api_dev_token():
    """Видає одноразовий токен для автологіну."""
    if not _authorized():
        return jsonify({'error': 'forbidden'}), 403
    data = request.json or {}
    user = login_user(data.get('username', ''), data.get('password', ''))
    if not user:
        return jsonify({'error': 'login failed'}), 401
    tok = secrets.token_urlsafe(32)
    _tokens[tok] = {'user': user, 'exp': time.time() + 120}   # живе 2 хв
    return jsonify({'token': tok})


@app.route('/dev/login/<token>')
def dev_login(token):
    """Логінить юзера за одноразовим токеном і редиректить на /."""
    entry = _tokens.pop(token, None)
    if not entry or time.time() > entry['exp']:
        return 'Token expired or invalid', 400
    u = entry['user']
    session['user_id'] = u['id']
    session['username'] = u['username']
    return redirect('/')
