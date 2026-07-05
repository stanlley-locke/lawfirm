import io
import os
import uuid
from datetime import datetime

from flask import (
    Blueprint, render_template, request, jsonify, session, current_app,
    send_file, abort,
)
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from extensions import db, socketio
from models import User, ChatMessage, ChatRoom, CannedResponse, ChatSetting
from utils.email_utils import send_email, escape_html
from utils.security import (
    user_can_access_room, socketio_authenticated_admin, reject_socket,
    is_within_business_hours,
)
from utils.uploads import save_upload

chat_bp = Blueprint('chat', __name__)


def _serialize_message(msg):
    data = {
        'id': msg.id,
        'content': msg.content,
        'is_from_client': msg.is_from_client,
        'client_name': msg.client_name if msg.is_from_client else None,
        'user': msg.user.username if msg.user else None,
        'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': msg.is_read,
    }
    if msg.attachment_filename:
        data['attachment_url'] = f"/static/uploads/chat/{msg.attachment_filename}"
        data['attachment_name'] = msg.attachment_original_name
    return data


def _notify_admin_new_message(chat_room, message):
    admin_email = current_app.config.get('ADMIN_NOTIFICATION_EMAIL')
    if not admin_email:
        return
    send_email(
        subject=f"New chat message from {chat_room.client_name or 'Visitor'}",
        recipients=[admin_email],
        text_body=(
            f"New chat message in room {chat_room.room_id}:\n\n"
            f"From: {chat_room.client_name} ({chat_room.client_email})\n"
            f"Message: {message.content}\n"
        ),
        html_body=(
            f"<p><strong>Room:</strong> {escape_html(chat_room.room_id)}</p>"
            f"<p><strong>From:</strong> {escape_html(chat_room.client_name)} "
            f"({escape_html(chat_room.client_email)})</p>"
            f"<p><strong>Message:</strong> {escape_html(message.content)}</p>"
        ),
    )


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated and current_user.is_admin:
        current_user.is_online = True
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        return True
    if session.get('chat_room'):
        return True
    return reject_socket('Authentication required')


@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated and current_user.is_admin:
        current_user.is_online = False
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    if not user_can_access_room(room):
        return reject_socket('Invalid room')

    join_room(room)
    chat_room = ChatRoom.query.filter_by(room_id=room).first()
    if chat_room:
        chat_room.last_activity = datetime.utcnow()
        db.session.commit()

    if socketio_authenticated_admin():
        emit('status', {'msg': 'Staff joined', 'joined': True, 'user': 'staff'}, room=room)
    else:
        emit('status', {'msg': 'Client joined', 'joined': True, 'user': 'client'}, room=room)


@socketio.on('leave')
def handle_leave(data):
    room = data.get('room')
    if not user_can_access_room(room):
        return reject_socket('Invalid room')
    leave_room(room)
    emit('status', {'msg': 'Left room', 'left': True}, room=room)


@socketio.on('typing')
def handle_typing(data):
    room = data.get('room')
    if not user_can_access_room(room):
        return
    emit('typing', {
        'room': room,
        'is_typing': data.get('is_typing', False),
        'user': current_user.username if socketio_authenticated_admin() else data.get('client_name', 'Client'),
        'is_staff': socketio_authenticated_admin(),
    }, room=room, include_self=False)


@socketio.on('read_receipt')
def handle_read_receipt(data):
    room = data.get('room')
    message_ids = data.get('message_ids', [])
    if not user_can_access_room(room):
        return

    for msg_id in message_ids:
        msg = ChatMessage.query.filter_by(id=msg_id, room=room).first()
        if msg:
            msg.is_read = True
    db.session.commit()
    emit('read_receipt', {'message_ids': message_ids, 'room': room}, room=room)


