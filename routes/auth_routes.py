from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone
from urllib.parse import urlparse
import logging

from extensions import db
from models import User, OTP_MAX_ATTEMPTS
from forms import LoginForm, OTPForm
from utils.otp import (
    generate_otp_code, send_otp_email, mask_email,
    start_otp_challenge, get_pending_otp_user, clear_otp_session,
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    ip = request.remote_addr
    failed = session_failed_attempts()
    if ip in failed:
        attempts, ts = failed[ip]
        if attempts >= 5 and (datetime.now(timezone.utc) - ts).total_seconds() < 300:
            flash('Too many login attempts. Try again in 5 minutes.', 'danger')
            return render_template('auth/login.html', title='Login', form=LoginForm())

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()

        if not user or not user.is_active or not user.check_password(form.password.data):
            record_failed_attempt(ip)
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth.login'))

        clear_failed_attempt(ip)

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('admin.dashboard')

        start_otp_challenge(user, role='admin', remember=form.remember.data, next_page=next_page)

        logger.info('Admin credentials verified, OTP sent: %s from IP %s', user.username, ip)
        flash('We emailed you a 6-digit verification code. Enter it below to finish signing in.', 'info')
        return redirect(url_for('auth.verify_otp'))

    return render_template('auth/login.html', title='Login', form=form)


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user = get_pending_otp_user('admin')
    if not user:
        flash('Your verification session has expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    form = OTPForm()
    if form.validate_on_submit():
        if user.otp_attempts >= OTP_MAX_ATTEMPTS:
            user.clear_otp()
            db.session.commit()
            clear_otp_session()
            flash('Too many incorrect attempts. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))

        if user.otp_is_expired():
            flash('That code has expired. Please request a new one.', 'danger')
        elif user.check_otp(form.code.data):
            user.clear_otp()
            db.session.commit()
            remember = session.pop('otp_remember', False)
            next_page = session.pop('otp_next', None) or url_for('admin.dashboard')
            clear_otp_session()
            login_user(user, remember=remember)
            flash('You have been logged in successfully!', 'success')
            return redirect(next_page)
        else:
            user.otp_attempts += 1
            db.session.commit()
            flash('Incorrect verification code. Please try again.', 'danger')

    return render_template(
        'auth/verify_otp.html',
        title='Verify Code',
        form=form,
        email=mask_email(user.email),
        resend_wait_seconds=user.otp_seconds_until_resend(),
    )


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    user = get_pending_otp_user('admin')
    if not user:
        flash('Your verification session has expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    if not user.otp_resend_allowed():
        flash('Please wait a moment before requesting another code.', 'warning')
        return redirect(url_for('auth.verify_otp'))

    code = generate_otp_code()
    user.set_otp(code)
    db.session.commit()
    send_otp_email(user, code)
    flash('A new verification code has been sent to your email.', 'success')
    return redirect(url_for('auth.verify_otp'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('main.index'))


def session_failed_attempts():
    from flask import session
    return session.get('failed_attempts', {})


def record_failed_attempt(ip):
    from flask import session
    failed = session.get('failed_attempts', {})
    cnt, _ = failed.get(ip, (0, None))
    failed[ip] = (cnt + 1, datetime.now(timezone.utc))
    session['failed_attempts'] = failed


def clear_failed_attempt(ip):
    from flask import session
    failed = session.get('failed_attempts', {})
    failed.pop(ip, None)
    session['failed_attempts'] = failed
