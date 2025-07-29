import functools
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

def role_required(min_level):
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.max_role_level < min_level:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('home.dashboard'))
            return func(*args, **kwargs)
        return wrapped
    return decorator

def department_manager_required(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        dept_id = kwargs.get('department_id') or request.form.get('department_id')
        found = False
        for assign in current_user.assignments:
            if assign.department_id == int(dept_id) and assign.role.level >= 60:
                found = True
                break
        if not found:
            abort(403)
        return func(*args, **kwargs)
    return wrapped