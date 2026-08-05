"""Helpers for OTP (one-time-passcode) two-factor login."""
import secrets

from flask import current_app, session

OTP_LENGTH = 6

# Holds the plaintext value of the most recently generated code, but ONLY
# while running under Flask's TESTING config. This lets the test suite
# complete the two-step login flow without weakening production security
# (the database only ever stores a salted hash of the code).
_last_generated_code_for_testing = None


def generate_otp_code(length=OTP_LENGTH):
    """Generate a cryptographically secure numeric OTP code."""
    global _last_generated_code_for_testing
    code = ''.join(secrets.choice('0123456789') for _ in range(length))
    if current_app and current_app.config.get('TESTING'):
        _last_generated_code_for_testing = code
    return code


def get_last_generated_code_for_testing():
    """Test-only helper to retrieve the last generated OTP's plaintext value."""
    return _last_generated_code_for_testing


def mask_email(email):
    """Mask an email address for display, e.g. 'jo**@example.com'."""
    if not email or '@' not in email:
        return email or ''
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '*' * max(len(local) - 1, 1)
    else:
        masked_local = local[0] + ('*' * (len(local) - 2)) + local[-1]
    return f'{masked_local}@{domain}'


def send_otp_email(user, code, expiry_minutes=10):
    """Send the styled OTP verification email to the given user."""
    from utils.email_utils import send_template_email

    text_body = (
        f"Hello {user.username},\n\n"
        f"Your verification code is: {code}\n\n"
        f"This code will expire in {expiry_minutes} minutes. "
        f"If you did not request this code, you can safely ignore this email.\n\n"
        f"Never share this code with anyone.\n"
    )
    send_template_email(
        subject='Your verification code',
        recipients=[user.email],
        template_name='emails/otp_code.html',
        text_body=text_body,
        context={'user': user, 'code': code, 'expiry_minutes': expiry_minutes},
    )


def start_otp_challenge(user, role, remember=False, next_page=None):
    """Generate + email a fresh OTP and stash pending-login state in the session.

    `role` is either 'admin' or 'client' and scopes the pending challenge so
    the admin and client login flows never cross-contaminate one another.
    """
    from extensions import db

    code = generate_otp_code()
    user.set_otp(code)
    db.session.commit()
    send_otp_email(user, code)
    session['otp_user_id'] = user.id
    session['otp_role'] = role
    session['otp_remember'] = bool(remember)
    if next_page:
        session['otp_next'] = next_page
    else:
        session.pop('otp_next', None)


def get_pending_otp_user(role):
    """Return the User awaiting OTP verification for the given role, if any."""
    from models import User

    user_id = session.get('otp_user_id')
    if not user_id or session.get('otp_role') != role:
        return None
    user = User.query.get(user_id)
    if not user:
        clear_otp_session()
        return None
    return user


def clear_otp_session():
    session.pop('otp_user_id', None)
    session.pop('otp_role', None)
    session.pop('otp_remember', None)
    session.pop('otp_next', None)
