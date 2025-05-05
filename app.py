import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
socketio = SocketIO()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # Needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///lawfirm.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 30,
    "max_overflow": 15,
    "pool_size": 30,
    "connect_args": {
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure email settings
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").lower() in ["true", "1", "t"]
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@lawfirm.com")

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate.init_app(app, db)
mail.init_app(app)
csrf.init_app(app)
socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent', ping_timeout=60)

with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, Service, TeamMember, CaseStudy, ContactMessage, ChatMessage, ChatRoom

    # Import and register blueprints
    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.main_routes import main_bp
    from routes.contact_routes import contact_bp
    from routes.chat_routes import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(chat_bp)

    # Create all database tables
    db.create_all()
    
    # Create default admin account if it doesn't exist
    admin_user = User.query.filter_by(username=os.environ.get('ADMIN_USERNAME', 'admin')).first()
    if not admin_user:
        admin_user = User(
            username=os.environ.get('ADMIN_USERNAME', 'admin'),
            email=os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
            is_admin=True
        )
        admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'lawfirm2025'))
        db.session.add(admin_user)
        db.session.commit()
    else:
        # Update existing admin credentials if they changed in .env
        admin_user.username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_user.email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'lawfirm2025'))
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Add context processor to make datetime available to all templates
@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.utcnow()}