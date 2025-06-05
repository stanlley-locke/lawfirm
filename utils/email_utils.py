# utils/email_utils.py

from flask_mail import Message
from threading import Thread
from flask import current_app

def _send_async_email(app, msg):
    """
    Background thread target: pushes an app context, retrieves the Mail extension,
    and sends the message. This avoids circular imports by not importing `mail` directly.
    """
    with app.app_context():
        mail_ext = current_app.extensions.get('mail')
        if mail_ext:
            mail_ext.send(msg)

def send_email(subject, recipients, text_body, html_body=None, reply_to=None):
    """
    Asynchronously send an email via Flask-Mail.

    :param subject:     Subject line of the email
    :param recipients:  List of recipient email addresses (e.g. ['admin@example.com'])
    :param text_body:   Plain-text body of the message
    :param html_body:   (Optional) HTML body of the message
    :param reply_to:    (Optional) email address to set as Reply‐To
    """
    default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
    msg = Message(subject, sender=default_sender, recipients=recipients)

    if reply_to:
        msg.reply_to = reply_to

    msg.body = text_body
    if html_body:
        msg.html = html_body

    # Send on a background thread
    Thread(target=_send_async_email, args=(current_app._get_current_object(), msg)).start()
