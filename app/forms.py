from flask_wtf import Form
from wtforms import StringField, BooleanField, SelectField, FileField, DecimalField, IntegerField
from wtforms.validators import DataRequired, Regexp, NumberRange


class SocketForm(Form):
    file = FileField('file')
    scut = DecimalField('scut', default=7.0)
    kcut = IntegerField('kcut', default=2)
