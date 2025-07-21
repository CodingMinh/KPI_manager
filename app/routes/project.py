from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Project
from ..extensions import db
from app.utils.access_control import role_required

bp = Blueprint('project', __name__)

@bp.route('/')
@login_required
def list_projects():
    projects = Project.query.all()
    return render_template('project/list.html', projects=projects)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(50)
def create_project():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            project = Project(name=name, creator_id=current_user.id)
            db.session.add(project)
            db.session.commit()
            flash('Project created successfully.', 'success')
            return redirect(url_for('project.list_projects'))
        flash('Project name is required.', 'danger')
    return render_template('project/create.html')