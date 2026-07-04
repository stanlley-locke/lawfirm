import os


def _env_bool(name, default='False'):
    return os.getenv(name, default).lower() in ('true', '1', 't', 'yes')


def _env_list(name, default=''):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(',') if item.strip()]


class Config:
    """Central application configuration."""

    SECRET_KEY = os.getenv('SESSION_SECRET', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///lawfirm.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session security
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', 'False')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 86400))

    # Resend email
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    RESEND_FROM_EMAIL = os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
    ADMIN_NOTIFICATION_EMAIL = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'admin@example.com')

    # App metadata
    APP_NAME = os.getenv('APP_NAME', 'Dan Ochieng & Company Advocates')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    ALLOWED_ORIGINS = _env_list('ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000')

    # Admin bootstrap
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

    # Business hours auto-reply
    BUSINESS_HOURS_TZ = os.getenv('BUSINESS_HOURS_TZ', 'Africa/Nairobi')
    BUSINESS_HOURS_START = int(os.getenv('BUSINESS_HOURS_START', 9))
    BUSINESS_HOURS_END = int(os.getenv('BUSINESS_HOURS_END', 17))
    BUSINESS_HOURS_DAYS = [int(d) for d in _env_list('BUSINESS_HOURS_DAYS', '0,1,2,3,4')]

    # Calendly
    CALENDLY_URL = os.getenv('CALENDLY_URL', '')

    # Upload limits
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))
    UPLOAD_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    CHAT_UPLOAD_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_SECRET = 'test-secret'
    RESEND_API_KEY = 're_test_key'
    ADMIN_PASSWORD = 'test-admin-password'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def validate_production_config(app):
    """Fail fast when required secrets are missing in production."""
    if app.config.get('TESTING'):
        return
    if app.debug:
        return
    env = os.getenv('FLASK_ENV', 'development')
    if env != 'production':
        return

    required = {
        'SESSION_SECRET': app.config.get('SECRET_KEY'),
        'ADMIN_PASSWORD': app.config.get('ADMIN_PASSWORD'),
        'RESEND_API_KEY': app.config.get('RESEND_API_KEY'),
    }
    missing = [name for name, value in required.items() if not value or value.startswith('dev-')]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables for production: {', '.join(missing)}"
        )
