from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms.project_forms import ProjectForm
from app.models import Project, Department, Task
from app.extensions import db
from app.utils.access_control import role_required

bp = Blueprint('project', __name__)

@bp.route('/')
@login_required
def list_projects():
    projects = Project.query.join(Department).add_columns(Project.id, Project.name, Department.name.label('department_name')).all()
    return render_template('project/list.html', projects=projects, title='Projects')

@bp.route('/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project.id).all()
    return render_template('project/detail.html', project=project, tasks=tasks)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(50)
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        proj = Project(
            name=form.name.data, 
            creator_id=current_user.id, 
            department_id=form.department_id.data, 
            description=form.description.data
        )
        db.session.add(proj)
        db.session.commit()
        flash('Project created successfully.', 'success')
        return redirect(url_for('project.list_projects'))
    return render_template('project/create.html', form=form, title='Create project')

@bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(50)
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        project.name = form.name.data
        project.department_id = form.department_id.data
        project.description = form.description.data
        db.session.commit()
        flash('Project updated successfully.', 'success')
        return redirect(url_for('project.list_projects'))
    return render_template('project/edit.html', form=form, project=project, title='Edit Project')

@bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
@role_required(50)
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully', 'success')
    return redirect(url_for('project.list_projects'))