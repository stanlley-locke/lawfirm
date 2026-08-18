from datetime import datetime, timedelta
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# --- OTP (two-factor login) settings ---
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Two-factor (OTP) login fields
    otp_code_hash = db.Column(db.String(255), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    otp_attempts = db.Column(db.Integer, default=0)
    otp_last_sent_at = db.Column(db.DateTime, nullable=True)

    assigned_rooms = db.relationship('ChatRoom', backref='assignee', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_otp(self, code):
        """Hash and store a freshly generated OTP code with a fresh expiry."""
        self.otp_code_hash = generate_password_hash(code)
        self.otp_expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        self.otp_last_sent_at = datetime.utcnow()
        self.otp_attempts = 0

    def check_otp(self, code):
        """Validate a submitted OTP code against the stored hash and expiry."""
        if not self.otp_code_hash or not self.otp_expires_at:
            return False
        if datetime.utcnow() > self.otp_expires_at:
            return False
        return check_password_hash(self.otp_code_hash, code)

    def clear_otp(self):
        self.otp_code_hash = None
        self.otp_expires_at = None
        self.otp_attempts = 0
        self.otp_last_sent_at = None

    def otp_is_expired(self):
        return not self.otp_expires_at or datetime.utcnow() > self.otp_expires_at

    def otp_resend_allowed(self):
        if not self.otp_last_sent_at:
            return True
        return (datetime.utcnow() - self.otp_last_sent_at).total_seconds() >= OTP_RESEND_COOLDOWN_SECONDS

    def otp_seconds_until_resend(self):
        if not self.otp_last_sent_at:
            return 0
        remaining = OTP_RESEND_COOLDOWN_SECONDS - (datetime.utcnow() - self.otp_last_sent_at).total_seconds()
        return max(0, int(remaining))

    def __repr__(self):
        return f'<User {self.username}>'


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50))
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
    practice_number = db.Column(db.String(50))
    photo_url = db.Column(db.Text)
    photo_filename = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def photo_src(self):
        if self.photo_filename:
            return f'/static/uploads/team/{self.photo_filename}'
        return self.photo_url

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


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    author = db.relationship('User', backref=db.backref('blog_posts', lazy=True))
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BlogPost {self.title}>'


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
    attachment_filename = db.Column(db.String(255))
    attachment_original_name = db.Column(db.String(255))
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
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ChatRoom {self.room_id}>'


class LegalCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Active')  # e.g., Active, Pending, Closed
    case_type = db.Column(db.String(100))  # e.g., Conveyancing, Commercial, Litigation
    reference_code = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = db.relationship('User', backref=db.backref('cases', lazy=True))

    def __repr__(self):
        return f'<LegalCase {self.case_number} - {self.title}>'


class CaseMilestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('legal_case.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='Upcoming')  # e.g., Upcoming, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    case = db.relationship('LegalCase', backref=db.backref('milestones', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<CaseMilestone {self.title} for {self.case_id}>'


class CaseDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('legal_case.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    case = db.relationship('LegalCase', backref=db.backref('documents', lazy=True, cascade="all, delete-orphan"))
    uploaded_by = db.relationship('User', backref=db.backref('uploaded_documents', lazy=True))

    def __repr__(self):
        return f'<CaseDocument {self.original_name}>'


class CaseInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('legal_case.id'), nullable=False)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='Unpaid')  # e.g., Unpaid, Paid, Overdue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    case = db.relationship('LegalCase', backref=db.backref('invoices', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<CaseInvoice {self.invoice_number} - {self.amount}>'


class CannedResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shortcut = db.Column(db.String(50), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CannedResponse {self.shortcut}>'


class ChatSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ChatSetting {self.key}>'

