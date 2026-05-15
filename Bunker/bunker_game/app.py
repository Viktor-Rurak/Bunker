import sys, os

_base = os.path.dirname(__file__)
sys.path.insert(0, _base)
sys.path.insert(0, os.path.join(_base, 'game'))
sys.path.insert(0, os.path.join(_base, 'routes'))
sys.path.insert(0, os.path.join(_base, 'sockets'))

from dotenv import load_dotenv
load_dotenv()

from database import init_db
init_db()

import auth_routes      # noqa: F401
import game_routes      # noqa: F401
import dev_routes       # noqa: F401
import socket_events    # noqa: F401
import action_handlers  # noqa: F401

from config import app, socketio

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port  = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
