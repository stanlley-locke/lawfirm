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
    from models import ChatSetting
    
    # Fetch settings from database with fallback to default configurations
    tz_setting = ChatSetting.query.filter_by(key='business_hours_tz').first()
    tz_val = tz_setting.value if tz_setting else app.config.get('BUSINESS_HOURS_TZ', 'Africa/Nairobi')
    
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_val)
    except Exception:
        tz = None

    now = datetime.now(tz) if tz else datetime.utcnow()
    
    days_setting = ChatSetting.query.filter_by(key='business_hours_days').first()
    if days_setting and days_setting.value:
        try:
            days_val = [int(d) for d in days_setting.value.split(',')]
        except Exception:
            days_val = [0, 1, 2, 3, 4]
    else:
        days_val = app.config.get('BUSINESS_HOURS_DAYS', [0, 1, 2, 3, 4])
        
    if now.weekday() not in days_val:
        return False
        
    start_setting = ChatSetting.query.filter_by(key='business_hours_start').first()
    start_val = int(start_setting.value) if (start_setting and start_setting.value) else app.config.get('BUSINESS_HOURS_START', 9)
    
    end_setting = ChatSetting.query.filter_by(key='business_hours_end').first()
    end_val = int(end_setting.value) if (end_setting and end_setting.value) else app.config.get('BUSINESS_HOURS_END', 17)
    
    return start_val <= now.hour < end_val
