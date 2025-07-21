from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from ..models import Department
from ..forms import DepartmentForm
from ..extensions import db

bp = Blueprint('department', __name__)

@bp.route('/')
@login_required
def list_departments():
    departments = Department.query.all()
    return render_template('department/list.html', departments=departments)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(name=form.name.data, parent_id=form.parent_id.data or None)
        db.session.add(department)
        db.session.commit()
        flash('Department created successfully.', 'success')
        return redirect(url_for('department.list_departments'))
    return render_template('department/create.html', form=form)