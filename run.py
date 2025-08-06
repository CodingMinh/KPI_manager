from app import create_app, db
from app.models import Department, Role, User, UserAssignment, Project, Task, Evaluation, AccessRequest

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Department': Department, 'Role': Role, 'User': User, 'UserAssignment': UserAssignment,
            'Project': Project, 'Task': Task, 'Evaluation': Evaluation, 'AccessRequest': AccessRequest}