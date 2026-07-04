"""Use socketio.run via app.py for development.

For production:
    gunicorn -c gunicorn.conf.py "app:app"
"""

from app import app, socketio

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=app.debug)
