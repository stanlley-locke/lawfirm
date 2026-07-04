from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, IntegerField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, URL, ValidationError
from models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')


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
    photo = FileField('Upload Photo')
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


class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=220)])
    summary = TextAreaField('Summary', validators=[DataRequired(), Length(max=500)])
    content = TextAreaField('Content', validators=[DataRequired()])
    is_published = BooleanField('Published', default=False)


class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password')])
    is_admin = BooleanField('Administrator', default=True)
    is_active = BooleanField('Active', default=True)

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_username(self, field):
        query = User.query.filter_by(username=field.data)
        if self.user:
            query = query.filter(User.id != self.user.id)
        if query.first():
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        query = User.query.filter_by(email=field.data)
        if self.user:
            query = query.filter(User.id != self.user.id)
        if query.first():
            raise ValidationError('Email already registered.')


class ReplyForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Message', validators=[DataRequired()])
