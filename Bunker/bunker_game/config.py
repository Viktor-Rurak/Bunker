import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key-change-me')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

_origins_env = os.environ.get('ALLOWED_ORIGINS', '*')
_origins = [o.strip() for o in _origins_env.split(',')] if _origins_env != '*' else '*'
socketio = SocketIO(app, cors_allowed_origins=_origins, async_mode='gevent')

# Глобальний стан: всі активні кімнати
rooms = {}

REVEAL_TABLE = {
    6:  [3, 3, 2],
    7:  [3, 2, 2, 1],
    8:  [3, 2, 2, 1],
    9:  [3, 2, 1, 1],
    10: [3, 2, 1, 1],
    11: [2, 2, 1, 1],
    12: [2, 2, 1, 1],
    13: [2, 1, 1, 1],
    14: [2, 1, 1, 1],
    15: [2, 1, 1, 1],
}
