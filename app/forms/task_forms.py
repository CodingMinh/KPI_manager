from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, DateField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class TaskForm(FlaskForm):
    name = StringField('Task Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    manager_id = SelectField('Manager', coerce=int, validators=[DataRequired()])
    assignees = SelectMultipleField('Assignees', coerce=int)
    start_date = DateField('Start Date')
    end_date = DateField('End Date')
    submit = SubmitField('Create/Edit Task')

class TaskReviewForm(FlaskForm):
    score = IntegerField('Score (0-100)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    comments = TextAreaField('Comments')
    submit = SubmitField('Submit Review')