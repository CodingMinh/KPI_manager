from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField, StringField
from wtforms.validators import DataRequired, Email, Length
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
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=128)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    department_id = SelectField('Department', coerce=int)
    role_id = SelectField('Role', coerce=int)
    submit = SubmitField('Update')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Department, Role
        self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
        self.role_id.choices = [(r.id, f"{r.name} (Level {r.level})") for r in Role.query.order_by(Role.level).all()]