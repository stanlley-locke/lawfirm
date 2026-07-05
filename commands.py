import os
import click
from datetime import datetime

from extensions import db
from models import Service, TeamMember, CaseStudy, BlogPost, User

TEAM_PHOTOS = [
    '/static/images/assets/patrick-fore-H5Lf0nGyetk-unsplash.webp',
    '/static/images/assets/mikhail-pavstyuk-EKy2OTRPXdw-unsplash.webp',
    '/static/images/assets/giammarco-boscaro-zeH-ljawHtg-unsplash.webp',
    '/static/images/assets/tingey-injury-law-firm-yCdPU73kGSc-unsplash.webp',
]

FIRM_EMAIL = 'danochiengadvocates@gmail.com'

SERVICE_DEFINITIONS = [
    {
        'title': 'Land Matters',
        'slug': 'land-matters',
        'description': (
            '<p>Expert representation and advisory on land ownership, boundaries, '
            'title disputes, and regulatory compliance across Kenya.</p>'
        ),
        'icon': 'fas fa-map-marked-alt',
        'display_order': 1,
    },
    {
        'title': 'General Civil Litigation',
        'slug': 'civil-litigation',
        'description': (
            '<p>Skilled advocacy in civil disputes before Kenyan courts, from case '
            'assessment through trial and enforcement of judgments.</p>'
        ),
        'icon': 'fas fa-gavel',
        'display_order': 2,
    },
    {
        'title': 'Conveyances & Property',
        'slug': 'conveyances-property',
        'description': (
            '<p>Conveyancing, property transfers, lease agreements, and related '
            'real estate transactions handled with precision and due diligence.</p>'
        ),
        'icon': 'fas fa-home',
        'display_order': 3,
    },
    {
        'title': 'Arbitration & ADR',
        'slug': 'arbitration-adr',
        'description': (
            '<p>Alternative dispute resolution including arbitration and mediation '
            'to achieve efficient, cost-effective settlements outside court.</p>'
        ),
        'icon': 'fas fa-handshake',
        'display_order': 4,
    },
    {
        'title': 'Employment Law',
        'slug': 'employment-law',
        'description': (
            '<p>Advisory and litigation support on employment contracts, workplace '
            'disputes, termination, and compliance with Kenyan labour legislation.</p>'
        ),
        'icon': 'fas fa-briefcase',
        'display_order': 5,
    },
    {
        'title': 'Mergers, Acquisitions & Joint Ventures',
        'slug': 'mergers-acquisitions-joint-ventures',
        'description': (
            '<p>Structuring and documenting mergers, acquisitions, and joint venture '
            'arrangements for corporates and growing businesses.</p>'
        ),
        'icon': 'fas fa-building',
        'display_order': 6,
    },
    {
        'title': 'Bank Securities',
        'slug': 'bank-securities',
        'description': (
            '<p>Legal services relating to banking security instruments, charges, '
            'guarantees, and enforcement of secured lending transactions.</p>'
        ),
        'icon': 'fas fa-university',
        'display_order': 7,
    },
    {
        'title': 'Company Law & Business Registration',
        'slug': 'company-law',
        'description': (
            '<p>Company incorporation, business registration, corporate governance, '
            'and ongoing compliance for enterprises in Kenya.</p>'
        ),
        'icon': 'fas fa-file-signature',
        'display_order': 8,
    },
    {
        'title': 'Family Law, Wills & Estates',
        'slug': 'family-law-wills-estates',
        'description': (
            '<p>Compassionate guidance on family matters, wills, probate, letters of '
            'administration, and estate distribution under Kenyan law.</p>'
        ),
        'icon': 'fas fa-users',
        'display_order': 9,
    },
    {
        'title': 'Insurance Law (Running Down)',
        'slug': 'insurance-law-running-down',
        'description': (
            '<p>Representation in motor accident and running-down claims, insurance '
            'disputes, and recovery of compensation from insurers.</p>'
        ),
        'icon': 'fas fa-car-crash',
        'display_order': 10,
    },
]

