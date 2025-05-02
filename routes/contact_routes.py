from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from app import db, mail
from models import Service, ContactMessage
from forms import ContactForm
from flask_mail import Message
from threading import Thread

contact_bp = Blueprint('contact', __name__)

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body=None):
    """Send email with optional HTML content"""
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    
    # Send email asynchronously to prevent blocking the main thread
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    
    # Get services for dropdown
    services = Service.query.filter_by(is_active=True).order_by(Service.title).all()
    form.service.choices = [(0, 'Select a service (optional)')] + [(s.id, s.title) for s in services]
    
    if form.validate_on_submit():
        # Handle service_id being None or 0
        service_id = form.service.data if form.service.data and form.service.data > 0 else None
        
        # Create new contact message
        message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data,
            service_id=service_id
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Send notification email to admin
        try:
            admin_email = current_app.config.get('MAIL_DEFAULT_SENDER')
            if admin_email:
                send_email(
                    subject=f"New Contact Form Submission: {form.subject.data}",
                    recipients=[admin_email],
                    text_body=f"""
New contact form submission from {form.name.data} ({form.email.data}):

Subject: {form.subject.data}
Service: {dict(form.service.choices).get(form.service.data, 'None')}
Phone: {form.phone.data or 'Not provided'}

Message:
{form.message.data}
                    """,
                    html_body=f"""
<h3>New Contact Form Submission</h3>
<p><strong>From:</strong> {form.name.data} (<a href="mailto:{form.email.data}">{form.email.data}</a>)</p>
<p><strong>Subject:</strong> {form.subject.data}</p>
<p><strong>Service:</strong> {dict(form.service.choices).get(form.service.data, 'None')}</p>
<p><strong>Phone:</strong> {form.phone.data or 'Not provided'}</p>
<p><strong>Message:</strong></p>
<p>{form.message.data}</p>
                    """
                )
        except Exception as e:
            current_app.logger.error(f"Failed to send email notification: {str(e)}")
        
        flash('Your message has been sent! We will get back to you soon.', 'success')
        return redirect(url_for('contact.thank_you'))
    
    return render_template('contact.html', title='Contact Us', form=form)

@contact_bp.route('/thank-you')
def thank_you():
    return render_template('contact.html', title='Thank You', thank_you=True)
