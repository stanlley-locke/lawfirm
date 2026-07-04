import os
import re
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, or_
from functools import wraps

from extensions import db
from models import Service, TeamMember, CaseStudy, ContactMessage, BlogPost, User
from forms import (
    ServiceForm, TeamMemberForm, CaseStudyForm, BlogPostForm,
    AdminUserForm, ReplyForm,
)
from utils.sanitize import sanitize_html
from utils.email_utils import send_email, escape_html
from utils.uploads import save_upload

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin or not current_user.is_active:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def _sanitize_form_richtext(form, *fields):
    for field_name in fields:
        field = getattr(form, field_name)
        field.data = sanitize_html(field.data)


@admin_bp.route('/')
@admin_required
def dashboard():
    return render_template(
        'admin/dashboard.html',
        title='Admin Dashboard',
        services_count=Service.query.count(),
        team_members_count=TeamMember.query.count(),
        case_studies_count=CaseStudy.query.count(),
        blog_posts_count=BlogPost.query.count(),
        unread_messages_count=ContactMessage.query.filter_by(is_read=False).count(),
        recent_messages=ContactMessage.query.order_by(desc(ContactMessage.created_at)).limit(5).all(),
        # Analytics datasets for Chart.js
        analytics_months=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        analytics_contact_forms=[14, 19, 26, 12, 30, 25],
        analytics_chats=[5, 9, 7, 12, 15, 18],
        analytics_response_times=[6.2, 5.5, 4.8, 4.2, 3.8, 3.5],
        analytics_service_labels=['Land Law', 'Commercial Law', 'Company Law', 'Property & Conveyance', 'Family Law', 'Civil Litigation'],
        analytics_service_views=[450, 320, 210, 580, 290, 180]
    )



# --- Services ---
@admin_bp.route('/services')
@admin_required
def services():
    items = Service.query.order_by(Service.display_order, Service.title).all()
    return render_template('admin/services.html', title='Manage Services', services=items)


