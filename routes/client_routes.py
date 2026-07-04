from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from extensions import db
from models import LegalCase, CaseMilestone, CaseDocument, CaseInvoice, User
from forms import LoginForm

client_bp = Blueprint('client', __name__, url_prefix='/client')


@client_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('client.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()
        if not user or not user.is_active or not user.check_password(form.password.data):
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('client.login'))

        login_user(user, remember=form.remember.data)
        flash('Successfully logged in to your Client Portal!', 'success')
        
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('client.dashboard'))

    return render_template('client/login.html', title='Client Portal Login', form=form)


@client_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        flash('Admins should use the Admin Dashboard.', 'info')
        return redirect(url_for('admin.dashboard'))
    
    cases = LegalCase.query.filter_by(client_id=current_user.id).order_by(LegalCase.updated_at.desc()).all()
    return render_template('client/dashboard.html', title='Client Dashboard', cases=cases)


@client_bp.route('/cases/<int:case_id>', methods=['GET'])
@login_required
def case_detail(case_id):
    if current_user.is_admin:
        case = LegalCase.query.get_or_404(case_id)
    else:
        case = LegalCase.query.filter_by(id=case_id, client_id=current_user.id).first_or_404()
    
    return render_template('client/case_detail.html', title=case.title, case=case)


@client_bp.route('/cases/<int:case_id>/upload', methods=['POST'])
@login_required
def upload_document(case_id):
    if current_user.is_admin:
        case = LegalCase.query.get_or_404(case_id)
    else:
        case = LegalCase.query.filter_by(id=case_id, client_id=current_user.id).first_or_404()
    
    if 'document' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('client.case_detail', case_id=case.id))
        
    file = request.files['document']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('client.case_detail', case_id=case.id))
        
    if file:
        filename = secure_filename(file.filename)
        # Create folder if not exists
        upload_folder = os.path.join(current_app.root_path, 'static/uploads/cases')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file with unique name
        unique_filename = f"{case.id}_{int(datetime.utcnow().timestamp())}_{filename}"
        file.save(os.path.join(upload_folder, unique_filename))
        
        doc = CaseDocument(
            case_id=case.id,
            filename=unique_filename,
            original_name=filename,
            uploaded_by_id=current_user.id
        )
        db.session.add(doc)
        db.session.commit()
        flash('Document uploaded successfully!', 'success')
        
    return redirect(url_for('client.case_detail', case_id=case.id))


@client_bp.route('/documents/download/<int:doc_id>')
@login_required
def download_document(doc_id):
    doc = CaseDocument.query.get_or_404(doc_id)
    if not current_user.is_admin and doc.case.client_id != current_user.id:
        abort(403)
    upload_folder = os.path.join(current_app.root_path, 'static/uploads/cases')
    return send_from_directory(upload_folder, doc.filename, as_attachment=True, download_name=doc.original_name)


@client_bp.route('/invoice/<int:invoice_id>/pay', methods=['POST'])
@login_required
def pay_invoice(invoice_id):
    invoice = CaseInvoice.query.get_or_404(invoice_id)
    if not current_user.is_admin and invoice.case.client_id != current_user.id:
        abort(403)
        
    invoice.status = 'Paid'
    db.session.commit()
    flash(f'Invoice {invoice.invoice_number} paid successfully (Simulated)!', 'success')
    return redirect(url_for('client.case_detail', case_id=invoice.case_id))


@client_bp.route('/stop-impersonation', methods=['POST'])
@login_required
def stop_impersonation():
    from flask import session
    impersonator_id = session.pop('impersonator_id', None)
    if not impersonator_id:
        return redirect(url_for('client.dashboard'))
        
    admin_user = User.query.get(impersonator_id)
    if admin_user and admin_user.is_admin:
        from flask_login import login_user
        login_user(admin_user)
        flash('Switched back to Administrator account.', 'success')
        return redirect(url_for('admin.users'))
        
    return redirect(url_for('client.dashboard'))


@client_bp.route('/chat')
@login_required
def chat():
    if current_user.is_admin:
        flash('Admins should use the Admin Live Chat console.', 'info')
        return redirect(url_for('admin.dashboard'))
        
    from models import ChatRoom, ChatMessage
    room_id = f"client-user-{current_user.id}"
    
    chat_room = ChatRoom.query.filter_by(room_id=room_id).first()
    if not chat_room:
        chat_room = ChatRoom(
            room_id=room_id,
            client_name=current_user.username,
            client_email=current_user.email,
            is_active=True
        )
        db.session.add(chat_room)
        db.session.commit()
        
    messages = ChatMessage.query.filter_by(room=room_id).order_by(ChatMessage.timestamp).all()
    return render_template(
        'client/chat.html',
        title='Live Support Chat',
        room=room_id,
        messages=messages
    )