@socketio.on('message')
def handle_message(data):
    room = data.get('room')
    message_text = (data.get('message') or '').strip()
    if not room or not message_text:
        return
    if not user_can_access_room(room):
        return reject_socket('Invalid room')

    is_from_client = data.get('is_from_client', False)
    if socketio_authenticated_admin():
        is_from_client = False
    elif not is_from_client and not session.get('chat_room') == room:
        return reject_socket('Invalid sender')

    chat_message = ChatMessage(
        content=message_text,
        room=room,
        is_from_client=is_from_client,
        client_name=data.get('client_name'),
        client_email=data.get('client_email'),
    )
    if socketio_authenticated_admin():
        chat_message.user_id = current_user.id

    db.session.add(chat_message)
    chat_room = ChatRoom.query.filter_by(room_id=room).first()
    if chat_room:
        chat_room.last_activity = datetime.utcnow()
    db.session.commit()

    if is_from_client and chat_room:
        _notify_admin_new_message(chat_room, chat_message)

    emit('message', _serialize_message(chat_message), room=room)

    if is_from_client and not is_within_business_hours(current_app):
        auto_reply = (
            'Thank you for contacting us. Our office is currently closed. '
            'We will respond during business hours (Mon–Fri 8:00 am–5:30 pm, Sat 9:30 am–1:00 pm EAT).'
        )
        auto_msg = ChatMessage(
            content=auto_reply,
            room=room,
            is_from_client=False,
        )
        db.session.add(auto_msg)
        db.session.commit()
        emit('message', _serialize_message(auto_msg), room=room)


@chat_bp.route('/chat')
def client_chat():
    if 'chat_room' not in session:
        session['chat_room'] = str(uuid.uuid4())

    room_id = session['chat_room']
    chat_room = ChatRoom.query.filter_by(room_id=room_id).first()
    if not chat_room:
        chat_room = ChatRoom(room_id=room_id)
        db.session.add(chat_room)
        db.session.commit()

    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp).all()
    return render_template(
        'chat/client_chat.html',
        title='Live Chat',
        room=room_id,
        messages=messages,
    )


@chat_bp.route('/chat/start', methods=['POST'])
def start_chat():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400

    room_id = session.get('chat_room')
    if room_id:
        chat_room = ChatRoom.query.filter_by(room_id=room_id).first()
        if chat_room:
            chat_room.client_name = name
            chat_room.client_email = email
            chat_room.last_activity = datetime.utcnow()
            db.session.commit()
            
            # Send notification if no messages exist in the room yet
            message_count = ChatMessage.query.filter_by(room=chat_room.room_id).count()
            if message_count == 0:
                handle_chat_start_notifications(chat_room)
                
            return jsonify({'success': True, 'room_id': room_id})

    room_id = str(uuid.uuid4())
    session['chat_room'] = room_id
    chat_room = ChatRoom(room_id=room_id, client_name=name, client_email=email)
    db.session.add(chat_room)
    db.session.commit()
    
    handle_chat_start_notifications(chat_room)
    
    return jsonify({'success': True, 'room_id': room_id})


@chat_bp.route('/chat/upload', methods=['POST'])
def upload_chat_file():
    room_id = session.get('chat_room')
    if not room_id:
        return jsonify({'error': 'No active chat session'}), 400

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'chat')
    try:
        stored, original = save_upload(
            file, upload_dir, current_app.config.get('CHAT_UPLOAD_EXTENSIONS', set())
        )
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first()
    client_name = chat_room.client_name if chat_room else None

    chat_message = ChatMessage(
        content=f'[Attachment: {original}]',
        room=room_id,
        is_from_client=True,
        client_name=client_name,
        attachment_filename=stored,
        attachment_original_name=original,
    )
    db.session.add(chat_message)
    if chat_room:
        chat_room.last_activity = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'message': _serialize_message(chat_message)})