TEAM_DEFINITIONS = [
    {
        'name': 'Ochieng Erick Daniel',
        'slug': 'ochieng-erick-daniel',
        'position': 'Principal Partner',
        'practice_number': 'P.105/16021/19',
        'phone': '0729 090 411 / 0734 090 411',
        'bio': (
            '<p>Ochieng Erick Daniel is the Principal Partner of Dan Ochieng &amp; Company '
            'Advocates, leading the firm\'s commercial, civil litigation, and consultancy '
            'practice from Kisumu with a secondary office in Kwale County.</p>'
        ),
        'email': FIRM_EMAIL,
        'display_order': 1,
        'is_active': True,
        'photo_url': TEAM_PHOTOS[0],
    },
    {
        'name': 'Otieno Rodgers Asembo',
        'slug': 'otieno-rodgers-asembo',
        'position': 'Senior Associate',
        'practice_number': 'P.105/23023/23',
        'phone': '0729 661 891',
        'bio': (
            '<p>Otieno Rodgers Asembo is a Senior Associate advising clients on civil '
            'litigation, land matters, and dispute resolution with practical courtroom '
            'experience across Western Kenya.</p>'
        ),
        'email': FIRM_EMAIL,
        'display_order': 2,
        'is_active': True,
        'photo_url': TEAM_PHOTOS[1],
    },
    {
        'name': 'Doris Kerubo Ondicho',
        'slug': 'doris-kerubo-ondicho',
        'position': 'Associate',
        'practice_number': 'P.105/23280/25',
        'phone': '0743 338 685',
        'bio': (
            '<p>Doris Kerubo Ondicho is an Associate supporting the firm\'s conveyancing, '
            'family law, and general advisory work for individuals and organisations.</p>'
        ),
        'email': FIRM_EMAIL,
        'display_order': 3,
        'is_active': True,
        'photo_url': TEAM_PHOTOS[2],
    },
    {
        'name': 'Stephanie Olwe',
        'slug': 'stephanie-olwe',
        'position': 'Office Secretary',
        'bio': (
            '<p>Stephanie Olwe manages front-office operations, client reception, and '
            'administrative coordination at the firm\'s Kisumu office.</p>'
        ),
        'email': FIRM_EMAIL,
        'display_order': 4,
        'is_active': True,
        'photo_url': TEAM_PHOTOS[3],
    },
    {
        'name': 'James Lumumba',
        'slug': 'james-lumumba',
        'position': 'Legal Assistant',
        'bio': (
            '<p>James Lumumba supports advocates with legal research, document preparation, '
            'and case file management across the firm\'s practice areas.</p>'
        ),
        'email': FIRM_EMAIL,
        'display_order': 5,
        'is_active': True,
        'photo_url': TEAM_PHOTOS[0],
    },
    {
        'name': 'Jane Juma',
        'slug': 'jane-juma',
        'position': 'Office Clerk',
        'bio': (
            '<p>Jane Juma provides clerical support, filing, and day-to-day office '
            'administration to keep client matters moving efficiently.</p>'
        ),
        'email': FIRM_EMAIL,
        'display_order': 6,
        'is_active': True,
        'photo_url': TEAM_PHOTOS[1],
    },
    {
        'name': 'Elizabeth Yonna Adhiambo',
        'slug': 'elizabeth-yonna-adhiambo',
        'position': 'Student (pupillage)',
        'bio': (
            '<p>Elizabeth Yonna Adhiambo is undertaking pupillage with the firm, '
            'gaining practical experience in advocacy, research, and client service.</p>'
        ),
        'email': FIRM_EMAIL,
        'display_order': 7,
        'is_active': True,
        'photo_url': TEAM_PHOTOS[2],
    },
]


def _upsert_service(data):
    service = Service.query.filter_by(slug=data['slug']).first()
    if not service:
        service = Service(slug=data['slug'])
        db.session.add(service)
    for key, value in data.items():
        setattr(service, key, value)
    service.is_active = True
    return service


def _upsert_team_member(data):
    member = TeamMember.query.filter_by(slug=data['slug']).first()
    if not member:
        member = TeamMember(slug=data['slug'])
        db.session.add(member)
    for key, value in data.items():
        setattr(member, key, value)
    return member


def _upsert_case_study(data):
    case = CaseStudy.query.filter_by(slug=data['slug']).first()
    if not case:
        case = CaseStudy(slug=data['slug'])
        db.session.add(case)
    for key, value in data.items():
        setattr(case, key, value)
    return case


