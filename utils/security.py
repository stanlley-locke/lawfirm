import os
from functools import wraps

from flask import request, abort
from flask_login import current_user
from flask_socketio import disconnect


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin or not current_user.is_active:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def get_client_room_id():
    """Return the chat room ID stored in the visitor session."""
    from flask import session
    return session.get('chat_room')


def user_can_access_room(room_id):
    """Check whether the current user may access a chat room."""
    if not room_id:
        return False
    if current_user.is_authenticated and current_user.is_admin and current_user.is_active:
        return True
    return get_client_room_id() == room_id


def socketio_authenticated_admin():
    return current_user.is_authenticated and current_user.is_admin and current_user.is_active


def reject_socket(reason='Unauthorized'):
    disconnect()
    return False


def is_within_business_hours(app):
    """Return True if current time is within configured business hours."""
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(app.config.get('BUSINESS_HOURS_TZ', 'Africa/Nairobi'))
    except Exception:
        tz = None

    now = datetime.now(tz) if tz else datetime.utcnow()
    if now.weekday() not in app.config.get('BUSINESS_HOURS_DAYS', [0, 1, 2, 3, 4]):
        return False
    start = app.config.get('BUSINESS_HOURS_START', 9)
    end = app.config.get('BUSINESS_HOURS_END', 17)
    return start <= now.hour < end
