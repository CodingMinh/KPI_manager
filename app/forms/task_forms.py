from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, DateField, SubmitField
from wtforms.validators import DataRequired

class TaskForm(FlaskForm):
    name = StringField('Task Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    manager_id = SelectField('Manager', coerce=int)
    assignees = SelectMultipleField('Assignees', coerce=int)
    start_date = DateField('Start Date')
    end_date = DateField('End Date')
    submit = SubmitField('Create Task')