from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, EqualTo, Optional, ValidationError

# Vozidla
class VehicleForm(FlaskForm):
    brand = StringField('Brand', validators=[DataRequired(), Length(min=2, max=50)])
    model = StringField('Model', validators=[DataRequired(), Length(min=1, max=50)])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1886, max=2100)])
    submit = SubmitField('Add Vehicle')

# Registrace
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Přihlášení
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Aktualizace profilu
class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('New Password')
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('password', message="❌ Passwords must match.")])
    submit = SubmitField('Save Changes')