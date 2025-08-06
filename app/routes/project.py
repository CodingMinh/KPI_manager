from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms.project_forms import ProjectForm
from app.models import Project
from app.extensions import db
from app.utils.access_control import role_required

bp = Blueprint('project', __name__)

@bp.route('/')
@login_required
def list_projects():
    projects = Project.query.all()
    return render_template('project/list.html', projects=projects, title='Projects')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(50)
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        proj = Project(name=form.name.data, creator_id=current_user.id, department_id=form.department_id.data)
        db.session.add(proj)
        db.session.commit()
        flash('Project created successfully.', 'success')
        return redirect(url_for('project.list_projects'))
    return render_template('project/create.html', form=form, title='Create project')