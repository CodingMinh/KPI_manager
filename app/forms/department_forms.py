from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired()])
    parent_id = IntegerField('Parent Department ID')
    submit = SubmitField('Create Department')