@chat_bp.route('/admin/chats')
@login_required
def admin_chats():
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403

    assignee_filter = request.args.get('assignee', type=int)
    query = ChatRoom.query.filter_by(is_active=True)
    if assignee_filter:
        query = query.filter_by(assigned_to_id=assignee_filter)
    active_rooms = query.order_by(ChatRoom.last_activity.desc()).all()
    archived_rooms = ChatRoom.query.filter_by(is_active=False).order_by(
        ChatRoom.last_activity.desc()
    ).all()

    for room in active_rooms:
        room.has_unread = ChatMessage.query.filter_by(
            room=room.room_id, is_read=False, is_from_client=True
        ).count() > 0
        room.unread_count = ChatMessage.query.filter_by(
            room=room.room_id, is_read=False, is_from_client=True
        ).count()
        last_msg = ChatMessage.query.filter_by(room=room.room_id).order_by(ChatMessage.timestamp.desc()).first()
        room.last_message_content = last_msg.content if last_msg else 'Started chat session.'
        room.last_message_time = last_msg.timestamp.strftime('%H:%M') if last_msg else room.last_activity.strftime('%H:%M')

    for room in archived_rooms:
        last_msg = ChatMessage.query.filter_by(room=room.room_id).order_by(ChatMessage.timestamp.desc()).first()
        room.last_message_content = last_msg.content if last_msg else 'Archived chat session.'
        room.last_message_time = last_msg.timestamp.strftime('%Y-%m-%d') if last_msg else room.last_activity.strftime('%Y-%m-%d')

    staff = User.query.filter_by(is_admin=True, is_active=True).all()
    canned_responses = CannedResponse.query.order_by(CannedResponse.shortcut).all()
    
    db_settings = ChatSetting.query.all()
    settings = {s.key: s.value for s in db_settings}
    settings.setdefault('business_hours_start', '9')
    settings.setdefault('business_hours_end', '17')
    settings.setdefault('business_hours_days', '0,1,2,3,4')
    settings.setdefault('business_hours_tz', 'Africa/Nairobi')
    settings.setdefault('closed_message', 'Thank you for contacting us. Our office is currently closed.')

    return render_template(
        'admin/chats.html',
        title='Manage Chats',
        active_rooms=active_rooms,
        archived_rooms=archived_rooms,
        total_chats=ChatRoom.query.count(),
        staff=staff,
        assignee_filter=assignee_filter,
        canned_responses=canned_responses,
        settings=settings
    )


@chat_bp.route('/admin/chat/<room_id>')
@login_required
def admin_chat_room(room_id):
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    unread_messages = ChatMessage.query.filter_by(room=room_id, is_read=False).all()
    for message in unread_messages:
        message.is_read = True
    db.session.commit()

    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp).all()
    staff = User.query.filter_by(is_admin=True, is_active=True).all()
    return render_template(
        'admin/chat_room.html',
        title=f'Chat with {chat_room.client_name}',
        room=chat_room,
        messages=messages,
        staff=staff,
    )


@chat_bp.route('/admin/chat/<room_id>/assign', methods=['POST'])
@login_required
def assign_chat_room(room_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    assignee_id = request.json.get('assigned_to_id') if request.is_json else request.form.get('assigned_to_id')
    if assignee_id:
        assignee = User.query.filter_by(id=int(assignee_id), is_admin=True, is_active=True).first()
        if not assignee:
            return jsonify({'error': 'Invalid assignee'}), 400
        chat_room.assigned_to_id = assignee.id
    else:
        chat_room.assigned_to_id = None
    db.session.commit()
    return jsonify({'success': True})


@chat_bp.route('/admin/chat/<room_id>/close', methods=['POST'])
@login_required
def close_chat_room(room_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    chat_room.is_active = False
    db.session.commit()
    return jsonify({'success': True})


@chat_bp.route('/admin/chat/<room_id>/reopen', methods=['POST'])
@login_required
def reopen_chat_room(room_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    chat_room.is_active = True
    chat_room.last_activity = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})


@chat_bp.route('/admin/chat/<room_id>/delete', methods=['POST'])
@login_required
def delete_chat_room(room_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    # Delete all messages first to prevent foreign key constraint failures
    ChatMessage.query.filter_by(room=room_id).delete()
    db.session.delete(chat_room)
    db.session.commit()
    return jsonify({'success': True})


@chat_bp.route('/admin/chat/<room_id>/export/pdf')
@login_required
def export_chat_pdf(room_id):
    if not current_user.is_admin:
        abort(403)

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp).all()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(50, y, f'Chat Transcript - {chat_room.client_name or room_id}')
    y -= 30
    pdf.setFont('Helvetica', 10)
    for msg in messages:
        sender = msg.client_name if msg.is_from_client else (msg.user.username if msg.user else 'Staff')
        line = f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] {sender}: {msg.content}"
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont('Helvetica', 10)
        pdf.drawString(50, y, line[:110])
        y -= 15
    pdf.save()
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'chat-{room_id}.pdf',
    )


