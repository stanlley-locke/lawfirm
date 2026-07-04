from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from urllib.parse import urlparse
import logging

from models import User
from forms import LoginForm

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
        if attempts >= 5 and (datetime.utcnow() - ts).total_seconds() < 300:
            flash('Too many login attempts. Try again in 5 minutes.', 'danger')
            return render_template('auth/login.html', title='Login', form=LoginForm())

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if not user or not user.is_active or not user.check_password(form.password.data):
            record_failed_attempt(ip)
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth.login'))

        clear_failed_attempt(ip)
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('admin.dashboard')

        logger.info('Admin login successful: %s from IP %s', user.username, ip)
        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', title='Login', form=form)


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
    failed[ip] = (cnt + 1, datetime.utcnow())
    session['failed_attempts'] = failed


def clear_failed_attempt(ip):
    from flask import session
    failed = session.get('failed_attempts', {})
    failed.pop(ip, None)
    session['failed_attempts'] = failed
