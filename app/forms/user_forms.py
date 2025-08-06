from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField, StringField
from wtforms.validators import DataRequired, Email
from app.models import User, Department, Role, UserAssignment

class UserRoleAssignForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    department_id = SelectField('Department', coerce=int, validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id.choices = [(u.id, u.name) for u in User.query.all()]
        self.department_id.choices = [(d.id, d.name) for d in Department.query.all()]
        self.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.level.desc()).all()]

class UserAssignmentEditForm(FlaskForm):
    assignment_id = HiddenField("Assignment ID")
    role_id = SelectField("Role", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Update")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.level.desc()).all()]

class EditUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Update")