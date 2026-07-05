"""Development entry point via socketio.run.

For production on Render or elsewhere:
    gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app
    # or: gunicorn -c gunicorn.conf.py wsgi:app
"""

import os

from app import create_app
from extensions import socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=app.debug)
