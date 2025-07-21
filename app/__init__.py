from flask import Flask
from config import Config
from .extensions import db, migrate, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .routes.auth import bp as auth_bp
    from .routes.department import bp as dept_bp
    from .routes.project import bp as proj_bp
    from .routes.task import bp as task_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dept_bp, url_prefix='/departments')
    app.register_blueprint(proj_bp, url_prefix='/projects')
    app.register_blueprint(task_bp, url_prefix='/tasks')

    return app