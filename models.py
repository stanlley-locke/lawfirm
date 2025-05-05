from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50))  # Font awesome icon name
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Service {self.title}>'

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    position = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    photo_url = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TeamMember {self.name}>'

class CaseStudy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    client = db.Column(db.String(100))
    summary = db.Column(db.Text, nullable=False)
    challenge = db.Column(db.Text)
    solution = db.Column(db.Text)
    outcome = db.Column(db.Text)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    service = db.relationship('Service', backref=db.backref('case_studies', lazy=True))
    featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CaseStudy {self.title}>'

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    service = db.relationship('Service', backref=db.backref('contact_messages', lazy=True))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContactMessage {self.name} - {self.subject}>'


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_from_client = db.Column(db.Boolean, default=False)
    client_name = db.Column(db.String(100), nullable=True)
    client_email = db.Column(db.String(120), nullable=True)
    room = db.Column(db.String(100), nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ChatMessage {self.id}>'


class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(100), unique=True, nullable=False)
    client_name = db.Column(db.String(100), nullable=True)
    client_email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<ChatRoom {self.room_id}>'
