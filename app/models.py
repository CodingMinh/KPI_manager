from datetime import datetime
from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager

task_assignments = db.Table(
    'task_assignments',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('workload_percent', db.Integer)
)

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('departments.id', name='fk_departments_parent_id'))
    children = db.relationship('Department', backref='parent', remote_side=[id])
    projects = db.relationship('Project', back_populates='department', lazy='dynamic')

    def __repr__(self):
        return f"<Department {self.name}>"

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    level = db.Column(db.Integer, nullable=False)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    assignments = db.relationship('UserAssignment', back_populates='user')

    def __repr__(self):
        return f"<User {self.email}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def max_role_level(self):
        levels = [assignment.role.level for assignment in self.assignments]
        return max(levels) if levels else 0
    
@login_manager.user_loader
def load_user(id): # id passed in here is string so we want to convert back to int for our database
    return db.session.get(User, int(id))

class UserAssignment(db.Model):
    __tablename__ = 'user_assignments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)

    user = db.relationship('User', back_populates='assignments')
    role = db.relationship('Role')
    department = db.relationship('Department')

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    description = db.Column(db.Text)
    
    creator = db.relationship('User', backref='created_projects')
    department = db.relationship('Department', back_populates='projects')

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    submitted = db.Column(db.Boolean, default=False)

    project = db.relationship('Project', backref='tasks')
    creator = db.relationship('User', foreign_keys=[created_by])
    manager = db.relationship('User', foreign_keys=[manager_id])
    assignees = db.relationship('User', secondary=task_assignments, backref='assigned_tasks')

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    evaluated_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer)
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship('Task')
    evaluator = db.relationship('User', foreign_keys=[evaluator_id])
    evaluated_user = db.relationship('User', foreign_keys=[evaluated_user_id])
    
    # force score to only be between 0 and 100
    __table_args__ = (
        db.CheckConstraint('score >= 0 AND score <= 100', name='check_score_range'),
    )

class AccessRequest(db.Model):
    __tablename__ = 'access_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    decision_timestamp = db.Column(db.DateTime)
    decided_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='access_requests')
    reviewer = db.relationship('User', foreign_keys=[decided_by])