import os
import logging
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config_by_name, validate_production_config
from extensions import db, login_manager, migrate, csrf, socketio

logging.basicConfig(level=logging.INFO)


def bootstrap_initial_admin():
    """Create the first admin user if none exists."""
    from models import User

    admin_user = User.query.filter_by(is_admin=True).first()
    if admin_user:
        return

    username = os.environ.get('ADMIN_USERNAME', 'admin')
    email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    password = os.environ.get('ADMIN_PASSWORD', 'lawfirm2025')

    admin_user = User(username=username, email=email, is_admin=True, is_active=True)
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    if app.config.get('USE_SQLITECLOUD'):
        try:
            import sqlalchemy_sqlitecloud  # noqa: F401 - registers SQLAlchemy dialect
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                'SQLite Cloud is enabled (USE_SQLITECLOUD or SQLITECLOUD_CONNECTION_STRING) '
                'but the cloud SQLAlchemy driver is not installed. '
                'Run: pip install sqlalchemy-sqlitecloud sqlitecloud'
            ) from exc

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    cors_origins = app.config.get('ALLOWED_ORIGINS') or ['http://localhost:5000']
    async_mode = 'eventlet' if config_name == 'production' else 'threading'
    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins,
        async_mode=async_mode,
        ping_timeout=60,
        manage_session=False,
    )

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_globals():
        from flask import current_app
        from sqlalchemy import desc
        from models import Service, TeamMember, CaseStudy, BlogPost
        footer_services = Service.query.filter_by(is_active=True).order_by(
            Service.display_order
        ).limit(4).all()
        nav_services = Service.query.filter_by(is_active=True).order_by(
            Service.display_order
        ).limit(6).all()
        nav_team = TeamMember.query.filter_by(is_active=True).order_by(
            TeamMember.display_order
        ).limit(4).all()
        nav_cases = CaseStudy.query.filter_by(is_active=True).order_by(
            desc(CaseStudy.created_at)
        ).limit(4).all()
        nav_blog = BlogPost.query.filter_by(is_published=True).order_by(
            BlogPost.published_at.desc()
        ).limit(4).all()
        return {
            'now': datetime.utcnow(),
            'app_name': current_app.config.get('APP_NAME'),
            'calendly_url': current_app.config.get('CALENDLY_URL'),
            'base_url': current_app.config.get('BASE_URL'),
            'footer_services': footer_services,
            'nav_services': nav_services,
            'nav_team': nav_team,
            'nav_cases': nav_cases,
            'nav_blog': nav_blog,
        }

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com "
            "https://cdn.replit.com https://cdn.tiny.cloud https://assets.calendly.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com "
            "https://cdn.replit.com https://cdn.tiny.cloud https://assets.calendly.com "
            "https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "connect-src 'self' ws: wss: https://cdn.tiny.cloud https://cdn.jsdelivr.net; "
            "frame-src https://www.google.com https://maps.google.com https://calendly.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        return response

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html', title='Page Not Found'), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template('errors/500.html', title='Server Error'), 500

    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.main_routes import main_bp
    from routes.contact_routes import contact_bp
    from routes.chat_routes import chat_bp
    from routes.client_routes import client_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(client_bp)

    if not app.config.get('TESTING'):
        with app.app_context():
            bootstrap_initial_admin()

    from commands import register_commands
    register_commands(app)

    validate_production_config(app)
    return app


if __name__ == '__main__':
    import eventlet

    eventlet.monkey_patch()

    port = int(os.environ.get('PORT', 5000))
    dev_app = create_app()
    socketio.run(dev_app, host='0.0.0.0', port=port, debug=dev_app.debug)
