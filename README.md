# Dan Ochieng & Company Advocates — Law Firm Website

Flask-based website and admin CMS for a Kisumu, Kenya law firm. Includes contact forms, live chat (SocketIO), blog, case studies, and admin content management.

## Requirements

- **Python 3.12** recommended (best prebuilt wheel support; 3.13+ may lack wheels for some packages)
- SQLite for local development (default) or PostgreSQL for production
- [Resend](https://resend.com) account for transactional email

## Quick Start

### 1. Clone and create virtual environment

```bash
cd lawfirm
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

**Development (SQLite)** — no PostgreSQL client or server required:

```bash
pip install -r requirements.txt
```

**Production (PostgreSQL)** — install the core dependencies first, then the PostgreSQL driver:

```bash
pip install -r requirements.txt
pip install -r requirements-postgres.txt
```

Or install the optional extra from the project root:

```bash
pip install -e ".[postgres]"
```

On Windows, `psycopg2-binary` needs a matching prebuilt wheel for your Python version. If `pip install -r requirements-postgres.txt` fails with `pg_config executable not found`, use **Python 3.12** or install PostgreSQL development tools.

Or with uv (dev, SQLite only by default):

```bash
uv sync
uv sync --extra postgres   # add PostgreSQL driver
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values. **Required in production:**

| Variable | Description |
|----------|-------------|
| `SESSION_SECRET` | Long random string for Flask sessions |
| `ADMIN_PASSWORD` | Password for the initial admin user |
| `RESEND_API_KEY` | Resend API key |
| `RESEND_FROM_EMAIL` | Verified sender in Resend |
| `ADMIN_NOTIFICATION_EMAIL` | Where contact/chat alerts are sent |
| `BASE_URL` | Public site URL (for sitemap, OG tags) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins for SocketIO |

Optional: `DATABASE_URL`, `CALENDLY_URL`, business hours settings — see `.env.example`.

### 4. Initialize database

```bash
set FLASK_APP=app.py          # Windows
export FLASK_APP=app.py       # macOS/Linux

flask db upgrade
flask seed-demo               # optional demo content
```

The first admin user is created automatically on startup if none exists (using `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` from `.env`).

### 5. Run development server

```bash
python app.py
```

Visit http://localhost:5000 — admin login at `/auth/login`.

## Resend Email Setup

1. Create an account at [resend.com](https://resend.com)
2. Add and verify your sending domain (or use `onboarding@resend.dev` for testing)
3. Create an API key and set `RESEND_API_KEY` in `.env`
4. Set `RESEND_FROM_EMAIL` to your verified sender
5. Set `ADMIN_NOTIFICATION_EMAIL` to receive contact form and chat alerts

Emails are sent asynchronously via the `resend` Python package (contact notifications, admin replies, chat alerts, transcript export).

## Production

```bash
export FLASK_ENV=production
export SESSION_SECRET=...
export ADMIN_PASSWORD=...
export RESEND_API_KEY=...
export DATABASE_URL=postgresql://user:pass@host:5432/lawfirm

pip install -r requirements-postgres.txt   # or: pip install -e ".[postgres]"
flask db upgrade
gunicorn -c gunicorn.conf.py "app:app"
```

Uses **gunicorn + eventlet** for SocketIO support. Set `SESSION_COOKIE_SECURE=True` (default in production config) when serving over HTTPS.

## Migrations

```bash
flask db migrate -m "description"   # generate migration after model changes
flask db upgrade                    # apply migrations
flask db downgrade                  # rollback one revision
```

## Testing

```bash
pytest
```

CI runs automatically via GitHub Actions (`.github/workflows/ci.yml`).

## Project Structure

```
lawfirm/
├── app.py              # Application factory & dev entry point
├── config.py           # Central configuration
├── models.py           # SQLAlchemy models
├── routes/             # Blueprints (auth, admin, main, contact, chat)
├── templates/          # Jinja2 templates
├── static/             # CSS, JS, uploads
├── docs/               # Design reference and project docs
├── utils/              # Email (Resend), sanitization, uploads, security
├── migrations/         # Alembic migrations
├── tests/              # pytest suite
└── gunicorn.conf.py    # Production WSGI config
```

## Design

The public site UI follows the **[Law Firm Figma Template (Community)](https://www.figma.com/design/hu42VvGOuHT4Jza6LVHEy4/Law-Firm-Figma-Template--Community-?node-id=1-1142)** — a professional law-firm kit with navy/gold palette, serif headings, and card-based sections.

- Design tokens and section mapping: [`docs/DESIGN.md`](docs/DESIGN.md)
- Stylesheet: `static/css/custom.css` (`--lf-*` CSS custom properties)
- Fonts: Playfair Display (headings) + Lato (body), loaded in `templates/layout.html`

The implementation uses a **hybrid dark theme** (navy surfaces, gold accents) to preserve admin panel, chat, and form behavior while aligning with typical law-firm template aesthetics.

## Admin Features

- Services, team, case studies, blog CRUD with TinyMCE + bleach sanitization
- Contact message inbox with read tracking and Resend reply
- Live chat with assignment, typing indicators, file upload, PDF/email export
- Admin user management at `/admin/users`
- Health check at `/health`

## Security Notes

- Backdoor auth routes removed (`/auth/token-access`, `/auth/secret`, contact-form login)
- Production startup validates required secrets
- CSRF protection on forms and admin fetch calls
- SocketIO room membership validated on join/message
- Security headers (CSP, X-Frame-Options, etc.) applied globally

## License

Private — Dan Ochieng & Company Advocates.
