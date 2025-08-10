from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth_forms import LoginForm, RegistrationForm, ResetPasswordForm, RequestPasswordResetForm
from app.models import User, Role, Department, UserAssignment, AccessRequest
from app.extensions import db
from app.utils.access_control import role_required
from app.utils.email import send_email
from datetime import datetime, timezone
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

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
    return render_template('auth/login.html', title='Login', form=form)

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
    return render_template('auth/register.html', title='Register', form=form)

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = get_serializer().dumps(user.email, salt='password-reset-salt')
            send_email(
                subject='Reset Your Password',
                sender=current_user.email,
                recipients=[user.email],
                text_body=render_template('email/reset_password.txt', user=user, token=token),
                html_body=render_template('email/reset_password.html', user=user, token=token)
            )
        flash('If your email is registered, you will receive a password reset link.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    try:
        email = get_serializer().loads(token, salt='password-reset-salt', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.reset_password_request'))
    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

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

        admins = User.query.join(User.assignments).join(UserAssignment.role).filter(Role.level >= 80).distinct()
        for admin in admins:
            send_email(
                subject="New Access Request",
                sender=current_user.email,
                recipients=[admin.email],
                text_body=render_template("email/access_request.txt", user=current_user, reason=reason),
                html_body=render_template("email/access_request.html", user=current_user, reason=reason)
            )

        flash("Your access request has been submitted. An admin will review it.", "info")
        return redirect(url_for("home.dashboard"))
    return render_template("auth/request_access.html", title='Request Access')

@bp.route('/access-requests')
@login_required
@role_required(80)
def view_access_requests():
    requests = AccessRequest.query.order_by(AccessRequest.timestamp.desc()).all()
    roles = Role.query.order_by(Role.level.asc()).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template("access_requests.html", requests=requests, title='Access Requests', roles=roles, departments=departments)

@bp.route('/access-requests/<int:request_id>/<action>', methods=['POST'])
@login_required
@role_required(80)
def handle_access_request(request_id, action):
    req = AccessRequest.query.get_or_404(request_id)
    req.decision_timestamp = datetime.now(timezone.utc)
    req.decided_by = current_user.id

    user = User.query.get(req.user_id)

    if action == 'approve':
        role_id = request.form.get("role_id", type=int)
        role = Role.query.get(role_id)
        dept = Department.query.first()
        if role and dept:
            req.status = 'approved'
            db.session.add(UserAssignment(user_id=user.id, department_id=dept.id, role_id=role.id))
            db.session.commit()
            send_email(
                subject="Access Request Approved",
                sender=current_user.email,
                recipients=[user.email],
                text_body=render_template("email/approved_request.txt", user=user, role=role.name),
                html_body=render_template("email/approved_request.html", user=user, role=role.name)
            )
            flash("Request approved and role assigned.", "success")
        else:
            flash("Invalid role or department.", "danger")
    elif action == 'deny':
        req.status = 'denied'
        db.session.commit()
        send_email(
            subject="Access Request Denied",
            sender=current_user.email,
            recipients=[user.email],
            text_body=render_template("email/denied_request.txt", user=user),
            html_body=render_template("email/denied_request.html", user=user)
        )
        flash("Request denied.", "warning")
    else:
        flash("Invalid action.", "danger")

    return redirect(url_for('auth.view_access_requests'))