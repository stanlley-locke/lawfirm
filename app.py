import os
import logging
from dotenv import load_dotenv

# 1) Load .env as early as possible
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

# Base class for SQLAlchemy models
definable_Base = DeclarativeBase  # for typing
class Base(definable_Base):
    pass

# Initialize extensions (no app binding yet)
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///lawfirm.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # —— EMAIL CONFIGURATION —— #
    app.config["MAIL_SERVER"] = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("SMTP_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.environ.get("SMTP_USE_TLS", "True").lower() in ["true", "1", "t"]
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = os.environ.get("SMTP_USER")             # ← from .env: SMTP_USER
    app.config["MAIL_PASSWORD"] = os.environ.get("SMTP_PASS")             # ← from .env: SMTP_PASS
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("SMTP_USER")       # ← ensures “From” matches your Gmail

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60)

    # Flask-Login settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Inject current UTC time into templates
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}

    # Register blueprints
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

    return app  


# Create the Flask app for CLI and WSGI
app = create_app()

if __name__ == "__main__":
    # Perform initial DB setup (creates tables and default admin if needed)
    with app.app_context():
        from models import User, Service, TeamMember, CaseStudy, ContactMessage, ChatMessage, ChatRoom

        db.create_all()

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
            admin_user.username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_user.email = os.environ.get('ADMIN_EMAIL', 'stanlleylocke@gmail.com')
            admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'lawfirm2025'))
            db.session.commit()

    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
