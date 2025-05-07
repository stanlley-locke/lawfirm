# app/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import random
import string
import logging
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlparse
from dotenv import load_dotenv
import os

from app import db
from models import User
from forms import LoginForm, SecretLoginForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

load_dotenv()


# ======= SMTP SETTINGS =======
# These settings are loaded from environment variables for security.
SMTP_HOST       = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT       = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER       = os.getenv('SMTP_USER')
SMTP_PASS       = os.getenv('SMTP_PASS')
SMTP_USE_TLS    = os.getenv('SMTP_USE_TLS', 'True') == 'True'
TEST_RECIPIENT  = os.getenv('TEST_RECIPIENT', SMTP_USER)
# ======= END SMTP SETTINGS =======



# ======= EMAIL SENDER FUNCTION =======
def send_email(subject: str, recipient: str, body: str):
    """Send an email via the hard-coded SMTP test account."""
    msg = MIMEText(body, _charset='utf-8')
    msg['Subject'] = subject
    msg['From']    = SMTP_USER
    msg['To']      = recipient

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    try:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    finally:
        server.quit()



@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    # Rate limiting by client IP
    ip = request.remote_addr
    failed = session.get('failed_attempts', {})
    if ip in failed:
        attempts, ts = failed[ip]
        if attempts >= 5 and (datetime.utcnow() - ts).seconds < 300:
            flash('Too many login attempts. Try again in 5 minutes.', 'danger')
            return render_template('auth/login.html',
                                   title='Login',
                                   form=LoginForm())

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if not user or not user.check_password(form.password.data):
            # record failure
            cnt, _ = failed.get(ip, (0, None))
            failed[ip] = (cnt + 1, datetime.utcnow())
            session['failed_attempts'] = failed
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth.login'))

        # reset failures
        failed.pop(ip, None)
        session['failed_attempts'] = failed

        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('admin.dashboard')

        logging.info(f'Admin login successful: {user.username} from IP {ip}')
        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', title='Login', form=form)


@auth_bp.route('/token-access/<token>')
def token_access(token):
    admin_token = os.environ.get('ADMIN_TOKEN', 'admin-test-token-2024')
    if token == admin_token:
        admin = User.query.filter_by(username='admin', is_admin=True).first()
        if not admin:
            flash('Admin account not configured', 'danger')
            return redirect(url_for('auth.login'))
        login_user(admin)
        flash('You have been logged in via token access', 'success')
        return redirect(url_for('admin.dashboard'))

    abort(404)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/create-admin', methods=['POST'])
@login_required
def create_admin():
    if not current_user.is_admin:
        abort(403)

    data = request.get_json() or {}
    if not all(k in data for k in ('username', 'email', 'password')):
        return {'error': 'Missing required fields'}, 400

    if User.query.filter_by(username=data['username']).first():
        return {'error': 'Username already exists'}, 400

    admin = User(username=data['username'],
                 email=data['email'],
                 is_admin=True)
    admin.set_password(data['password'])
    db.session.add(admin)
    db.session.commit()
    return {'message': 'Admin created successfully'}, 200


@auth_bp.route('/secret', methods=['GET', 'POST'])
def secret_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    # Generate or renew code if missing/expired
    need_new = (
        'secret_access_code' not in session or
        'code_expiry' not in session or
        datetime.utcnow() > datetime.fromisoformat(session['code_expiry'])
    )
    if need_new:
        code   = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        expiry = datetime.utcnow() + timedelta(minutes=5)
        session['secret_access_code'] = code
        session['code_expiry']        = expiry.isoformat()

        # email it immediately
        try:
            send_email(
                subject="Your One-Time Admin Access Code",
                recipient=TEST_RECIPIENT,
                body=(
                    f"Hello Admin,\n\n"
                    f"Your one-time access code is: {code}\n"
                    f"It expires at {expiry.isoformat()} UTC.\n\n"
                    f"If you did not request this, please ignore."
                )
            )
            flash('A one-time access code has been emailed to you.', 'info')
        except Exception:
            logging.exception("Failed to send access code email")
            flash('Error sending access code. Please try again later.', 'danger')
            return redirect(url_for('auth.login'))

    form = SecretLoginForm()
    if form.validate_on_submit():
        # expiry check
        if datetime.utcnow() > datetime.fromisoformat(session['code_expiry']):
            flash('Access code expired. Please refresh for a new code.', 'danger')
            return redirect(url_for('auth.secret_login'))

        if form.access_code.data != session['secret_access_code']:
            flash('Invalid access code', 'danger')
            return redirect(url_for('auth.secret_login'))

        # static password for POC
        if form.password.data != 'lawyer@2025':
            flash('Invalid password', 'danger')
            return redirect(url_for('auth.secret_login'))

        admin = User.query.filter_by(username='admin', is_admin=True).first()
        if not admin:
            flash('Admin account not configured', 'danger')
            return redirect(url_for('auth.secret_login'))

        login_user(admin)
        session.pop('secret_access_code', None)
        session.pop('code_expiry', None)

        flash('You have been logged in through the secret entrance', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/auth/secret_login.html',
                           title='Secret Admin Access',
                           form=form)
