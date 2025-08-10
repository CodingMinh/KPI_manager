from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms.task_forms import TaskForm, TaskReviewForm
from app.models import Task, Project, User, Role, TaskReview
from app.extensions import db
from app.utils.access_control import role_required
from app.utils.email import send_email
from datetime import datetime, timezone

bp = Blueprint('task', __name__)

@bp.route('/')
@login_required
def list_tasks():
    tasks = Task.query.order_by(Task.start_date.desc()).all()
    return render_template('task/list.html', tasks=tasks, title='Tasks')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(60)
def create_task():
    form = TaskForm()
    projects = Project.query.order_by(Project.name).all()
    managers = (
        User.query
        .join(User.assignments)
        .join(Role)
        .filter(Role.level >= 60)
        .distinct()
        .order_by(User.name)
        .all()
    )
    users = User.query.order_by(User.name).all()

    form.project_id.choices = [(p.id, p.name) for p in projects]
    form.manager_id.choices = [(m.id, m.name) for m in managers]
    form.assignees.choices = [(u.id, u.name) for u in users]

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
            u = User.query.get(uid)
            if u:
                task.assignees.append(u)

        db.session.add(task)
        db.session.commit()
        flash('Task created successfully.', 'success')
        return redirect(url_for('task.list_tasks'))
    elif request.method == 'POST':
        flash('Please fill out all required fields before submitting.', 'danger')

    return render_template('task/create.html', form=form, projects=projects, managers=managers, users=users, title='Create task')

@bp.route('/<int:task_id>')
@login_required
def detail(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('task/detail.html', task=task)

@bp.route('/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_submission(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user not in task.assignees:
        flash('Only assignees can mark this task done.', 'danger')
        return redirect(url_for('task.detail', task_id=task.id))

    task.submitted = not task.submitted
    db.session.commit()

    if task.submitted and task.manager and task.manager.email:
        text = render_template('email/task_completed.txt', task=task, user=current_user)
        html = render_template('email/task_completed.html', task=task, user=current_user)
        send_email(
            subject=f"Task submitted: {task.name}",
            sender=current_user.email,
            recipients=[task.manager.email],
            text_body=text,
            html_body=html
        )
    flash('Task status updated.', 'success')
    return redirect(url_for('task.detail', task_id=task.id))

@bp.route('/<int:task_id>/review', methods=['GET', 'POST'])
@login_required
@role_required(60)
def review(task_id):
    task = Task.query.get_or_404(task_id)
    form = TaskReviewForm()
    if form.validate_on_submit():
        review = TaskReview(task_id=task.id, reviewer_id=current_user.id, score=form.score.data, comments=form.comments.data, timestamp=datetime.now(timezone.utc))
        db.session.add(review)
        db.session.commit()

        assignee_emails = [u.email for u in task.assignees if u.email]
        if assignee_emails:
            text = render_template('email/task_reviewed.txt', task=task, review=review)
            html = render_template('email/task_reviewed.html', task=task, review=review)
            send_email(
                subject=f"Task reviewed: {task.name}",
                sender=current_user.email,
                recipients=assignee_emails,
                text_body=text,
                html_body=html
            )

        flash('Review submitted and assignees notified.', 'success')
        return redirect(url_for('task.detail', task_id=task.id))

    return render_template('task/review.html', task=task, form=form)

@bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(60)
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    form = TaskForm()

    projects = Project.query.order_by(Project.name).all()
    users = User.query.order_by(User.name).all()
    form.project_id.choices = [(p.id, p.name) for p in projects]
    form.manager_id.choices = [(u.id, u.name) for u in users]
    form.assignees.choices = [(u.id, u.name) for u in users]

    if form.validate_on_submit():
        task.name = form.name.data
        task.description = form.description.data
        task.project_id = form.project_id.data
        task.manager_id = form.manager_id.data
        task.start_date = form.start_date.data
        task.end_date = form.end_date.data

        selected_ids = form.assignees.data or []
        if selected_ids:
            selected_users = User.query.filter(User.id.in_(selected_ids)).all()
        else:
            selected_users = []
        task.assignees = selected_users

        db.session.commit()
        flash('Task updated successfully.', 'success')
        return redirect(url_for('task.list_tasks'))

    if request.method == 'GET':
        form.name.data = task.name
        form.description.data = task.description
        form.project_id.data = task.project_id
        form.manager_id.data = task.manager_id
        form.assignees.data = [u.id for u in task.assignees]
        form.start_date.data = task.start_date
        form.end_date.data = task.end_date

    return render_template('task/edit.html', form=form, task=task)

@bp.route('/<int:task_id>/delete', methods=['POST', 'GET'])
@login_required
@role_required(60)
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('task.list_tasks'))