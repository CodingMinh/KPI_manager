from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from app.models import Department

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(min=1, max=128)])
    department_id = SelectField('Department', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Create/Edit Project')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]