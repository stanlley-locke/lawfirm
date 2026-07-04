from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from extensions import db
from models import Service, ContactMessage
from forms import ContactForm
from utils.email_utils import send_email, escape_html

contact_bp = Blueprint('contact', __name__)


@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()

    services = Service.query.filter_by(is_active=True).order_by(Service.title).all()
    form.service.choices = [(0, 'Select a service (optional)')] + [(s.id, s.title) for s in services]

    if form.validate_on_submit():
        service_id = form.service.data if form.service.data and form.service.data > 0 else None
        new_message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data,
            service_id=service_id,
        )
        db.session.add(new_message)
        db.session.commit()

        try:
            admin_email = current_app.config.get('ADMIN_NOTIFICATION_EMAIL')
            if admin_email:
                service_label = dict(form.service.choices).get(form.service.data, 'None')
                text_body = f"""New contact form submission from {form.name.data} ({form.email.data}):

Subject: {form.subject.data}
Service: {service_label}
Phone: {form.phone.data or 'Not provided'}

Message:
{form.message.data}
"""
                html_body = f"""
<h3>New Contact Inquiry Submission</h3>
<p><strong>From:</strong> {escape_html(form.name.data)} &lt;{escape_html(form.email.data)}&gt;</p>
<p><strong>Subject:</strong> {escape_html(form.subject.data)}</p>
<p><strong>Service:</strong> {escape_html(service_label)}</p>
<p><strong>Phone:</strong> {escape_html(form.phone.data or 'Not provided')}</p>
<hr>
<p><strong>Message:</strong></p>
<p>{escape_html(form.message.data).replace(chr(10), '<br>')}</p>
"""
                send_email(
                    subject=f"New Contact Inquiry: {form.subject.data}",
                    recipients=[admin_email],
                    text_body=text_body,
                    html_body=html_body,
                    reply_to=form.email.data,
                )
        except Exception as e:
            current_app.logger.error('Failed to send email notification: %s', e)

        flash('Your message has been sent! We will get back to you soon.', 'success')
        return redirect(url_for('contact.thank_you'))

    return render_template('contact.html', title='Contact Us', form=form)


@contact_bp.route('/thank-you')
def thank_you():
    return render_template('contact.html', title='Thank You', thank_you=True)
