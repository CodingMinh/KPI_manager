from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Task, Project, User
from ..extensions import db
from app.utils.access_control import role_required

bp = Blueprint('task', __name__)

@bp.route('/')
@login_required
def list_tasks():
    tasks = Task.query.all()
    return render_template('task/list.html', tasks=tasks)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(50)
def create_task():
    projects = Project.query.all()
    users = User.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        project_id = request.form.get('project_id')
        assignee_ids = request.form.getlist('assignees')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        manager_id = request.form.get('manager_id')

        if name and project_id:
            task = Task(
                name=name,
                description=description,
                project_id=project_id,
                created_by=current_user.id,
                start_date=start_date,
                end_date=end_date,
                manager_id=manager_id
            )
            db.session.add(task)
            db.session.commit()

            for uid in assignee_ids:
                user = User.query.get(uid)
                if user:
                    task.assignees.append(user)

            db.session.commit()
            flash('Task created successfully.', 'success')
            return redirect(url_for('task.list_tasks'))

        flash('Task name and project are required.', 'danger')
    return render_template('task/create.html', projects=projects, users=users)