from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, URL

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    
class SecretLoginForm(FlaskForm):
    access_code = StringField('Access Code', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=30)])
    service = SelectField('Service', coerce=int, validators=[Optional()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])

class ServiceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=120)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    icon = StringField('Icon (Font Awesome)', validators=[Optional(), Length(max=50)])
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)

class TeamMemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=150)])
    position = StringField('Position', validators=[DataRequired(), Length(max=100)])
    bio = TextAreaField('Biography', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=30)])
    photo_url = StringField('Photo URL', validators=[Optional(), URL(), Length(max=255)])
    linkedin = StringField('LinkedIn URL', validators=[Optional(), URL(), Length(max=255)])
    twitter = StringField('Twitter URL', validators=[Optional(), URL(), Length(max=255)])
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)

class CaseStudyForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=200)])
    client = StringField('Client', validators=[Optional(), Length(max=100)])
    summary = TextAreaField('Summary', validators=[DataRequired()])
    challenge = TextAreaField('Challenge', validators=[Optional()])
    solution = TextAreaField('Solution', validators=[Optional()])
    outcome = TextAreaField('Outcome', validators=[Optional()])
    service_id = SelectField('Service', coerce=int, validators=[Optional()])
    featured = BooleanField('Featured', default=False)
    is_active = BooleanField('Active', default=True)
