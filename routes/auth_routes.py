from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user
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
    # If the user is already authenticated, redirect to admin dashboard
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Check if the user exists and the password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Log in the user
        login_user(user, remember=form.remember.data)
        
        # Check if there is a next page to redirect to
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('admin.dashboard')
        
        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('main.index'))

# This route is for demonstration purposes only
# In a production environment, user creation should be more secure
@auth_bp.route('/create-admin', methods=['GET'])
def create_admin():
    # Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        flash('Admin user already exists!', 'warning')
        return redirect(url_for('auth.login'))
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@lawfirm.com',
        is_admin=True
    )
    admin.set_password('adminpassword')
    
    db.session.add(admin)
    db.session.commit()
    
    flash('Admin user has been created! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

# Secret admin login page - not linked from anywhere in the UI
@auth_bp.route('/secret', methods=['GET', 'POST'])
def secret_login():
    # If already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    # Generate a random access code if one doesn't exist in the session
    if 'secret_access_code' not in session:
        session['secret_access_code'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    form = SecretLoginForm()
    if form.validate_on_submit():
        # Verify the access code
        if form.access_code.data != session['secret_access_code']:
            flash('Invalid access code', 'danger')
            return redirect(url_for('auth.secret_login'))
            
        # Check password matches the super admin password
        correct_password = 'lawyer@2025' # A hardcoded password for the example
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