@chat_bp.route('/admin/chat/<room_id>/export/email', methods=['POST'])
@login_required
def export_chat_email(room_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp).all()
    recipient = current_app.config.get('ADMIN_NOTIFICATION_EMAIL')
    if not recipient:
        return jsonify({'error': 'Admin email not configured'}), 400

    lines = []
    for msg in messages:
        sender = msg.client_name if msg.is_from_client else (msg.user.username if msg.user else 'Staff')
        lines.append(f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] {sender}: {msg.content}")

    send_email(
        subject=f'Chat transcript: {chat_room.client_name or room_id}',
        recipients=[recipient],
        text_body='\n'.join(lines),
    )
    return jsonify({'success': True})


@chat_bp.route('/admin/chat/unread-count')
@login_required
def unread_message_count():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    count = ChatMessage.query.filter_by(is_read=False, is_from_client=True).count()
    return jsonify({'count': count})


@chat_bp.route('/admin/chat/active-count')
@login_required
def active_chat_count():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    count = ChatRoom.query.filter_by(is_active=True).count()
    return jsonify({'count': count})


@chat_bp.route('/admin/chat/<room_id>/messages', methods=['GET'])
@login_required
def admin_chat_room_messages(room_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    
    # Mark messages as read
    unread_messages = ChatMessage.query.filter_by(room=room_id, is_read=False).all()
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp).all()
    serialized = [_serialize_message(msg) for msg in messages]
    
    return jsonify({
        'success': True,
        'messages': serialized,
        'client_name': chat_room.client_name or 'Anonymous',
        'client_email': chat_room.client_email or '',
        'assigned_to_id': chat_room.assigned_to_id,
        'is_active': chat_room.is_active
    })


@chat_bp.route('/admin/chat/settings', methods=['POST'])
@login_required
def admin_chat_save_settings():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    settings_data = request.json or {}
    for key, val in settings_data.items():
        setting = ChatSetting.query.filter_by(key=key).first()
        if not setting:
            setting = ChatSetting(key=key)
            db.session.add(setting)
        setting.value = str(val) if val is not None else ''
        
    db.session.commit()
    return jsonify({'success': True})


@chat_bp.route('/admin/chat/canned', methods=['POST'])
@login_required
def admin_chat_save_canned():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    shortcut = request.form.get('shortcut')
    content = request.form.get('content')
    canned_id = request.form.get('id', type=int)

    if not shortcut or not content:
        return jsonify({'error': 'Shortcut and content are required'}), 400

    if canned_id:
        canned = CannedResponse.query.get_or_404(canned_id)
        canned.shortcut = shortcut
        canned.content = content
    else:
        canned = CannedResponse(shortcut=shortcut, content=content)
        db.session.add(canned)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Shortcut already exists'}), 400

    return jsonify({'success': True})


