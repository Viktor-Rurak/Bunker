import sqlite3
import hashlib
import uuid
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bunker.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            current_game_code TEXT DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def register_user(username: str, password: str):
    """Створює нового користувача. Повертає user dict або None якщо нік зайнятий."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        user_id = str(uuid.uuid4())
        c.execute(
            'INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)',
            (user_id, username, _hash(password))
        )
        conn.commit()
        return {'id': user_id, 'username': username, 'current_game_code': None}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def login_user(username: str, password: str):
    """Перевіряє пароль. Повертає user dict або None."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'SELECT id, username, password_hash, current_game_code '
        'FROM users WHERE username = ?',
        (username,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    if row[2] != _hash(password):
        return None
    return {
        'id': row[0],
        'username': row[1],
        'current_game_code': row[3]
    }


def get_user(user_id: str):
    """Повертає user dict по id або None."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'SELECT id, username, current_game_code FROM users WHERE id = ?',
        (user_id,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {'id': row[0], 'username': row[1], 'current_game_code': row[2]}


def set_user_game(user_id: str, game_code):
    """Прив'язує або відв'язує акаунт від гри (game_code=None для виходу)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'UPDATE users SET current_game_code = ? WHERE id = ?',
        (game_code, user_id)
    )
    conn.commit()
    conn.close()
