from flask import abort
from flask_login import current_user

def role_required(min_level):
    def decorator(f):
        def wrapped(*args, **kwargs):
            user_roles = [assign.role.level for assign in current_user.assignments]
            if not user_roles or max(user_roles) < min_level:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator