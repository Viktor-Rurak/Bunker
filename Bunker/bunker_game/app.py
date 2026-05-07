import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db
init_db()

# Реєструємо маршрути та обробники (імпорт = реєстрація через декоратори)
import auth_routes      # noqa: F401
import game_routes      # noqa: F401
import socket_events    # noqa: F401
import action_handlers  # noqa: F401

from config import app, socketio

if __name__ == '__main__':
    socketio.run(app, debug=True)
