from flask import Blueprint, render_template, abort
from models import Service, TeamMember, CaseStudy

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get featured services and case studies for homepage
    services = Service.query.filter_by(is_active=True).order_by(Service.display_order).limit(6).all()
    featured_case_studies = CaseStudy.query.filter_by(is_active=True, featured=True).limit(3).all()
    team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.display_order).limit(4).all()
    
    return render_template('index.html', 
                          title='Home', 
                          services=services, 
                          case_studies=featured_case_studies,
                          team_members=team_members)

@main_bp.route('/about')
def about():
    team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.display_order).all()
    return render_template('about.html', title='About Us', team_members=team_members)

@main_bp.route('/services')
def services():
    services = Service.query.filter_by(is_active=True).order_by(Service.display_order).all()
    return render_template('services.html', title='Our Services', services=services)

@main_bp.route('/services/<slug>')
def service_detail(slug):
    service = Service.query.filter_by(slug=slug, is_active=True).first_or_404()
    related_cases = CaseStudy.query.filter_by(service_id=service.id, is_active=True).all()
    
    return render_template('service_detail.html', 
                          title=service.title, 
                          service=service,
                          related_cases=related_cases)

@main_bp.route('/team')
def team():
    team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.display_order).all()
    return render_template('team.html', title='Our Team', team_members=team_members)

@main_bp.route('/team/<slug>')
def team_member(slug):
    team_member = TeamMember.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template('team_member.html', title=team_member.name, team_member=team_member)

@main_bp.route('/case-studies')
def case_studies():
    case_studies = CaseStudy.query.filter_by(is_active=True).all()
    services = Service.query.filter_by(is_active=True).all()
    
    return render_template('case_studies.html', 
                          title='Case Studies', 
                          case_studies=case_studies,
                          services=services)

@main_bp.route('/case-studies/<slug>')
def case_study_detail(slug):
    case_study = CaseStudy.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Get related case studies (same service)
    related_cases = []
    if case_study.service_id:
        related_cases = CaseStudy.query.filter(
            CaseStudy.service_id == case_study.service_id,
            CaseStudy.id != case_study.id,
            CaseStudy.is_active == True
        ).limit(3).all()
    
    return render_template('case_study_detail.html', 
                          title=case_study.title, 
                          case_study=case_study,
                          related_cases=related_cases)
