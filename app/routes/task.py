from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms.task_forms import TaskForm
from app.models import Task, Project, User
from app.extensions import db
from app.utils.access_control import role_required

bp = Blueprint('task', __name__)

@bp.route('/')
@login_required
def list_tasks():
    tasks = Task.query.all()
    return render_template('task/list.html', tasks=tasks, title='Tasks')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(50)
def create_task():
    form = TaskForm()
    # populate choices
    form.project_id.choices = [(p.id, p.name) for p in Project.query.all()]
    form.manager_id.choices = [(u.id, u.name) for u in User.query.all()]
    form.assignees.choices = [(u.id, u.name) for u in User.query.all()]

    if form.validate_on_submit():
        task = Task(
            name=form.name.data,
            description=form.description.data,
            project_id=form.project_id.data,
            created_by=current_user.id,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            manager_id=form.manager_id.data
        )
        for uid in form.assignees.data:
            user = User.query.get(uid)
            if user:
                task.assignees.append(user)
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully.', 'success')
        return redirect(url_for('task.list_tasks'))
    return render_template('task/create.html', form=form, title='Create task')