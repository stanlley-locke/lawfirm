from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, IntegerField, FileField, DateField, FloatField
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
    practice_number = StringField('Practice Number', validators=[Optional(), Length(max=50)])
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


class ClientCaseForm(FlaskForm):
    case_number = StringField('Case Number', validators=[DataRequired(), Length(max=50)])
    title = StringField('Case Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Optional()])
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    case_type = SelectField('Case Type', choices=[
        ('Land Law', 'Land Law'),
        ('Commercial Law', 'Commercial Law'),
        ('Company Law', 'Company Law'),
        ('Property & Conveyance', 'Property & Conveyance'),
        ('Family Law', 'Family Law'),
        ('Criminal Law', 'Criminal Law'),
        ('Civil Litigation', 'Civil Litigation'),
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Active', 'Active'),
        ('Pending', 'Pending'),
        ('Closed', 'Closed'),
    ], default='Active', validators=[DataRequired()])
    reference_code = StringField('Reference Code (Optional, leave blank to auto-generate)', validators=[Optional(), Length(max=50)])


class MilestoneForm(FlaskForm):
    title = StringField('Milestone Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Optional()])
    date = DateField('Target Date', format='%Y-%m-%d', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Upcoming', 'Upcoming'),
        ('Completed', 'Completed'),
    ], default='Upcoming', validators=[DataRequired()])


class InvoiceForm(FlaskForm):
    invoice_number = StringField('Invoice Number', validators=[DataRequired(), Length(max=50)])
    amount = FloatField('Amount (KES)', validators=[DataRequired()])
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
    ], default='Unpaid', validators=[DataRequired()])

