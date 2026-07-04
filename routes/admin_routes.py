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
    admins = User.query.filter_by(is_admin=True).order_by(User.username).all()
    return render_template('admin/users.html', title='Manage Admin Users', users=admins)


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
        flash('Admin user created successfully!', 'success')
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