def _upsert_blog_post(data):
    post = BlogPost.query.filter_by(slug=data['slug']).first()
    if not post:
        post = BlogPost(slug=data['slug'])
        db.session.add(post)
    for key, value in data.items():
        setattr(post, key, value)
    return post


def _seed_services():
    active_slugs = set()
    for data in SERVICE_DEFINITIONS:
        _upsert_service(data)
        active_slugs.add(data['slug'])
    Service.query.filter(~Service.slug.in_(active_slugs)).update(
        {'is_active': False}, synchronize_session=False
    )
    db.session.commit()


def _service_id(*slugs):
    for slug in slugs:
        service = Service.query.filter_by(slug=slug).first()
        if service:
            return service.id
    return None


def _seed_team_members():
    active_slugs = set()
    for data in TEAM_DEFINITIONS:
        _upsert_team_member(data)
        active_slugs.add(data['slug'])
    TeamMember.query.filter(~TeamMember.slug.in_(active_slugs)).update(
        {'is_active': False}, synchronize_session=False
    )
    db.session.commit()


def _seed_case_studies():
    cases = [
        {
            'title': 'Commercial Lease Negotiation for Retail Operator',
            'slug': 'commercial-lease-negotiation',
            'client': 'Star Hospital Kisumu Annex Limited',
            'summary': (
                'Negotiated favourable lease terms for a healthcare client establishing '
                'operations in Kisumu.'
            ),
            'challenge': (
                'The proposed lease contained onerous rent escalation clauses, broad '
                'indemnities, and restrictive assignment provisions.'
            ),
            'solution': (
                'Our team conducted a clause-by-clause review, benchmarked terms against '
                'local commercial practice, and negotiated directly with the landlord\'s counsel.'
            ),
            'outcome': (
                'The client secured capped annual increases, limited personal guarantees, '
                'and a right of first refusal on adjacent premises.'
            ),
            'service_id': _service_id('conveyances-property', 'company-law'),
            'featured': True,
            'is_active': True,
        },
        {
            'title': 'Land Dispute Resolution in Nyanza',
            'slug': 'land-dispute-resolution',
            'client': 'Rusinga Humanist Of Hope Centre',
            'summary': (
                'Resolved a protracted boundary dispute over community-held land near Kisumu.'
            ),
            'challenge': (
                'Overlapping survey maps, informal transfers, and competing claims under '
                'customary and statutory title complicated ownership.'
            ),
            'solution': (
                'We commissioned an independent survey, traced historical title documents, '
                'and pursued mediated settlement before escalating to the Environment and '
                'Land Court.'
            ),
            'outcome': (
                'Parties reached a binding settlement with a corrected boundary plan '
                'registered at the lands office, avoiding costly trial.'
            ),
            'service_id': _service_id('land-matters', 'conveyances-property'),
            'featured': True,
            'is_active': True,
        },
        {
            'title': 'Family Succession and Estate Administration',
            'slug': 'family-succession-matter',
            'client': 'Confidential — Kisumu Family',
            'summary': (
                'Guided beneficiaries through intestate succession and distribution of '
                'a mixed estate comprising urban property and agricultural land.'
            ),
            'challenge': (
                'The deceased left no will, multiple dependants, and disputed shares '
                'among adult children and a surviving spouse.'
            ),
            'solution': (
                'We obtained letters of administration, prepared a comprehensive inventory, '
                'and facilitated family conferences aligned with the Law of Succession Act.'
            ),
            'outcome': (
                'The estate was distributed by consent, titles were transferred cleanly, '
                'and family relationships were preserved.'
            ),
            'service_id': _service_id('family-law-wills-estates'),
            'featured': True,
            'is_active': True,
        },
        {
            'title': 'Insurance Running-Down Claim',
            'slug': 'insurance-running-down-claim',
            'client': 'Maxcure Insurance Agency',
            'summary': (
                'Secured compensation for a client injured in a road traffic accident '
                'on the Kisumu–Nairobi highway.'
            ),
            'challenge': (
                'The insurer disputed liability and argued contributory negligence, '
                'delaying medical assessment and settlement.'
            ),
            'solution': (
                'We assembled medical evidence, instructed an accident reconstruction '
                'expert, and issued a formal demand under the Insurance Act.'
            ),
            'outcome': (
                'The insurer settled the claim in full, covering medical costs, loss of '
                'earnings, and general damages without protracted litigation.'
            ),
            'service_id': _service_id('insurance-law-running-down', 'civil-litigation'),
            'featured': True,
            'is_active': True,
        },
    ]
    for data in cases:
        _upsert_case_study(data)
    db.session.commit()


