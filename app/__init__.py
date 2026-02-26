from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    import os
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)

    from config import config as config_dict
    app.config.from_object(config_dict[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Ensure app_settings table exists (safe even if it already does)
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'app_settings' not in inspector.get_table_names():
            from app.models import AppSetting
            AppSetting.__table__.create(db.engine)

    return app
