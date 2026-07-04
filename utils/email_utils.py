import html
import logging
from threading import Thread

import resend
from flask import current_app

logger = logging.getLogger(__name__)


def _send_resend(params):
    api_key = current_app.config.get('RESEND_API_KEY')
    if not api_key:
        logger.warning('RESEND_API_KEY not configured; skipping email send')
        return None
    resend.api_key = api_key
    return resend.Emails.send(params)


def _send_async(app, params):
    with app.app_context():
        try:
            _send_resend(params)
        except Exception:
            logger.exception('Failed to send email via Resend')


def send_email(subject, recipients, text_body, html_body=None, reply_to=None):
    """
    Asynchronously send an email via Resend.

    :param subject: Email subject
    :param recipients: List of recipient email addresses
    :param text_body: Plain-text body
    :param html_body: Optional HTML body
    :param reply_to: Optional reply-to address
    """
    if not recipients:
        return

    sender = current_app.config.get('RESEND_FROM_EMAIL')
    params = {
        'from': sender,
        'to': recipients,
        'subject': subject,
        'text': text_body,
    }
    if html_body:
        params['html'] = html_body
    if reply_to:
        params['reply_to'] = reply_to

    Thread(
        target=_send_async,
        args=(current_app._get_current_object(), params),
    ).start()


def escape_html(value):
    """Escape user-supplied text for HTML email bodies."""
    return html.escape(str(value or ''), quote=True)
