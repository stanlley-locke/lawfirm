from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Service, TeamMember, CaseStudy, ContactMessage
from forms import ServiceForm, TeamMemberForm, CaseStudyForm
from sqlalchemy import desc
import re

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Custom decorator to check if user is admin
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    # Get counts for dashboard
    services_count = Service.query.count()
    team_members_count = TeamMember.query.count()
    case_studies_count = CaseStudy.query.count()
    unread_messages_count = ContactMessage.query.filter_by(is_read=False).count()
    
    # Get recent messages
    recent_messages = ContactMessage.query.order_by(desc(ContactMessage.created_at)).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          title='Admin Dashboard',
                          services_count=services_count,
                          team_members_count=team_members_count,
                          case_studies_count=case_studies_count,
                          unread_messages_count=unread_messages_count,
                          recent_messages=recent_messages)

# Services management
@admin_bp.route('/services')
@admin_required
def services():
    services = Service.query.order_by(Service.display_order, Service.title).all()
    return render_template('admin/services.html', title='Manage Services', services=services)

@admin_bp.route('/services/new', methods=['GET', 'POST'])
@admin_required
def new_service():
    form = ServiceForm()
    
    if form.validate_on_submit():
        # Generate slug if not provided
        slug = form.slug.data if form.slug.data else re.sub(r'[^\w]+', '-', form.title.data.lower())
        
        service = Service(
            title=form.title.data,
            slug=slug,
            description=form.description.data,
            icon=form.icon.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data
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
    
    # Check if service has case studies
    if service.case_studies:
        flash('Cannot delete service with associated case studies. Please reassign or delete the case studies first.', 'danger')
        return redirect(url_for('admin.services'))
    
    db.session.delete(service)
    db.session.commit()
    
    flash('Service deleted successfully!', 'success')
    return redirect(url_for('admin.services'))

# Team members management
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
        # Generate slug if not provided
        slug = form.slug.data if form.slug.data else re.sub(r'[^\w]+', '-', form.name.data.lower())
        
        team_member = TeamMember(
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
            is_active=form.is_active.data
        )
        
        db.session.add(team_member)
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

# Case studies management
@admin_bp.route('/cases')
@admin_required
def cases():
    case_studies = CaseStudy.query.order_by(desc(CaseStudy.created_at)).all()
    return render_template('admin/cases.html', title='Manage Case Studies', case_studies=case_studies)

@admin_bp.route('/cases/new', methods=['GET', 'POST'])
@admin_required
def new_case():
    form = CaseStudyForm()
    # Populate service choices
    form.service_id.choices = [(0, 'None')] + [(s.id, s.title) for s in Service.query.order_by(Service.title).all()]
    
    if form.validate_on_submit():
        # Generate slug if not provided
        slug = form.slug.data if form.slug.data else re.sub(r'[^\w]+', '-', form.title.data.lower())
        
        # Handle service_id being None or 0
        service_id = form.service_id.data if form.service_id.data and form.service_id.data > 0 else None
        
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
            is_active=form.is_active.data
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
    # Populate service choices
    form.service_id.choices = [(0, 'None')] + [(s.id, s.title) for s in Service.query.order_by(Service.title).all()]
    
    if form.validate_on_submit():
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
    
    # Set the current service_id
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

# Messages management
@admin_bp.route('/messages')
@admin_required
def messages():
    messages = ContactMessage.query.order_by(desc(ContactMessage.created_at)).all()
    return render_template('admin/messages.html', title='Contact Messages', messages=messages)

@admin_bp.route('/messages/view/<int:id>')
@admin_required
def view_message(id):
    message = ContactMessage.query.get_or_404(id)
    
    # Mark message as read if it wasn't
    if not message.is_read:
        message.is_read = True
        db.session.commit()
    
    return render_template('admin/messages.html', title='View Message', view_message=message, 
                          messages=ContactMessage.query.order_by(desc(ContactMessage.created_at)).all())

@admin_bp.route('/messages/delete/<int:id>', methods=['POST'])
@admin_required
def delete_message(id):
    message = ContactMessage.query.get_or_404(id)
    
    db.session.delete(message)
    db.session.commit()
    
    flash('Message deleted successfully!', 'success')
    return redirect(url_for('admin.messages'))
