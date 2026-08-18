import html
import logging
from datetime import datetime
from threading import Thread

import resend
from flask import current_app, render_template, url_for

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


def send_email(subject, recipients, text_body, html_body=None, reply_to=None, attachments=None):
    """
    Asynchronously send an email via Resend.

    :param subject: Email subject
    :param recipients: List of recipient email addresses
    :param text_body: Plain-text body
    :param html_body: Optional HTML body
    :param reply_to: Optional reply-to address
    :param attachments: Optional list of dicts with 'content' (base64 string) and 'filename'
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
    if attachments:
        params['attachments'] = attachments

    Thread(
        target=_send_async,
        args=(current_app._get_current_object(), params),
    ).start()


def escape_html(value):
    """Escape user-supplied text for HTML email bodies."""
    return html.escape(str(value or ''), quote=True)


def _default_email_context():
    """Shared branding context injected into every templated email."""
    from utils import firm_contact

    try:
        logo_url = url_for(
            'static', filename='images/logo/dan_ochieng_advocates_logo.webp', _external=True
        )
    except RuntimeError:
        # No active request context (e.g. called from a background job) — fall
        # back to building the URL from the configured public base URL.
        base_url = (current_app.config.get('BASE_URL') or '').rstrip('/')
        logo_url = f"{base_url}/static/images/logo/dan_ochieng_advocates_logo.webp"

    return {
        'app_name': current_app.config.get('APP_NAME', "Dan Ochieng Advocates LLP"),
        'current_year': datetime.utcnow().year,
        'logo_url': logo_url,
        'firm_email': firm_contact.FIRM_EMAIL,
        'firm_phone_primary': firm_contact.FIRM_PHONE_PRIMARY,
        'firm_phone_primary_tel': firm_contact.FIRM_PHONE_PRIMARY_TEL,
    }


def render_email_template(template_name, **context):
    """Render an HTML email template with shared branding context applied."""
    merged = _default_email_context()
    merged.update(context)
    return render_template(template_name, **merged)


def send_template_email(subject, recipients, template_name, text_body, context=None,
                         reply_to=None, attachments=None):
    """
    Render a styled HTML email template (extending templates/emails/base_email.html)
    and send it via Resend with an accompanying plain-text fallback part.
    """
    html_body = render_email_template(template_name, **(context or {}))
    send_email(
        subject=subject,
        recipients=recipients,
        text_body=text_body,
        html_body=html_body,
        reply_to=reply_to,
        attachments=attachments,
    )
