"""Production WSGI entry point for gunicorn + eventlet.

Monkey-patch MUST run before any Flask/SQLAlchemy imports.
"""

from app import create_app  # noqa: E402

app = create_app('production')
