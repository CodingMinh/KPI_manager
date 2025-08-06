from .auth import bp as auth_bp
from .department import bp as department_bp
from .project import bp as project_bp
from .task import bp as task_bp
from .home import bp as home_bp
from .user import bp as user_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(department_bp, url_prefix='/departments')
    app.register_blueprint(project_bp, url_prefix='/projects')
    app.register_blueprint(task_bp, url_prefix='/tasks')
    app.register_blueprint(home_bp)
    app.register_blueprint(user_bp, url_prefix='/users')