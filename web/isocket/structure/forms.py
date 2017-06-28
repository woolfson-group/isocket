from flask_wtf import Form
from wtforms import FileField, DecimalField, IntegerField
from wtforms.validators import DataRequired, NumberRange


class SocketForm(Form):
    structure = FileField('structure', validators=[DataRequired()])
    scut = DecimalField('scut', default=7.0, validators=[NumberRange(min=0.0)])
    kcut = IntegerField('kcut', default=2, validators=[NumberRange(min=0)])