@chat_bp.route('/admin/chat/canned/<int:id>/delete', methods=['POST'])
@login_required
def admin_chat_delete_canned(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    canned = CannedResponse.query.get_or_404(id)
    db.session.delete(canned)
    db.session.commit()
    return jsonify({'success': True})


def get_next_business_hours(app):
    from datetime import datetime, timedelta
    from models import ChatSetting
    
    tz_setting = ChatSetting.query.filter_by(key='business_hours_tz').first()
    tz_val = tz_setting.value if tz_setting else app.config.get('BUSINESS_HOURS_TZ', 'Africa/Nairobi')
    
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_val)
    except Exception:
        tz = None

    now = datetime.now(tz) if tz else datetime.utcnow()
    
    start_setting = ChatSetting.query.filter_by(key='business_hours_start').first()
    start_val = int(start_setting.value) if (start_setting and start_setting.value) else app.config.get('BUSINESS_HOURS_START', 9)
    
    days_setting = ChatSetting.query.filter_by(key='business_hours_days').first()
    if days_setting and days_setting.value:
        try:
            days_val = [int(d) for d in days_setting.value.split(',')]
        except Exception:
            days_val = [0, 1, 2, 3, 4]
    else:
        days_val = app.config.get('BUSINESS_HOURS_DAYS', [0, 1, 2, 3, 4])
        
    weekday_names = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }
    
    for i in range(8):
        candidate = now + timedelta(days=i)
        wday = candidate.weekday()
        if wday in days_val:
            if i == 0:
                if now.hour < start_val:
                    return f"today ({weekday_names[wday]}) at {start_val:02d}:00"
            else:
                day_desc = "tomorrow" if i == 1 else f"on {weekday_names[wday]}"
                return f"{day_desc} at {start_val:02d}:00"
                
    return f"on Monday at {start_val:02d}:00"


def handle_chat_start_notifications(chat_room):
    from flask import current_app, url_for
    from utils.security import is_within_business_hours
    from models import User, ChatMessage
    from extensions import db
    from utils.email_utils import send_email

    admin_email = current_app.config.get('ADMIN_NOTIFICATION_EMAIL')
    if not admin_email:
        admin = User.query.filter_by(is_admin=True).first()
        admin_email = admin.email if admin else 'admin@doa.com'

    within_hours = is_within_business_hours(current_app)
    next_hours = get_next_business_hours(current_app)

    online_admins = User.query.filter_by(is_admin=True, is_online=True).count()
    has_online_admin = online_admins > 0

    admin_chats_link = url_for('chat.admin_chats', _external=True)

    if not within_hours:
        reply_content = (
            f"Thank you for contacting us. Our office is currently closed. "
            f"We will be back online {next_hours} (EAT timezone). "
            f"We have forwarded your contact details to our legal team and will get back to you as soon as we resume."
        )
        auto_msg = ChatMessage(
            content=reply_content,
            room=chat_room.room_id,
            is_from_client=False
        )
        db.session.add(auto_msg)
        db.session.commit()

        email_body = (
            f"A visitor has requested a live chat outside business hours.\n\n"
            f"Visitor Name: {chat_room.client_name or 'Anonymous'}\n"
            f"Visitor Email: {chat_room.client_email or 'Not provided'}\n"
            f"Requested Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Next Business Hours Resume: {next_hours}\n\n"
            f"View chat logs here:\n{admin_chats_link}"
        )
        try:
            send_email(
                subject=f"Off-Hours Chat Request from {chat_room.client_name or 'Visitor'}",
                recipients=[admin_email],
                text_body=email_body
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send off-hours email to admin: {e}")

    elif not has_online_admin:
        reply_content = (
            "Our office is currently open, but all our advocates are currently away from their desks. "
            "We have forwarded your request to our support desk. We will respond directly to your email shortly."
        )
        auto_msg = ChatMessage(
            content=reply_content,
            room=chat_room.room_id,
            is_from_client=False
        )
        db.session.add(auto_msg)
        db.session.commit()

        email_body = (
            f"ALERT: A visitor has requested a live chat during business hours, but NO staff members are currently logged into the dashboard.\n\n"
            f"Visitor Name: {chat_room.client_name or 'Anonymous'}\n"
            f"Visitor Email: {chat_room.client_email or 'Not provided'}\n"
            f"Requested Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"Please log in to respond:\n{admin_chats_link}"
        )
        try:
            send_email(
                subject=f"UNANSWERED CHAT: Live Chat Request from {chat_room.client_name or 'Visitor'}",
                recipients=[admin_email],
                text_body=email_body
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send missed chat email to admin: {e}")


