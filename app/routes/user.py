from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.forms.user_forms import (
    UserRoleAssignForm,
    UserAssignmentEditForm,
    EditUserForm,
    DateRangeForm,
    MonthlyKPIForm
)
from app.models import User, UserAssignment, Department, Role, Task, MonthlyKPI
from app.extensions import db
from app.utils.access_control import role_required
from datetime import date, datetime, timezone
import calendar

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
    departments = Department.query.order_by(Department.name).all()
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
        #departments=Department.query.filter(Department.id.in_(managed_depts)).all(),
        departments=departments,
        title='Users',
        current_time=datetime.now(timezone.utc)
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

    roles = Role.query.order_by(Role.level).all()
    return render_template('user/manage_user_roles.html', forms=forms, title='Manage user roles', roles=roles)

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

@bp.route('/update-assignment/<int:assignment_id>', methods=['POST'])
@login_required
def update_assignment(assignment_id):
    assignment = UserAssignment.query.get_or_404(assignment_id)
    new_role_id = int(request.form.get('role_id'))
    assignment.role_id = new_role_id
    db.session.commit()
    flash("Role updated successfully.", "success")
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
        user.name = form.name.data
        user.email = form.email.data
        assignment = user.assignments[0] if user.assignments else None
        if assignment:
            assignment.department_id = form.department_id.data
            assignment.role_id = form.role_id.data
        db.session.commit()
        db.session.refresh(user)
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

# helper permission function
def _user_view_permission_or_403(target_user):
    # managers of departments they manage (role.level >= 60) or admins (>=80)
    if current_user.max_role_level >= 80:
        return True
    managed_departments = [a.department_id for a in current_user.assignments if a.role.level >= 60]
    target_depts = [a.department_id for a in target_user.assignments]
    if any(d in managed_departments for d in target_depts):
        return True
    abort(403)

@bp.route('/<int:user_id>/detail', methods=['GET', 'POST'])
@login_required
@role_required(60)
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    _user_view_permission_or_403(user)

    dr_form = DateRangeForm(request.form)
    kpi_form = MonthlyKPIForm()

    # defaults: show current month
    today = date.today()
    if request.method == 'GET':
        dr_form.start_date.data = date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        dr_form.end_date.data = date(today.year, today.month, last_day)

    # build query: tasks assigned to this user
    query = Task.query.join(Task.assignees).filter(User.id == user.id)

    if dr_form.start_date.data:
        query = query.filter(Task.start_date >= dr_form.start_date.data)
    if dr_form.end_date.data:
        query = query.filter(Task.start_date <= dr_form.end_date.data)
    if dr_form.completed_only.data:
        query = query.filter(Task.submitted == True)

    page = request.args.get('page', 1, type=int)
    tasks = query.order_by(Task.start_date.desc()).paginate(page=page, per_page=10, error_out=False)
    total = tasks.total
    completed = sum(1 for t in tasks.items if t.submitted)
    completed_all = query.filter(Task.submitted == True).count()

    # KPI submission handling
    if kpi_form.validate_on_submit():
        new_kpi = MonthlyKPI(
            user_id=user.id,
            reviewer_id=current_user.id,
            year=int(kpi_form.year.data),
            month=int(kpi_form.month.data),
            score=int(kpi_form.score.data),
            comments=kpi_form.comments.data
        )
        db.session.add(new_kpi)
        db.session.commit()
        flash('Monthly KPI submitted.', 'success')
        return redirect(url_for('user.user_detail', user_id=user.id))

    # display highest KPI for chosen (or current) month
    display_year = request.args.get('year', default=today.year, type=int)
    display_month = request.args.get('month', default=today.month, type=int)
    highest_kpi_row = MonthlyKPI.query.filter_by(user_id=user.id, year=display_year, month=display_month).order_by(MonthlyKPI.score.desc()).first()
    highest_kpi = highest_kpi_row.score if highest_kpi_row else None

    return render_template('user/detail.html', user=user, tasks=tasks, total=total, completed=completed, completed_all=completed_all,
                           dr_form=dr_form, kpi_form=kpi_form, display_year=display_year, display_month=display_month,
                           highest_kpi=highest_kpi)

@bp.route('/<int:user_id>/kpi/<int:year>/<int:month>')
@login_required
@role_required(60)
def user_kpi_detail(user_id, year, month):
    user = User.query.get_or_404(user_id)
    _user_view_permission_or_403(user)

    kpis = MonthlyKPI.query.filter_by(user_id=user.id, year=year, month=month).order_by(MonthlyKPI.score.desc()).all()

    # tasks within that month (by start_date)
    month_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = date(year, month, last_day)
    page = request.args.get('page', 1, type=int)
    tasks = Task.query.join(Task.assignees).filter(User.id == user.id, Task.start_date >= month_start, Task.start_date <= month_end).order_by(Task.start_date.desc()).paginate(page=page, per_page=10, error_out=False) 

    highest = kpis[0].score if kpis else None

    return render_template('user/kpi_detail.html', user=user, year=year, month=month, kpis=kpis, highest=highest, tasks=tasks)