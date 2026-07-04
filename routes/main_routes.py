from datetime import datetime

from flask import Blueprint, render_template, abort, request, Response, current_app, jsonify
from sqlalchemy import or_

from extensions import db
from models import Service, TeamMember, CaseStudy, BlogPost

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    services = Service.query.filter_by(is_active=True).order_by(Service.display_order).limit(6).all()
    featured_case_studies = CaseStudy.query.filter_by(is_active=True, featured=True).limit(3).all()
    team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.display_order).limit(4).all()
    recent_posts = BlogPost.query.filter_by(is_published=True).order_by(
        BlogPost.published_at.desc()
    ).limit(3).all()
    return render_template(
        'index.html',
        title='Home',
        services=services,
        case_studies=featured_case_studies,
        team_members=team_members,
        recent_posts=recent_posts,
    )


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
    return render_template(
        'service_detail.html',
        title=service.title,
        service=service,
        related_cases=related_cases,
    )


@main_bp.route('/team')
def team():
    team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.display_order).all()
    return render_template('team.html', title='Our Team', team_members=team_members)


@main_bp.route('/team/<slug>')
def team_member(slug):
    member = TeamMember.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template('team_member.html', title=member.name, team_member=member)


@main_bp.route('/case-studies')
def case_studies():
    studies = CaseStudy.query.filter_by(is_active=True).all()
    services = Service.query.filter_by(is_active=True).all()
    return render_template(
        'case_studies.html',
        title='Case Studies',
        case_studies=studies,
        services=services,
    )


@main_bp.route('/case-studies/<slug>')
def case_study_detail(slug):
    case_study = CaseStudy.query.filter_by(slug=slug, is_active=True).first_or_404()
    related_cases = []
    if case_study.service_id:
        related_cases = CaseStudy.query.filter(
            CaseStudy.service_id == case_study.service_id,
            CaseStudy.id != case_study.id,
            CaseStudy.is_active == True,  # noqa: E712
        ).limit(3).all()
    return render_template(
        'case_study_detail.html',
        title=case_study.title,
        case_study=case_study,
        related_cases=related_cases,
    )


@main_bp.route('/blog')
def blog():
    posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).all()
    return render_template('blog.html', title='News & Insights', posts=posts)


@main_bp.route('/blog/<slug>')
def blog_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('blog_detail.html', title=post.title, post=post)


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html', title='Privacy Policy')


@main_bp.route('/terms')
def terms():
    return render_template('terms.html', title='Terms of Service')


@main_bp.route('/appointments')
def appointments():
    calendly_url = current_app.config.get('CALENDLY_URL')
    if not calendly_url:
        abort(404)
    return render_template('appointments.html', title='Book an Appointment', calendly_url=calendly_url)


@main_bp.route('/search')
def search():
    query = (request.args.get('q') or '').strip()
    results = {'services': [], 'cases': [], 'posts': []}
    if query:
        like = f'%{query}%'
        results['services'] = Service.query.filter(
            Service.is_active == True,  # noqa: E712
            or_(Service.title.ilike(like), Service.description.ilike(like)),
        ).all()
        results['cases'] = CaseStudy.query.filter(
            CaseStudy.is_active == True,  # noqa: E712
            or_(CaseStudy.title.ilike(like), CaseStudy.summary.ilike(like)),
        ).all()
        results['posts'] = BlogPost.query.filter(
            BlogPost.is_published == True,  # noqa: E712
            or_(BlogPost.title.ilike(like), BlogPost.summary.ilike(like), BlogPost.content.ilike(like)),
        ).all()
    return render_template('search.html', title='Search', query=query, results=results)


@main_bp.route('/health')
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'ok'
    except Exception as exc:
        db_status = f'error: {exc}'
    return jsonify({'status': 'ok' if db_status == 'ok' else 'degraded', 'database': db_status})


@main_bp.route('/sitemap.xml')
def sitemap():
    pages = [
        {'loc': '/', 'priority': '1.0'},
        {'loc': '/about', 'priority': '0.8'},
        {'loc': '/services', 'priority': '0.9'},
        {'loc': '/team', 'priority': '0.8'},
        {'loc': '/case-studies', 'priority': '0.8'},
        {'loc': '/blog', 'priority': '0.8'},
        {'loc': '/contact', 'priority': '0.9'},
        {'loc': '/privacy', 'priority': '0.5'},
        {'loc': '/terms', 'priority': '0.5'},
    ]
    base = current_app.config.get('BASE_URL', '').rstrip('/')
    for service in Service.query.filter_by(is_active=True).all():
        pages.append({'loc': f'/services/{service.slug}', 'priority': '0.7'})
    for case in CaseStudy.query.filter_by(is_active=True).all():
        pages.append({'loc': f'/case-studies/{case.slug}', 'priority': '0.6'})
    for post in BlogPost.query.filter_by(is_published=True).all():
        pages.append({'loc': f'/blog/{post.slug}', 'priority': '0.6'})

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{base}{page["loc"]}</loc>')
        xml.append(f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>')
        xml.append(f'    <priority>{page["priority"]}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@main_bp.route('/track-case', methods=['GET', 'POST'])
def track_case():
    from models import LegalCase
    code = request.args.get('code') or request.form.get('code')
    case = None
    error = None
    if code:
        case = LegalCase.query.filter_by(reference_code=code.strip()).first()
        if not case:
            error = "No case found with that Reference Code. Please check and try again."
    return render_template('case_tracker.html', title='Case Tracker', case=case, code=code, error=error)

