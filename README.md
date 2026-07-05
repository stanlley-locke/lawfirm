# Dan Ochieng & Company Advocates — Law Firm Website

Flask-based website and admin CMS for a Kisumu, Kenya law firm. Includes contact forms, live chat (SocketIO), blog, case studies, and admin content management.

## Requirements

- **Python 3.12** recommended (best prebuilt wheel support; 3.13+ may lack wheels for some packages)
- SQLite for local development (default), [SQLite Cloud](https://sqlitecloud.io) for production, or PostgreSQL
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

For SQLite Cloud production, set `USE_SQLITECLOUD=true` and `SQLITECLOUD_CONNECTION_STRING` (see [SQLite Cloud setup](#sqlite-cloud) below).

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

## SQLite Cloud

The app can use [SQLite Cloud](https://sqlitecloud.io) as a managed SQLite backend in production. Flask-SQLAlchemy connects via the native [`sqlitecloud`](https://pypi.org/project/sqlitecloud/) driver and the [`sqlalchemy-sqlitecloud`](https://pypi.org/project/sqlalchemy-sqlitecloud/) SQLAlchemy dialect (port 8860).

### 1. Create a SQLite Cloud project

1. Sign up at [sqlitecloud.io](https://sqlitecloud.io) and open your project dashboard.
2. Upload or create your database (e.g. `lawfirm.db`).
3. Copy the **connection string** from the dashboard (format: `sqlitecloud://host:8860/lawfirm.db?apikey=...`).

### 2. Configure environment

Add to `.env` (see `.env.example` for placeholders — **never commit real API keys**):

| Variable | Description |
|----------|-------------|
| `USE_SQLITECLOUD` | Set to `true` to use cloud DB instead of local `DATABASE_URL` |
| `SQLITECLOUD_API_KEY` | API key (`orgkey_...` or project key from dashboard) |
| `SQLITECLOUD_GATEWAY_URL` | Weblite gateway URL (e.g. `https://your-id.g1.gateway.sqlite.cloud`) |
| `SQLITECLOUD_DATABASE` | Database filename on the node (default: `lawfirm.db`) |
| `SQLITECLOUD_CONNECTION_STRING` | **Preferred:** full native connection string from the dashboard |
| `SQLITECLOUD_HOST` | Alternative: native hostname (`your-id.g1.sqlite.cloud`) with `SQLITECLOUD_APIKEY` |
| `SQLITECLOUD_APIKEY` | Alternative API key alias (same as `SQLITECLOUD_API_KEY`) |

Cloud mode activates when `USE_SQLITECLOUD=true` or a connection string is set. The app derives the native host from `SQLITECLOUD_GATEWAY_URL` by replacing `.gateway.` with `.` (e.g. `caxawolbdz.g1.gateway.sqlite.cloud` → `caxawolbdz.g1.sqlite.cloud`). Leave cloud vars unset for local SQLite development.

**Security:** If an API key is ever exposed in git, chat, or logs, rotate it immediately in the [SQLite Cloud dashboard](https://dashboard.sqlitecloud.io).

### 3. Install cloud dependencies

Both packages are included in `requirements.txt`:

```bash
pip install sqlitecloud sqlalchemy-sqlitecloud
# or install everything:
pip install -r requirements.txt
```

Or install the optional extra:

```bash
pip install -e ".[sqlitecloud]"
```

### 4. Test the connection

```bash
# Enable cloud mode in .env first: USE_SQLITECLOUD=true
flask test-sqlitecloud
```

This verifies the Weblite REST API (optional), native `sqlitecloud` driver, SQLAlchemy engine, and Flask-SQLAlchemy models.

If Weblite REST returns `401`, use the **project connection string** from the dashboard (`SQLITECLOUD_CONNECTION_STRING`) — the native driver on port 8860 is what Flask-SQLAlchemy uses.

You can also test directly in Python:

```python
import sqlitecloud
conn = sqlitecloud.connect("sqlitecloud://host:8860/lawfirm.db?apikey=YOUR_KEY")
print(conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
```

### 5. Run in production

```bash
export FLASK_ENV=production
export USE_SQLITECLOUD=true
export SQLITECLOUD_CONNECTION_STRING="sqlitecloud://host:8860/lawfirm.db?apikey=..."
# ... other production secrets (SESSION_SECRET, ADMIN_PASSWORD, RESEND_API_KEY)

flask db upgrade
gunicorn -c gunicorn.conf.py wsgi:app
```

### Flask-Migrate notes

Flask-Migrate/Alembic works with SQLite Cloud because the `sqlalchemy-sqlitecloud` dialect extends the standard SQLite dialect. Keep in mind:

- The `sqlalchemy-sqlitecloud` integration is still marked **beta** upstream.
- SQLite Cloud is SQLite-compatible, but remote latency makes large migrations slower than local SQLite.
- Avoid concurrent `flask db upgrade` runs against the same cloud database.
- Some SQLite-specific DDL edge cases may behave differently over the network driver.

## Production

```bash
export FLASK_ENV=production
export SESSION_SECRET=...
export ADMIN_PASSWORD=...
export RESEND_API_KEY=...
# Option A: SQLite Cloud
export USE_SQLITECLOUD=true
export SQLITECLOUD_CONNECTION_STRING="sqlitecloud://host:8860/lawfirm.db?apikey=..."
# Option B: PostgreSQL
# export DATABASE_URL=postgresql://user:pass@host:5432/lawfirm

pip install -r requirements-postgres.txt   # or: pip install -e ".[postgres]"
flask db upgrade
gunicorn -c gunicorn.conf.py wsgi:app
```

Uses **gunicorn + eventlet** via `wsgi.py` (monkey-patch runs before Flask imports). Set `SESSION_COOKIE_SECURE=True` (default in production config) when serving over HTTPS.

### Deploy on Render

1. Connect the repo and use **Python 3.12** (`runtime.txt` pins `python-3.12.8`).
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app`
   - Alternative: `gunicorn -c gunicorn.conf.py wsgi:app`
4. Set environment variables (see checklist below).
5. Optional: use the included `render.yaml` Blueprint for one-click setup.

**Render environment variables (required in production):**

| Variable | Required | Notes |
|----------|----------|-------|
| `FLASK_ENV` | Yes | Set to `production` |
| `SESSION_SECRET` | Yes | Long random secret for session signing |
| `ADMIN_PASSWORD` | Yes | Bootstrap password for first admin user |
| `RESEND_API_KEY` | Yes | Resend transactional email API key |
| `BASE_URL` | Yes | Public site URL, e.g. `https://your-app.onrender.com` |
| `ALLOWED_ORIGINS` | Yes | Comma-separated CORS/SocketIO origins, e.g. `https://your-app.onrender.com` |
| `USE_SQLITECLOUD` | If using cloud DB | Set to `true` |
| `SQLITECLOUD_CONNECTION_STRING` | If using cloud DB | Full `sqlitecloud://...` connection string from dashboard |

**Optional:** `ADMIN_USERNAME`, `ADMIN_EMAIL`, `RESEND_FROM_EMAIL`, `ADMIN_NOTIFICATION_EMAIL`, `CALENDLY_URL`, `DATABASE_URL` (local SQLite fallback when cloud is disabled).

Do **not** use `gunicorn app:app` — that imports `app.py` before the eventlet monkey patch and breaks SocketIO/SQLAlchemy under eventlet workers.

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
├── wsgi.py             # Production WSGI entry (eventlet monkey_patch)
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
