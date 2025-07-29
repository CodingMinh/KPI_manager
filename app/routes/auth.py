from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth_forms import LoginForm, RegistrationForm
from app.models import User, Role, Department, UserAssignment, AccessRequest
from app.extensions import db
from app.utils.access_control import role_required

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        fresher_role = Role.query.filter_by(level=30).first()
        if not fresher_role:
            fresher_role = Role(name="Fresher", level=30)
            db.session.add(fresher_role)
            db.session.commit()

        default_dept = Department.query.first()
        if default_dept:
            ua = UserAssignment(user=user, department=default_dept, role=fresher_role)
            db.session.add(ua)
            db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/request-access', methods=['GET', 'POST'])
@login_required
def request_access():
    if request.method == 'POST':
        reason = request.form.get('reason')
        req = AccessRequest(user_id=current_user.id, reason=reason)
        db.session.add(req)
        db.session.commit()
        flash("Your access request has been submitted. An admin will review it.", "info")
        return redirect(url_for("home.dashboard"))
    return render_template("auth/request_access.html")

@bp.route('/access-requests')
@login_required
@role_required(80)
def view_access_requests():
    requests = AccessRequest.query.order_by(AccessRequest.timestamp.desc()).all()
    return render_template("access_requests.html", requests=requests)

@bp.route('/access-requests/<int:request_id>/approve', methods=['POST'])
@login_required
@role_required(80)
def approve_access_request(request_id):
    req = AccessRequest.query.get_or_404(request_id)
    req.status = 'approved'
    db.session.commit()
    flash("Access request approved.", "success")
    return redirect(url_for('auth.view_access_requests'))

@bp.route('/access-requests/<int:request_id>/deny', methods=['POST'])
@login_required
@role_required(80)
def deny_access_request(request_id):
    req = AccessRequest.query.get_or_404(request_id)
    req.status = 'denied'
    db.session.commit()
    flash("Access request denied.", "warning")
    return redirect(url_for('auth.view_access_requests'))