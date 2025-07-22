from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.forms.department_forms import DepartmentForm
from app.models import Department
from app.extensions import db
from app.utils.access_control import role_required

bp = Blueprint('department', __name__)

@bp.route('/')
@login_required
def list_departments():
    departments = Department.query.all()
    return render_template('department/list.html', departments=departments)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(60)
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        dept = Department(name=form.name.data, parent_id=form.parent_id.data or None)
        db.session.add(dept)
        db.session.commit()
        flash('Department created successfully.', 'success')
        return redirect(url_for('department.list_departments'))
    return render_template('department/create.html', form=form)