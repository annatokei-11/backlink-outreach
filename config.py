import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://localhost/backlink_outreach')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GMAIL_SENDER_EMAIL = os.environ.get('GMAIL_SENDER_EMAIL', 'anna@writeitgreat.com')
    GMAIL_CREDENTIALS_FILE = os.environ.get('GMAIL_CREDENTIALS_FILE', 'credentials.json')
    GMAIL_TOKEN_FILE = os.environ.get('GMAIL_TOKEN_FILE', 'token.json')

    # Email finder API keys
    KENDO_API_KEY = os.environ.get('KENDO_API_KEY', '')
    SALESQL_API_KEY = os.environ.get('SALESQL_API_KEY', '')
    APOLLO_API_KEY = os.environ.get('APOLLO_API_KEY', '')
    ANYMAIL_API_KEY = os.environ.get('ANYMAIL_API_KEY', '')
    SNOV_CLIENT_ID = os.environ.get('SNOV_CLIENT_ID', '')
    SNOV_CLIENT_SECRET = os.environ.get('SNOV_CLIENT_SECRET', '')
    ROCKETREACH_API_KEY = os.environ.get('ROCKETREACH_API_KEY', '')
    SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

    # Fix Heroku's postgres:// -> postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
