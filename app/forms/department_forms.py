from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from app.models import Department

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired(), Length(min=1, max=128)])
    parent_id = SelectField('Parent Department', coerce=int, validators=[Optional()])
    submit = SubmitField('Create/Edit Department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_id.choices = [(-1, 'None')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]