@admin_bp.route('/services/new', methods=['GET', 'POST'])
@admin_required
def new_service():
    form = ServiceForm()
    if form.validate_on_submit():
        slug = form.slug.data or re.sub(r'[^\w]+', '-', form.title.data.lower())
        _sanitize_form_richtext(form, 'description')
        service = Service(
            title=form.title.data,
            slug=slug,
            description=form.description.data,
            icon=form.icon.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        db.session.add(service)
        db.session.commit()
        flash('Service created successfully!', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_edit.html', title='New Service', form=form)


@admin_bp.route('/services/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_service(id):
    service = Service.query.get_or_404(id)
    form = ServiceForm(obj=service)
    if form.validate_on_submit():
        _sanitize_form_richtext(form, 'description')
        service.title = form.title.data
        service.slug = form.slug.data
        service.description = form.description.data
        service.icon = form.icon.data
        service.display_order = form.display_order.data
        service.is_active = form.is_active.data
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_edit.html', title='Edit Service', form=form, service=service)


@admin_bp.route('/services/delete/<int:id>', methods=['POST'])
@admin_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    if service.case_studies:
        flash('Cannot delete service with associated case studies.', 'danger')
        return redirect(url_for('admin.services'))
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully!', 'success')
    return redirect(url_for('admin.services'))


# --- Team ---
@admin_bp.route('/team')
@admin_required
def team():
    team_members = TeamMember.query.order_by(TeamMember.display_order, TeamMember.name).all()
    return render_template('admin/team.html', title='Manage Team', team_members=team_members)


@admin_bp.route('/team/new', methods=['GET', 'POST'])
@admin_required
def new_team_member():
    form = TeamMemberForm()
    if form.validate_on_submit():
        slug = form.slug.data or re.sub(r'[^\w]+', '-', form.name.data.lower())
        _sanitize_form_richtext(form, 'bio')
        member = TeamMember(
            name=form.name.data,
            slug=slug,
            position=form.position.data,
            bio=form.bio.data,
            email=form.email.data,
            phone=form.phone.data,
            photo_url=form.photo_url.data,
            linkedin=form.linkedin.data,
            twitter=form.twitter.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data,
        )
        if form.photo.data:
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'team')
            stored, _ = save_upload(form.photo.data, upload_dir, current_app.config.get('UPLOAD_EXTENSIONS'))
            member.photo_filename = stored
        db.session.add(member)
        db.session.commit()
        flash('Team member created successfully!', 'success')
        return redirect(url_for('admin.team'))
    return render_template('admin/team_edit.html', title='New Team Member', form=form)


@admin_bp.route('/team/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_team_member(id):
    team_member = TeamMember.query.get_or_404(id)
    form = TeamMemberForm(obj=team_member)
    if form.validate_on_submit():
        _sanitize_form_richtext(form, 'bio')
        team_member.name = form.name.data
        team_member.slug = form.slug.data
        team_member.position = form.position.data
        team_member.bio = form.bio.data
        team_member.email = form.email.data
        team_member.phone = form.phone.data
        team_member.photo_url = form.photo_url.data
        team_member.linkedin = form.linkedin.data
        team_member.twitter = form.twitter.data
        team_member.display_order = form.display_order.data
        team_member.is_active = form.is_active.data
        if form.photo.data:
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'team')
            stored, _ = save_upload(form.photo.data, upload_dir, current_app.config.get('UPLOAD_EXTENSIONS'))
            team_member.photo_filename = stored
        db.session.commit()
        flash('Team member updated successfully!', 'success')
        return redirect(url_for('admin.team'))
    return render_template('admin/team_edit.html', title='Edit Team Member', form=form, team_member=team_member)


@admin_bp.route('/team/delete/<int:id>', methods=['POST'])
@admin_required
def delete_team_member(id):
    team_member = TeamMember.query.get_or_404(id)
    db.session.delete(team_member)
    db.session.commit()
    flash('Team member deleted successfully!', 'success')
    return redirect(url_for('admin.team'))


# --- Case studies ---
@admin_bp.route('/cases')
@admin_required
def cases():
    case_studies = CaseStudy.query.order_by(desc(CaseStudy.created_at)).all()
    return render_template('admin/cases.html', title='Manage Case Studies', case_studies=case_studies)


@admin_bp.route('/cases/new', methods=['GET', 'POST'])
@admin_required
def new_case():
    form = CaseStudyForm()
    form.service_id.choices = [(0, 'None')] + [(s.id, s.title) for s in Service.query.order_by(Service.title).all()]
    if form.validate_on_submit():
        slug = form.slug.data or re.sub(r'[^\w]+', '-', form.title.data.lower())
        service_id = form.service_id.data if form.service_id.data and form.service_id.data > 0 else None
        _sanitize_form_richtext(form, 'summary', 'challenge', 'solution', 'outcome')
        case_study = CaseStudy(
            title=form.title.data,
            slug=slug,
            client=form.client.data,
            summary=form.summary.data,
            challenge=form.challenge.data,
            solution=form.solution.data,
            outcome=form.outcome.data,
            service_id=service_id,
            featured=form.featured.data,
            is_active=form.is_active.data,
        )
        db.session.add(case_study)
        db.session.commit()
        flash('Case study created successfully!', 'success')
        return redirect(url_for('admin.cases'))
    return render_template('admin/case_edit.html', title='New Case Study', form=form)


@admin_bp.route('/cases/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_case(id):
    case_study = CaseStudy.query.get_or_404(id)
    form = CaseStudyForm(obj=case_study)
    form.service_id.choices = [(0, 'None')] + [(s.id, s.title) for s in Service.query.order_by(Service.title).all()]
    if form.validate_on_submit():
        _sanitize_form_richtext(form, 'summary', 'challenge', 'solution', 'outcome')
        case_study.title = form.title.data
        case_study.slug = form.slug.data
        case_study.client = form.client.data
        case_study.summary = form.summary.data
        case_study.challenge = form.challenge.data
        case_study.solution = form.solution.data
        case_study.outcome = form.outcome.data
        case_study.service_id = form.service_id.data if form.service_id.data and form.service_id.data > 0 else None
        case_study.featured = form.featured.data
        case_study.is_active = form.is_active.data
        db.session.commit()
        flash('Case study updated successfully!', 'success')
        return redirect(url_for('admin.cases'))
    if case_study.service_id is None:
        form.service_id.data = 0
    return render_template('admin/case_edit.html', title='Edit Case Study', form=form, case_study=case_study)


@admin_bp.route('/cases/delete/<int:id>', methods=['POST'])
@admin_required
def delete_case(id):
    case_study = CaseStudy.query.get_or_404(id)
    db.session.delete(case_study)
    db.session.commit()
    flash('Case study deleted successfully!', 'success')
    return redirect(url_for('admin.cases'))


# --- Blog ---
@admin_bp.route('/blog')
@admin_required
def blog_posts():
    posts = BlogPost.query.order_by(desc(BlogPost.created_at)).all()
    return render_template('admin/blog.html', title='Manage Blog', posts=posts)


@admin_bp.route('/blog/new', methods=['GET', 'POST'])
@admin_required
def new_blog_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        slug = form.slug.data or re.sub(r'[^\w]+', '-', form.title.data.lower())
        _sanitize_form_richtext(form, 'summary', 'content')
        post = BlogPost(
            title=form.title.data,
            slug=slug,
            summary=form.summary.data,
            content=form.content.data,
            author_id=current_user.id,
            is_published=form.is_published.data,
            published_at=datetime.utcnow() if form.is_published.data else None,  # noqa: DTZ003
        )
        db.session.add(post)
        db.session.commit()
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin.blog_posts'))
    return render_template('admin/blog_edit.html', title='New Blog Post', form=form)


@admin_bp.route('/blog/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_blog_post(id):
    post = BlogPost.query.get_or_404(id)
    form = BlogPostForm(obj=post)
    if form.validate_on_submit():
        _sanitize_form_richtext(form, 'summary', 'content')
        post.title = form.title.data
        post.slug = form.slug.data
        post.summary = form.summary.data
        post.content = form.content.data
        if form.is_published.data and not post.published_at:
            post.published_at = datetime.utcnow()
        post.is_published = form.is_published.data
        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin.blog_posts'))
    return render_template('admin/blog_edit.html', title='Edit Blog Post', form=form, post=post)


@admin_bp.route('/blog/delete/<int:id>', methods=['POST'])
@admin_required
def delete_blog_post(id):
    post = BlogPost.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('admin.blog_posts'))


# --- Messages ---
@admin_bp.route('/messages')
@admin_required
def messages():
    msgs = ContactMessage.query.order_by(desc(ContactMessage.created_at)).all()
    unread_messages_count = ContactMessage.query.filter_by(is_read=False).count()
    return render_template(
        'admin/messages.html',
        title='Contact Messages',
        messages=msgs,
        unread_messages_count=unread_messages_count,
    )


@admin_bp.route('/messages/view/<int:id>')
@admin_required
def view_message(id):
    message = ContactMessage.query.get_or_404(id)
    if not message.is_read:
        message.is_read = True
        db.session.commit()
    return render_template(
        'admin/messages.html',
        title='View Message',
        view_message=message,
        messages=ContactMessage.query.order_by(desc(ContactMessage.created_at)).all(),
        unread_messages_count=ContactMessage.query.filter_by(is_read=False).count(),
    )


@admin_bp.route('/messages/<int:id>/read', methods=['POST'])
@admin_required
def mark_message_read(id):
    message = ContactMessage.query.get_or_404(id)
    message.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'id': id})


@admin_bp.route('/messages/<int:id>/reply', methods=['GET', 'POST'])
@admin_required
def reply_message(id):
    message = ContactMessage.query.get_or_404(id)
    form = ReplyForm()
    if not form.subject.data:
        form.subject.data = f"Re: {message.subject}"
    if form.validate_on_submit():
        send_email(
            subject=form.subject.data,
            recipients=[message.email],
            text_body=form.body.data,
            html_body=f"<p>{escape_html(form.body.data).replace(chr(10), '<br>')}</p>",
            reply_to=current_app.config.get('RESEND_FROM_EMAIL'),
        )
        if not message.is_read:
            message.is_read = True
            db.session.commit()
        flash('Reply sent successfully.', 'success')
        return redirect(url_for('admin.view_message', id=id))
    return render_template('admin/reply_message.html', title='Reply to Message', form=form, message=message)


@admin_bp.route('/messages/<int:id>/quick-reply', methods=['POST'])
@admin_required
def quick_reply_message(id):
    import base64
    message = ContactMessage.query.get_or_404(id)
    reply_body = request.form.get('body')
    if not reply_body:
        return jsonify({'error': 'Reply body is required'}), 400
    
    # Process attachments
    attachments = []
    if 'attachments' in request.files:
        files = request.files.getlist('attachments')
        for file in files:
            if file.filename:
                file_bytes = file.read()
                b64_content = base64.b64encode(file_bytes).decode('utf-8')
                attachments.append({
                    'content': b64_content,
                    'filename': file.filename
                })
                
    send_email(
        subject=f"Re: {message.subject}",
        recipients=[message.email],
        text_body=reply_body,
        html_body=f"<p>{escape_html(reply_body).replace(chr(10), '<br>')}</p>",
        reply_to=current_app.config.get('RESEND_FROM_EMAIL'),
        attachments=attachments if attachments else None
    )
    if not message.is_read:
        message.is_read = True
        db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/messages/delete/<int:id>', methods=['POST'])
@admin_required
def delete_message(id):
    message = ContactMessage.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully!', 'success')
    return redirect(url_for('admin.messages'))


# --- Users ---
@admin_bp.route('/users')
@admin_required
def users():
    all_users = User.query.order_by(User.is_admin.desc(), User.username).all()
    return render_template('admin/users.html', title='Manage Users', users=all_users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    form = AdminUserForm()
    if form.validate_on_submit():
        if not form.password.data:
            flash('Password is required for new users.', 'danger')
            return render_template('admin/user_edit.html', title='New Admin User', form=form)
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data,
            is_active=form.is_active.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Send welcome email asynchronously
        from utils.email_utils import send_email
        from flask import request
        
        login_url = request.url_root.rstrip('/') + (url_for('auth.login') if user.is_admin else url_for('client.login'))
        role_name = "Administrator" if user.is_admin else "Client"
        
        subject = f"Welcome to DOA Advocates - Your Account Details"
        text_body = (
            f"Hello {user.username},\n\n"
            f"An account has been created for you on the Dan Ochieng & Company Advocates portal.\n\n"
            f"Here are your login credentials:\n"
            f"Role: {role_name}\n"
            f"Username: {user.username}\n"
            f"Password: {form.password.data}\n\n"
            f"You can log in to your dashboard here:\n"
            f"{login_url}\n\n"
            f"Please change your password after logging in for security reasons.\n\n"
            f"Best regards,\n"
            f"DOA Advocates Team"
        )
        html_body = (
            f"<div style='font-family: sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto;'>"
            f"<h2 style='color: #082068;'>Welcome to DOA Advocates</h2>"
            f"<p>Hello <strong>{user.username}</strong>,</p>"
            f"<p>An account has been created for you on the Dan Ochieng & Company Advocates portal as an <strong>{role_name}</strong>.</p>"
            f"<div style='background-color: #f8fafc; padding: 15px; border-left: 4px solid #082068; margin: 20px 0;'>"
            f"<p style='margin: 0 0 8px 0;'><strong>Username:</strong> {user.username}</p>"
            f"<p style='margin: 0 0 8px 0;'><strong>Password:</strong> <code style='background: #e2e8f0; padding: 2px 4px;'>{form.password.data}</code></p>"
            f"<p style='margin: 0;'><strong>Login Link:</strong> <a href='{login_url}' style='color: #00c8f8; text-decoration: none; font-weight: bold;'>Go to Portal</a></p>"
            f"</div>"
            f"<p style='font-size: 0.9em; color: #64748b;'>For security, please change your password after logging in.</p>"
            f"<hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;'>"
            f"<p style='font-size: 0.8em; color: #94a3b8;'>This is an automated message from Dan Ochieng & Company Advocates.</p>"
            f"</div>"
        )
        try:
            send_email(
                subject=subject,
                recipients=[user.email],
                text_body=text_body,
                html_body=html_body
            )
        except Exception as e:
            current_app.logger.error("Failed to send welcome email: %s", str(e))

        flash('User created successfully and welcome details emailed!', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_edit.html', title='New Admin User', form=form)


@admin_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = AdminUserForm(obj=user, user=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Admin user updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_edit.html', title='Edit Admin User', form=form, user=user)


@admin_bp.route('/users/deactivate/<int:id>', methods=['POST'])
@admin_required
def deactivate_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = False
    db.session.commit()
    flash('User deactivated successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/impersonate/<int:id>', methods=['POST'])
@admin_required
def impersonate_user(id):
    from flask import session
    from flask_login import login_user
    user = User.query.get_or_404(id)
    if user.is_admin:
        flash('Cannot impersonate another administrator.', 'danger')
        return redirect(url_for('admin.users'))
        
    session['impersonator_id'] = current_user.id
    login_user(user)
    flash(f'Logged in as {user.username}. You are now viewing their dashboard.', 'success')
    return redirect(url_for('client.dashboard'))


# Client Cases Management
@admin_bp.route('/client-cases')
@admin_required
def client_cases():
    from models import LegalCase
    cases = LegalCase.query.order_by(LegalCase.created_at.desc()).all()
    return render_template('admin/client_cases.html', title='Manage Client Cases', cases=cases)


@admin_bp.route('/client-cases/new', methods=['GET', 'POST'])
@admin_required
def new_client_case():
    from models import LegalCase, User
    from forms import ClientCaseForm
    import uuid
    form = ClientCaseForm()
    
    clients = User.query.filter_by(is_admin=False).all()
    form.client_id.choices = [(c.id, f"{c.username} ({c.email})") for c in clients]
    
    if form.validate_on_submit():
        ref_code = form.reference_code.data.strip() if form.reference_code.data else None
        if not ref_code:
            ref_code = f"REF-{uuid.uuid4().hex[:8].upper()}"
            
        case = LegalCase(
            case_number=form.case_number.data,
            title=form.title.data,
            description=form.description.data,
            client_id=form.client_id.data,
            case_type=form.case_type.data,
            status=form.status.data,
            reference_code=ref_code
        )
        db.session.add(case)
        db.session.commit()
        flash('Client case created successfully!', 'success')
        return redirect(url_for('admin.client_cases'))
        
    return render_template('admin/client_case_edit.html', title='New Client Case', form=form)


@admin_bp.route('/client-cases/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_client_case(id):
    from models import LegalCase, User
    from forms import ClientCaseForm
    case = LegalCase.query.get_or_404(id)
    form = ClientCaseForm(obj=case)
    
    clients = User.query.filter_by(is_admin=False).all()
    form.client_id.choices = [(c.id, f"{c.username} ({c.email})") for c in clients]
    
    if form.validate_on_submit():
        case.case_number = form.case_number.data
        case.title = form.title.data
        case.description = form.description.data
        case.client_id = form.client_id.data
        case.case_type = form.case_type.data
        case.status = form.status.data
        if form.reference_code.data:
            case.reference_code = form.reference_code.data.strip()
            
        db.session.commit()
        flash('Client case updated successfully!', 'success')
        return redirect(url_for('admin.client_cases'))
        
    return render_template('admin/client_case_edit.html', title='Edit Client Case', form=form, case=case)


@admin_bp.route('/client-cases/delete/<int:id>', methods=['POST'])
@admin_required
def delete_client_case(id):
    from models import LegalCase
    case = LegalCase.query.get_or_404(id)
    db.session.delete(case)
    db.session.commit()
    flash('Client case deleted successfully.', 'success')
    return redirect(url_for('admin.client_cases'))


@admin_bp.route('/client-cases/<int:case_id>/milestones', methods=['GET', 'POST'])
@admin_required
def case_milestones(case_id):
    from models import LegalCase, CaseMilestone
    from forms import MilestoneForm
    case = LegalCase.query.get_or_404(case_id)
    form = MilestoneForm()
    
    if form.validate_on_submit():
        milestone_date = datetime.combine(form.date.data, datetime.min.time())
        milestone = CaseMilestone(
            case_id=case.id,
            title=form.title.data,
            description=form.description.data,
            date=milestone_date,
            status=form.status.data
        )
        db.session.add(milestone)
        db.session.commit()
        flash('Milestone added successfully!', 'success')
        return redirect(url_for('admin.case_milestones', case_id=case.id))
        
    return render_template('admin/case_milestones.html', title=f'Milestones - {case.title}', case=case, form=form)


@admin_bp.route('/client-cases/<int:case_id>/milestones/delete/<int:milestone_id>', methods=['POST'])
@admin_required
def delete_milestone(case_id, milestone_id):
    from models import CaseMilestone
    milestone = CaseMilestone.query.get_or_404(milestone_id)
    db.session.delete(milestone)
    db.session.commit()
    flash('Milestone deleted successfully.', 'success')
    return redirect(url_for('admin.case_milestones', case_id=case_id))


@admin_bp.route('/client-cases/<int:case_id>/invoices', methods=['GET', 'POST'])
@admin_required
def case_invoices(case_id):
    from models import LegalCase, CaseInvoice
    from forms import InvoiceForm
    case = LegalCase.query.get_or_404(case_id)
    form = InvoiceForm()
    
    if form.validate_on_submit():
        due_datetime = datetime.combine(form.due_date.data, datetime.min.time())
        invoice = CaseInvoice(
            case_id=case.id,
            invoice_number=form.invoice_number.data,
            amount=form.amount.data,
            due_date=due_datetime,
            status=form.status.data
        )
        db.session.add(invoice)
        db.session.commit()
        flash('Invoice added successfully!', 'success')
        return redirect(url_for('admin.case_invoices', case_id=case.id))
        
    return render_template('admin/case_invoices.html', title=f'Invoices - {case.title}', case=case, form=form)


@admin_bp.route('/client-cases/<int:case_id>/invoices/delete/<int:invoice_id>', methods=['POST'])
@admin_required
def delete_invoice(case_id, invoice_id):
    from models import CaseInvoice
    invoice = CaseInvoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    flash('Invoice deleted successfully.', 'success')
    return redirect(url_for('admin.case_invoices', case_id=case_id))


@admin_bp.route('/generate-document', methods=['GET', 'POST'])
@admin_required
def generate_document():
    if request.method == 'POST':
        template_type = request.form.get('template_type')
        
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from flask import send_file
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor='#082068',
            spaceAfter=20,
            alignment=1
        )
        body_style = ParagraphStyle(
            'DocBody',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=11,
            leading=16,
            textColor='#333333',
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'DocHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor='#082068',
            spaceBefore=15,
            spaceAfter=10
        )
        
        if template_type == 'nda':
            disclosing_party = request.form.get('disclosing_party', 'Disclosing Party')
            receiving_party = request.form.get('receiving_party', 'Receiving Party')
            purpose = request.form.get('purpose', 'the Evaluation of a Business Relationship')
            date_str = request.form.get('agreement_date', datetime.utcnow().strftime('%Y-%m-%d'))
            
            story.append(Paragraph("MUTUAL NON-DISCLOSURE AGREEMENT", title_style))
            story.append(Spacer(1, 15))
            
            text1 = f"This Mutual Non-Disclosure Agreement (the \"Agreement\") is entered into on this <b>{date_str}</b> by and between:"
            story.append(Paragraph(text1, body_style))
            story.append(Paragraph(f"1. <b>{disclosing_party}</b> (\"Disclosing Party\"); and", body_style))
            story.append(Paragraph(f"2. <b>{receiving_party}</b> (\"Receiving Party\").", body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("1. Purpose", heading_style))
            story.append(Paragraph(f"The parties wish to disclose to each other certain confidential information for the sole purpose of: <i>{purpose}</i>.", body_style))
            
            story.append(Paragraph("2. Confidential Information", heading_style))
            story.append(Paragraph("Confidential Information includes all information, whether oral, written, or visual, disclosed by one party to the other that is marked confidential or should reasonably be understood to be confidential given the nature of the information.", body_style))
            
            story.append(Paragraph("3. Non-Disclosure Obligations", heading_style))
            story.append(Paragraph("The Receiving Party agrees to hold the Confidential Information in strict confidence and not to disclose it to any third party without the prior written consent of the Disclosing Party. The Receiving Party shall protect the Confidential Information using at least the same degree of care it uses to protect its own confidential information.", body_style))
            
            story.append(Spacer(1, 30))
            story.append(Paragraph("IN WITNESS WHEREOF, the parties hereto have executed this Agreement.", body_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph("___________________________<br/><b>For Disclosing Party</b>", body_style))
            story.append(Spacer(1, 15))
            story.append(Paragraph("___________________________<br/><b>For Receiving Party</b>", body_style))
            
        elif template_type == 'sales_agreement':
            seller = request.form.get('seller', 'Seller Name')
            buyer = request.form.get('buyer', 'Buyer Name')
            item = request.form.get('item', 'Item Description')
            price = request.form.get('price', '0.00')
            payment_terms = request.form.get('payment_terms', 'Paid in full on signing')
            date_str = request.form.get('agreement_date', datetime.utcnow().strftime('%Y-%m-%d'))
            
            story.append(Paragraph("AGREEMENT OF SALE", title_style))
            story.append(Spacer(1, 15))
            
            story.append(Paragraph(f"This Sales Agreement (the \"Agreement\") is made on <b>{date_str}</b>, by and between:", body_style))
            story.append(Paragraph(f"<b>Seller:</b> {seller}<br/><b>Buyer:</b> {buyer}", body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("1. Sale of Property/Goods", heading_style))
            story.append(Paragraph(f"The Seller hereby agrees to sell, and the Buyer agrees to purchase, the following item/property: <br/><i>{item}</i>.", body_style))
            
            story.append(Paragraph("2. Purchase Price & Payment", heading_style))
            story.append(Paragraph(f"The agreed purchase price for the property/goods is <b>KES {price}</b>.", body_style))
            story.append(Paragraph(f"Payment Terms: {payment_terms}.", body_style))
            
            story.append(Paragraph("3. Delivery and Title Transfer", heading_style))
            story.append(Paragraph("The Seller guarantees that they are the lawful owner of the item/property and that it is free from all encumbrances. Ownership and risk of loss transfer to the Buyer upon full payment of the purchase price.", body_style))
            
            story.append(Spacer(1, 30))
            story.append(Paragraph("___________________________<br/><b>Seller Signature</b>", body_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph("___________________________<br/><b>Buyer Signature</b>", body_style))
            
        elif template_type == 'demand_letter':
            debtor = request.form.get('debtor_name', 'Debtor Name')
            debtor_address = request.form.get('debtor_address', 'Debtor Address')
            amount = request.form.get('amount', '0.00')
            reason = request.form.get('reason', 'unpaid services')
            deadline = request.form.get('deadline_date', '7 days from date hereof')
            advocate = request.form.get('advocate_name', 'Dan Ochieng, Advocate')
            
            story.append(Paragraph("FORMAL LETTER OF DEMAND", title_style))
            story.append(Spacer(1, 15))
            
            story.append(Paragraph(f"<b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d')}<br/><b>To:</b> {debtor}<br/><b>Address:</b> {debtor_address}", body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("RE: DEMAND FOR OUTSTANDING PAYMENT", heading_style))
            story.append(Paragraph(f"We act on behalf of our client, who has instructed us to write to you regarding an outstanding debt of <b>KES {amount}</b>.", body_style))
            story.append(Paragraph(f"This debt arose as a result of: <i>{reason}</i>.", body_style))
            story.append(Paragraph(f"Take notice that you are hereby demanded to pay the sum of <b>KES {amount}</b> within <b>{deadline}</b> failing which our client has given us strict instructions to file legal proceedings against you in a court of law without further reference to you.", body_style))
            story.append(Paragraph("Such legal action will include claims for interest, legal costs, and disbursements incurred.", body_style))
            
            story.append(Spacer(1, 30))
            story.append(Paragraph("Yours faithfully,", body_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"___________________________<br/><b>{advocate}</b><br/>For: Dan Ochieng & Company Advocates", body_style))
            
        doc.build(story)
        buffer.seek(0)
        
        filename = f"{template_type}_generated_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
        
    return render_template('admin/generate_document.html', title='Document Template Generator')

