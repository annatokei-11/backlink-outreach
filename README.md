# Backlink Outreach Campaign Manager

A Flask web application for managing backlink outreach campaigns for **Write it Great**. Track platforms, targets, compose and send outreach emails via the Gmail API, and monitor campaign progress through a dashboard.

## Features

- **Platform Management** — Track websites/blogs you want backlinks from, including domain authority and contact info
- **Target Tracking** — Manage specific pages/URLs to target for backlinks with status workflow (identified → contacted → negotiating → approved → live)
- **Campaign Organization** — Group outreach efforts into campaigns
- **Email Outreach** — Compose and send HTML emails directly via Gmail API from anna@writeitgreat.com
- **Dashboard** — Overview of all outreach activity with status breakdowns

## Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF
- **Database:** PostgreSQL
- **Email:** Gmail API (OAuth2)
- **Frontend:** Bootstrap 5, Bootstrap Icons
- **Deployment:** Heroku (Gunicorn)

## Local Setup

```bash
# Clone and install
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Create the database
createdb backlink_outreach

# Run migrations
flask db upgrade

# Start the dev server
FLASK_CONFIG=development flask run
```

## Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **Gmail API**
3. Create OAuth 2.0 credentials (Desktop application)
4. Download the credentials as `credentials.json` in the project root
5. On first email send, you'll be prompted to authorize — this creates `token.json`

## Heroku Deployment

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:essential-0

# Set config vars
heroku config:set FLASK_CONFIG=production
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set GMAIL_SENDER_EMAIL=anna@writeitgreat.com

# Deploy
git push heroku main

# Migrations run automatically via the release phase (Procfile)
```

## Project Structure

```
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models
│   ├── routes.py            # All route handlers
│   ├── forms.py             # WTForms form classes
│   ├── services/
│   │   └── gmail_service.py # Gmail API integration
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── platforms/
│   │   ├── targets/
│   │   ├── campaigns/
│   │   └── emails/
│   └── static/css/style.css
├── migrations/              # Alembic migrations
├── config.py                # Configuration classes
├── wsgi.py                  # WSGI entry point
├── Procfile                 # Heroku process config
├── runtime.txt              # Python version for Heroku
└── requirements.txt
```
