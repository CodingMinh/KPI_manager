from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.forms.user_forms import (
    UserRoleAssignForm,
    UserAssignmentEditForm,
    EditUserForm
)
from app.models import User, UserAssignment, Department, Role
from app.extensions import db

bp = Blueprint('user', __name__)

@bp.route('/')
@login_required
def list_users():
    # Departments this user manages (role >= 60)
    managed_depts = [a.department_id for a in current_user.assignments if a.role.level >= 60]
    if not managed_depts and current_user.max_role_level < 80:
        flash("You do not manage any departments.", "warning")
        return redirect(url_for('home.dashboard'))

    dept_id = request.args.get('department', type=int)
    query = User.query.join(User.assignments)

    # Restrict for managers
    if current_user.max_role_level < 80:
        query = query.filter(UserAssignment.department_id.in_(managed_depts))
    if dept_id:
        query = query.filter(UserAssignment.department_id == dept_id)

    query = query.distinct()
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=20)

    return render_template(
        'user/list.html',
        pagination=pagination,
        departments=Department.query.filter(Department.id.in_(managed_depts)).all(),
        title='Users'
    )

@bp.route('/assign', methods=['GET', 'POST'])
@login_required
def assign_role():
    form = UserRoleAssignForm()
    # Limit departments for non-admins
    if current_user.max_role_level < 80:
        allowed = [a.department_id for a in current_user.assignments if a.role.level >= 60]
        form.department_id.choices = [
            (d.id, d.name) for d in Department.query.filter(Department.id.in_(allowed)).all()
        ]

    if form.validate_on_submit():
        ua = UserAssignment.query.filter_by(
            user_id=form.user_id.data,
            department_id=form.department_id.data
        ).first()
        if ua:
            ua.role_id = form.role_id.data
        else:
            ua = UserAssignment(
                user_id=form.user_id.data,
                department_id=form.department_id.data,
                role_id=form.role_id.data
            )
            db.session.add(ua)
        db.session.commit()
        flash("Role assignment updated.", "success")
        return redirect(url_for('user.list_users'))

    return render_template('user/assign_user_roles.html', form=form, title='Assign role to user')

@bp.route('/manage-roles', methods=['GET', 'POST'])
@login_required
def manage_roles():
    # Admins see all; managers only their depts
    if current_user.max_role_level < 80:
        allowed = [a.department_id for a in current_user.assignments if a.role.level >= 60]
        assignments = UserAssignment.query.filter(
            UserAssignment.department_id.in_(allowed)
        ).all()
    else:
        assignments = UserAssignment.query.all()

    forms = []
    for ua in assignments:
        form = UserAssignmentEditForm(obj=ua)
        form.assignment_id.data = ua.id
        forms.append((ua, form))

    if request.method == 'POST':
        for ua, form in forms:
            if form.validate_on_submit() and int(form.assignment_id.data) == ua.id:
                ua.role_id = form.role_id.data
        db.session.commit()
        flash("Roles updated successfully.", "success")
        return redirect(url_for('user.manage_roles'))

    return render_template('user/manage_user_roles.html', forms=forms, title='Manage user roles')

@bp.route('/delete-assignment/<int:assignment_id>', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    ua = UserAssignment.query.get_or_404(assignment_id)
    if current_user.max_role_level < 80:
        allowed = [a.department_id for a in current_user.assignments if a.role.level >= 60]
        if ua.department_id not in allowed:
            abort(403)
    db.session.delete(ua)
    db.session.commit()
    flash("Assignment deleted.", "success")
    return redirect(url_for('user.manage_roles'))

@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    managed_depts = [a.department_id for a in current_user.assignments if a.role.level >= 60]
    if current_user.max_role_level < 80:
        user_depts = [a.department_id for a in user.assignments]
        if not any(d in managed_depts for d in user_depts):
            abort(403)

    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for('user.list_users'))

    return render_template('user/edit.html', form=form, user=user, title='Edit user role')

@bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    managed_depts = [a.department_id for a in current_user.assignments if a.role.level >= 60]
    if current_user.max_role_level < 80:
        user_depts = [a.department_id for a in user.assignments]
        if not any(d in managed_depts for d in user_depts):
            abort(403)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for('user.list_users'))