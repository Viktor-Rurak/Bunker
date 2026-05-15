import psycopg2
import psycopg2.errors
import bcrypt
import uuid
import os


def _get_conn():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        raise RuntimeError('DATABASE_URL environment variable is not set')
    return psycopg2.connect(url)


def init_db():
    conn = _get_conn()
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
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def register_user(username: str, password: str):
    conn = _get_conn()
    c = conn.cursor()
    try:
        user_id = str(uuid.uuid4())
        c.execute(
            'INSERT INTO users (id, username, password_hash) VALUES (%s, %s, %s)',
            (user_id, username, _hash(password))
        )
        conn.commit()
        return {'id': user_id, 'username': username, 'current_game_code': None}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return None
    finally:
        conn.close()


def login_user(username: str, password: str):
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, username, password_hash, current_game_code '
        'FROM users WHERE username = %s',
        (username,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    if not _verify(password, row[2]):
        return None
    return {
        'id': row[0],
        'username': row[1],
        'current_game_code': row[3]
    }


def get_user(user_id: str):
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, username, current_game_code FROM users WHERE id = %s',
        (user_id,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {'id': row[0], 'username': row[1], 'current_game_code': row[2]}


def set_user_game(user_id: str, game_code):
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        'UPDATE users SET current_game_code = %s WHERE id = %s',
        (game_code, user_id)
    )
    conn.commit()
    conn.close()
