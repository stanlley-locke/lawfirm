import pytest

from app import create_app
from extensions import db
from models import User


@pytest.fixture
def app():
    application = create_app('testing')
    with application.app_context():
        db.create_all()
        admin = User(username='admin', email='admin@test.com', is_admin=True, is_active=True)
        admin.set_password('testpass123')
        db.session.add(admin)
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _complete_otp_step(client, verify_url):
    """Look up the last OTP generated during this test run and submit it."""
    from utils.otp import get_last_generated_code_for_testing
    code = get_last_generated_code_for_testing()
    if code:
        return client.post(verify_url, data={'code': code}, follow_redirects=True)
    return None


@pytest.fixture
def admin_client(client):
    client.post('/auth/login', data={'username': 'admin', 'password': 'testpass123'})
    _complete_otp_step(client, '/auth/verify-otp')
    return client
