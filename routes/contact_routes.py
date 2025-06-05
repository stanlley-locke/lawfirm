# routes/contact_routes.py

import os
from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from app import db
from models import Service, ContactMessage, User
from forms import ContactForm
from flask_login import login_user
from utils.email_utils import send_email

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()

    # Populate the “Service” dropdown
    services = Service.query.filter_by(is_active=True).order_by(Service.title).all()
    form.service.choices = [(0, 'Select a service (optional)')] + [(s.id, s.title) for s in services]

    if form.validate_on_submit():
        # 1) Secret admin login check (if configured)
        if (form.email.data == os.getenv('ADMIN_SECRET_EMAIL') and 
            form.message.data == os.getenv('ADMIN_SECRET_MESSAGE')):
            admin = User.query.filter_by(username='admin').first()
            if admin and admin.check_password(os.getenv('ADMIN_SECRET_PASSWORD')):
                login_user(admin)
                flash('Logged in as administrator', 'success')
                return redirect(url_for('admin.dashboard'))

        # 2) Save the contact message to the database
        service_id = form.service.data if form.service.data and form.service.data > 0 else None
        new_message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data,
            service_id=service_id
        )
        db.session.add(new_message)
        db.session.commit()

        # 3) Send email notification to the admin
        try:
            admin_email = current_app.config.get('MAIL_DEFAULT_SENDER')
            if admin_email:
                # Build plain-text body
                text_body = f"""
New contact form submission from {form.name.data} ({form.email.data}):

Subject: {form.subject.data}
Service: {dict(form.service.choices).get(form.service.data, 'None')}
Phone: {form.phone.data or 'Not provided'}

Message:
{form.message.data}
                """

                # Build optional HTML body
                html_body = f"""
<h3>New Contact Inquiry Submission</h3>
<p><strong>From:</strong> {form.name.data} &lt;<a href="mailto:{form.email.data}">{form.email.data}</a>&gt;</p>
<p><strong>Subject:</strong> {form.subject.data}</p>
<p><strong>Service:</strong> {dict(form.service.choices).get(form.service.data, 'None')}</p>
<p><strong>Phone:</strong> {form.phone.data or 'Not provided'}</p>
<hr>
<p><strong>Message:</strong></p>
<p>{form.message.data}</p>
                """

                # Pass reply_to=form.email.data so replies go directly to the user
                send_email(
                    subject=f"New Contact Inquiry Submission: {form.subject.data}",
                    recipients=[admin_email],
                    text_body=text_body,
                    html_body=html_body,
                    reply_to=form.email.data
                )
        except Exception as e:
            current_app.logger.error(f"Failed to send email notification: {str(e)}")

        flash('Your message has been sent! We will get back to you soon.', 'success')
        return redirect(url_for('contact.thank_you'))

    return render_template('contact.html', title='Contact Us', form=form)

@contact_bp.route('/thank-you')
def thank_you():
    return render_template('contact.html', title='Thank You', thank_you=True)
