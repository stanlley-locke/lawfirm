from flask import Blueprint, render_template, request, jsonify, session
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from models import User, ChatMessage, ChatRoom
import uuid
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    join_room(room)
    emit('status', {'msg': 'Joined room: ' + room}, room=room)
    
    # Update room activity timestamp
    chat_room = ChatRoom.query.filter_by(room_id=room).first()
    if chat_room:
        chat_room.last_activity = datetime.utcnow()
        db.session.commit()

@socketio.on('leave')
def handle_leave(data):
    room = data.get('room')
    leave_room(room)
    emit('status', {'msg': 'Left room: ' + room}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data.get('room')
    message = data.get('message')
    is_from_client = data.get('is_from_client', False)
    client_name = data.get('client_name')
    client_email = data.get('client_email')
    
    # Store message in database
    chat_message = ChatMessage(
        content=message,
        room=room,
        is_from_client=is_from_client,
        client_name=client_name,
        client_email=client_email
    )
    
    # If the message is from a logged-in user (admin/staff), link it
    if current_user.is_authenticated and not is_from_client:
        chat_message.user_id = current_user.id
    
    db.session.add(chat_message)
    
    # Update room's last activity
    chat_room = ChatRoom.query.filter_by(room_id=room).first()
    if chat_room:
        chat_room.last_activity = datetime.utcnow()
    
    db.session.commit()
    
    # Broadcast message to the room
    emit('message', {
        'id': chat_message.id,
        'content': message,
        'is_from_client': is_from_client,
        'client_name': client_name if is_from_client else None,
        'user': current_user.username if current_user.is_authenticated and not is_from_client else None,
        'timestamp': chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

# Routes
@chat_bp.route('/chat')
def client_chat():
    """Public chat interface for website visitors"""
    # Generate a unique room ID if not already set
    if 'chat_room' not in session:
        session['chat_room'] = str(uuid.uuid4())
    
    room_id = session['chat_room']
    
    # Check if room exists, if not create it
    chat_room = ChatRoom.query.filter_by(room_id=room_id).first()
    if not chat_room:
        chat_room = ChatRoom(room_id=room_id)
        db.session.add(chat_room)
        db.session.commit()
    
    # Get recent messages
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp).all()
    
    return render_template('chat/client_chat.html', 
                          title='Live Chat',
                          room=room_id,
                          messages=messages)

@chat_bp.route('/chat/start', methods=['POST'])
def start_chat():
    """Endpoint for clients to start a new chat with their information"""
    data = request.json
    name = data.get('name')
    email = data.get('email')
    
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    
    # If room already exists in session, update it with client info
    room_id = session.get('chat_room')
    if room_id:
        chat_room = ChatRoom.query.filter_by(room_id=room_id).first()
        if chat_room:
            chat_room.client_name = name
            chat_room.client_email = email
            chat_room.last_activity = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'room': room_id
            })
    
    # Otherwise create a new room
    room_id = str(uuid.uuid4())
    session['chat_room'] = room_id
    
    chat_room = ChatRoom(
        room_id=room_id,
        client_name=name,
        client_email=email
    )
    db.session.add(chat_room)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'room': room_id
    })

@chat_bp.route('/admin/chats')
@login_required
def admin_chats():
    """Admin interface for viewing and managing all chats"""
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    
    # Get all chat rooms ordered by activity
    chat_rooms = ChatRoom.query.filter_by(is_active=True).order_by(ChatRoom.last_activity.desc()).all()
    
    return render_template('admin/chats.html', 
                          title='Manage Chats',
                          chat_rooms=chat_rooms)

@chat_bp.route('/admin/chat/<room_id>')
@login_required
def admin_chat_room(room_id):
    """Admin interface for a specific chat room"""
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    
    # Get the room
    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    
    # Mark all unread messages as read
    unread_messages = ChatMessage.query.filter_by(room=room_id, is_read=False).all()
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    
    # Get all messages for this room
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp).all()
    
    return render_template('admin/chat_room.html',
                          title=f'Chat with {chat_room.client_name}',
                          room=chat_room,
                          messages=messages)

@chat_bp.route('/admin/chat/<room_id>/close', methods=['POST'])
@login_required
def close_chat_room(room_id):
    """Endpoint to close/deactivate a chat room"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    chat_room = ChatRoom.query.filter_by(room_id=room_id).first_or_404()
    chat_room.is_active = False
    db.session.commit()
    
    return jsonify({'success': True})

@chat_bp.route('/admin/chat/unread-count')
@login_required
def unread_message_count():
    """API endpoint for getting the count of unread messages"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    count = ChatMessage.query.filter_by(is_read=False, is_from_client=True).count()
    return jsonify({'count': count})