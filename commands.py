import os
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

    @app.cli.command('test-sqlitecloud')
    def test_sqlitecloud():
        """Test SQLite Cloud native driver, Weblite REST, SQLAlchemy, and Flask-SQLAlchemy."""
        import sqlitecloud
        from sqlalchemy import create_engine, text
        from models import User
        from utils.sqlitecloud import (
            WebliteClient,
            get_sqlitecloud_connection_string,
            redact_connection_string,
        )

        if not app.config.get('USE_SQLITECLOUD'):
            click.echo(
                'SQLite Cloud is not enabled. Set USE_SQLITECLOUD=true in .env first.'
            )
            raise SystemExit(1)

        conn_str = get_sqlitecloud_connection_string()
        click.echo(f'Connection: {redact_connection_string(conn_str)}')

        if os.getenv('SQLITECLOUD_GATEWAY_URL'):
            click.echo('Testing Weblite REST API...')
            try:
                client = WebliteClient()
                databases = client.list_databases()
                db_names = [item.get('name') for item in databases.get('data', [])]
                click.echo(f'  Databases: {", ".join(db_names) or "(none)"}')
            except RuntimeError as exc:
                click.echo(f'  REST API: {exc}')
                click.echo('  (Native driver is used for the app; REST is optional.)')

        click.echo('Testing native sqlitecloud driver...')
        conn = sqlitecloud.connect(conn_str)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        click.echo(f'  Tables: {", ".join(tables) or "(none)"}')
        conn.close()

        click.echo('Testing SQLAlchemy engine...')
        import sqlalchemy_sqlitecloud  # noqa: F401 — registers dialect
        engine = create_engine(conn_str)
        with engine.connect() as connection:
            result = connection.execute(text('SELECT COUNT(*) FROM user')).scalar()
        click.echo(f'  User count (SQLAlchemy): {result}')

        click.echo('Testing Flask-SQLAlchemy...')
        user_count = User.query.count()
        click.echo(f'  User count (Flask db): {user_count}')
        click.echo('SQLite Cloud connection OK.')
