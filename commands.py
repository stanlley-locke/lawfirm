import click
from datetime import datetime

from extensions import db
from models import Service, TeamMember, CaseStudy, BlogPost, User


def register_commands(app):
    @app.cli.command('seed-demo')
    @click.option('--force', is_flag=True, help='Replace existing demo content')
    def seed_demo(force):
        """Seed the database with demo content."""
        with app.app_context():
            if force:
                BlogPost.query.delete()
                CaseStudy.query.delete()
                TeamMember.query.delete()
                Service.query.delete()
                db.session.commit()

            if Service.query.count() == 0:
                services = [
                    Service(
                        title='Corporate Law',
                        slug='corporate-law',
                        description='<p>Comprehensive corporate legal services for businesses in Kenya.</p>',
                        icon='fa-building',
                        display_order=1,
                    ),
                    Service(
                        title='Family Law',
                        slug='family-law',
                        description='<p>Compassionate representation in family and matrimonial matters.</p>',
                        icon='fa-users',
                        display_order=2,
                    ),
                    Service(
                        title='Property Law',
                        slug='property-law',
                        description='<p>Conveyancing, land disputes, and real estate transactions.</p>',
                        icon='fa-home',
                        display_order=3,
                    ),
                ]
                db.session.add_all(services)
                db.session.commit()

            if TeamMember.query.count() == 0:
                members = [
                    TeamMember(
                        name='Dan Ochieng',
                        slug='dan-ochieng',
                        position='Managing Partner',
                        bio='<p>Experienced advocate serving clients across Kisumu and Western Kenya.</p>',
                        email='info@danochiengadvocates.com',
                        display_order=1,
                    ),
                ]
                db.session.add_all(members)
                db.session.commit()

            if CaseStudy.query.count() == 0:
                svc = Service.query.first()
                cases = [
                    CaseStudy(
                        title='Successful Commercial Lease Negotiation',
                        slug='commercial-lease-negotiation',
                        client='Confidential',
                        summary='Negotiated favorable lease terms for a retail client in Kisumu.',
                        challenge='Complex lease terms with unfavorable clauses.',
                        solution='Detailed review and strategic negotiation with landlord counsel.',
                        outcome='Client secured improved terms and reduced liability exposure.',
                        service_id=svc.id if svc else None,
                        featured=True,
                    ),
                ]
                db.session.add_all(cases)
                db.session.commit()

            if BlogPost.query.count() == 0:
                author = User.query.filter_by(is_admin=True).first()
                posts = [
                    BlogPost(
                        title='Welcome to Our New Website',
                        slug='welcome-new-website',
                        summary='We are pleased to launch our updated online presence.',
                        content='<p>Our firm is committed to providing accessible legal services in Kisumu.</p>',
                        author_id=author.id if author else None,
                        is_published=True,
                        published_at=datetime.utcnow(),
                    ),
                ]
                db.session.add_all(posts)
                db.session.commit()

            click.echo('Demo content seeded successfully.')