def _seed_blog_posts():
    author = User.query.filter_by(is_admin=True).first()
    author_id = author.id if author else None
    posts = [
        {
            'title': 'Welcome to Our New Website',
            'slug': 'welcome-new-website',
            'summary': (
                'Dan Ochieng & Company Advocates launches an updated online presence '
                'to serve clients across Kisumu, Kwale County, and Western Kenya.'
            ),
            'content': (
                '<p>We are pleased to unveil our new website for Dan Ochieng &amp; Company '
                'Advocates — a premier full-service firm established in December 2023, '
                'building on the legacy of M/s Ochieng &amp; Associates Advocates.</p>'
                '<p>Whether you need advice on commercial law, civil litigation, land matters, '
                'or legal research and consultancy, our team is ready to assist. Browse our '
                'services, read our insights, or contact us today.</p>'
            ),
            'author_id': author_id,
            'is_published': True,
            'published_at': datetime(2026, 7, 1, 9, 0, 0),
        },
        {
            'title': 'Understanding Land Law in Kenya',
            'slug': 'understanding-land-law-kenya',
            'summary': (
                'A practical overview of title registration, adverse possession, and '
                'common pitfalls when buying or inheriting land in Kenya.'
            ),
            'content': (
                '<p>Land remains one of the most valuable — and contested — assets in Kenya. '
                'Before purchasing or inheriting property, verify the title at the relevant '
                'lands registry and confirm boundary beacons with a licensed surveyor.</p>'
                '<p>Disputes often arise from duplicate allocations, unregistered transfers, '
                'or failure to update ownership after succession. Early legal review can '
                'prevent costly litigation.</p>'
            ),
            'author_id': author_id,
            'is_published': True,
            'published_at': datetime(2026, 6, 20, 10, 0, 0),
        },
        {
            'title': 'When to Consult a Commercial Lawyer',
            'slug': 'when-to-consult-commercial-lawyer',
            'summary': (
                'Key moments in a business lifecycle when professional legal advice '
                'protects your interests and reduces risk.'
            ),
            'content': (
                '<p>Engage a commercial lawyer before signing leases, shareholder agreements, '
                'or supply contracts — not after a dispute arises.</p>'
                '<p>Regular legal health checks help Kisumu and Kwale businesses comply with '
                'tax, employment, and regulatory obligations while supporting sustainable growth.</p>'
            ),
            'author_id': author_id,
            'is_published': True,
            'published_at': datetime(2026, 6, 10, 11, 0, 0),
        },
        {
            'title': 'Family Law: Protecting Your Estate',
            'slug': 'family-law-protecting-your-estate',
            'summary': (
                'How wills, trusts, and succession planning safeguard your family\'s '
                'future under Kenyan law.'
            ),
            'content': (
                '<p>A valid will clarifies your wishes and reduces uncertainty for dependants. '
                'Without one, the Law of Succession Act determines how your estate is shared.</p>'
                '<p>We advise clients on wills, letters of administration, and matrimonial '
                'property agreements to protect children, spouses, and family businesses.</p>'
            ),
            'author_id': author_id,
            'is_published': True,
            'published_at': datetime(2026, 5, 28, 14, 0, 0),
        },
    ]
    for data in posts:
        _upsert_blog_post(data)
    db.session.commit()


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

            _seed_services()
            _seed_team_members()
            _seed_case_studies()
            _seed_blog_posts()

            team_count = TeamMember.query.filter_by(is_active=True).count()
            case_count = CaseStudy.query.filter_by(is_active=True, featured=True).count()
            blog_count = BlogPost.query.filter_by(is_published=True).count()
            service_count = Service.query.filter_by(is_active=True).count()
            click.echo('Demo content seeded successfully.')
            click.echo(f'  Practice areas (active): {service_count}')
            click.echo(f'  Team members (active): {team_count}')
            click.echo(f'  Featured case studies: {case_count}')
            click.echo(f'  Published blog posts: {blog_count}')

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
