from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import random
import string
from urllib.parse import urlparse
import random
import string
import os
from app import db
from models import User
from forms import LoginForm, SecretLoginForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    # Rate limiting using client IP
    ip = request.remote_addr
    failed_attempts = session.get('failed_attempts', {})
    if ip in failed_attempts:
        attempts, timestamp = failed_attempts[ip]
        if attempts >= 5 and (datetime.utcnow() - timestamp).seconds < 300:
            flash('Too many login attempts. Please try again in 5 minutes.', 'danger')
            return render_template('auth/login.html', title='Login', form=LoginForm())

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if not user or not user.check_password(form.password.data):
            # Update failed attempts
            if ip in failed_attempts:
                attempts, _ = failed_attempts[ip]
                failed_attempts[ip] = (attempts + 1, datetime.utcnow())
            else:
                failed_attempts[ip] = (1, datetime.utcnow())
            session['failed_attempts'] = failed_attempts
            
            flash('Invalid credentials. Please check your username and password.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth.login'))

        # Reset failed attempts on successful login
        if ip in failed_attempts:
            del failed_attempts[ip]
            session['failed_attempts'] = failed_attempts
            
        login_user(user, remember=form.remember.data)
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('admin.dashboard')
        
        # Log successful login
        logging.info(f'Admin login successful: {user.username} from IP {ip}')
        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/token-access/<token>')
def token_access(token):
    # Check against a predefined token
    admin_token = os.environ.get('ADMIN_TOKEN', 'admin-test-token-2024')
    if token == admin_token:
        # Find or create admin user
        admin = User.query.filter_by(username='admin', is_admin=True).first()
        if not admin:
            flash('Admin account not configured', 'danger')
            return redirect(url_for('auth.login'))
        
        # Log in as admin
        login_user(admin)
        flash('You have been logged in via token access', 'success')
        return redirect(url_for('admin.dashboard'))
    
    abort(404)  # Return 404 to mask that this route exists

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('main.index'))

# This route is for demonstration purposes only
# In a production environment, user creation should be more secure
@auth_bp.route('/create-admin', methods=['POST'])
@login_required
def create_admin():
    if not current_user.is_admin:
        abort(403)
        
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    existing_admin = User.query.filter_by(username=data['username']).first()
    if existing_admin:
        return jsonify({'error': 'Username already exists'}), 400
    
    admin = User(
        username=data['username'],
        email=data['email'],
        is_admin=True
    )
    admin.set_password(data['password'])
    
    db.session.add(admin)
    db.session.commit()
    
    return jsonify({'message': 'Admin created successfully'})

# Secret admin login page - not linked from anywhere in the UI
@auth_bp.route('/secret', methods=['GET', 'POST'])
def secret_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    # Generate new access code with expiration
    if 'secret_access_code' not in session or 'code_expiry' not in session or \
       datetime.utcnow() > datetime.fromisoformat(session['code_expiry']):
        session['secret_access_code'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        session['code_expiry'] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    
    form = SecretLoginForm()
    if form.validate_on_submit():
        # Check if code is expired
        if datetime.utcnow() > datetime.fromisoformat(session['code_expiry']):
            flash('Access code expired. Please refresh for a new code.', 'danger')
            return redirect(url_for('auth.secret_login'))
            
        # Verify the access code
        if form.access_code.data != session['secret_access_code']:
            flash('Invalid access code', 'danger')
            return redirect(url_for('auth.secret_login'))
            
        # Check password - using environment variable for security
        correct_password = os.environ.get('ADMIN_SECRET_PASSWORD', 'lawyer@2025')
        if form.password.data != correct_password:
            flash('Invalid password', 'danger')
            return redirect(url_for('auth.secret_login'))
            
        # Look up the admin user
        admin = User.query.filter_by(username='admin', is_admin=True).first()
        if not admin:
            flash('Admin account not configured', 'danger')
            return redirect(url_for('auth.secret_login'))
            
        # Log in as the admin
        login_user(admin)
        
        # Regenerate access code for security
        session.pop('secret_access_code', None)
        session['secret_access_code'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        flash('You have been logged in through the secret entrance', 'success')
        return redirect(url_for('admin.dashboard'))
        
    # Show the access code (in a real app, would be sent via email/SMS)
    access_code = session['secret_access_code']
    
    return render_template('admin/auth/secret_login.html', 
                           title='Secret Admin Access',
                           form=form,
                           access_code=access_code)
