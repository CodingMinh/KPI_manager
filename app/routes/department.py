from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.forms.department_forms import DepartmentForm
from app.models import Department
from app.extensions import db
from app.utils.access_control import role_required

bp = Blueprint('department', __name__)

@bp.route('/')
@login_required
@role_required(70)
def list_departments():
    departments = Department.query.all()
    view = request.args.get('view', 'table')

    if view == 'tree':
        return render_template('department/tree.html', departments=departments, title='Departments')
    return render_template('department/list.html', departments=departments, title='Departments')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(70)
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        parent_id = form.parent_id.data
        if parent_id == -1:
            parent_id = None
        dept = Department(name=form.name.data, parent_id=parent_id)
        db.session.add(dept)
        db.session.commit()
        flash('Department created successfully.', 'success')
        return redirect(url_for('department.list_departments'))
    return render_template('department/create.html', form=form, title='Create department')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(70)
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        department.name = form.name.data
        department.parent_id = form.parent_id.data if form.parent_id.data != -1 else None
        db.session.commit()
        flash('Department updated successfully.', 'success')
        return redirect(url_for('department.list_departments'))
    return render_template('department/edit.html', form=form, department=department, title='Edit department')

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required(70)
def delete_department(id):
    department = Department.query.get_or_404(id)
    child_departments = Department.query.filter_by(parent_id=id).all()
    for child in child_departments:
        db.session.delete(child)
    db.session.delete(department)
    db.session.commit()
    flash('Department and its sub-departments deleted successfully.', 'success')
    return redirect(url_for('department.list_departments'))