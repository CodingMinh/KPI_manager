from datetime import datetime
from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager
from datetime import datetime, timezone

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
    
    def get_kpi_for_month(self, year: int, month: int):
        """Return the highest KPI score (int) for this user in given year/month, or None."""
        row = MonthlyKPI.query.filter_by(user_id=self.id, year=year, month=month).order_by(MonthlyKPI.score.desc()).first()
        return row.score if row else None
    
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

class TaskReview(db.Model):
    __tablename__ = 'task_reviews'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    task = db.relationship('Task', backref=db.backref('reviews', cascade='all, delete-orphan'))
    reviewer = db.relationship('User')

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

class MonthlyKPI(db.Model):
    __tablename__ = 'monthly_kpis'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)  # 0-100
    comments = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('monthly_kpis', cascade='all, delete-orphan'))
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])

    __table_args__ = (
        db.Index('ix_monthlykpi_user_year_month', 'user_id', 'year', 'month'),
    )