"""Shared firm contact details and link builders."""

from urllib.parse import quote

FIRM_EMAIL = 'danochiengadvocates@gmail.com'
FIRM_PHONE_PRIMARY = '0729 116 086'
FIRM_PHONE_PRIMARY_TEL = '+254729116086'
FIRM_PHONE_SECONDARY = '0734 090 411'
FIRM_PHONE_SECONDARY_TEL = '+254734090411'
FIRM_WHATSAPP_NUMBER = '254729116086'
FIRM_INQUIRY_SUBJECT = 'Legal Inquiry - Dan Ochieng & Company Advocates'
FIRM_INQUIRY_BODY = (
    'Hello, I would like to inquire about your legal services. '
    'Please contact me at your earliest convenience.'
)


def tel_href(display_number):
    """Convert a Kenyan display number to a tel: href value."""
    digits = ''.join(c for c in display_number if c.isdigit())
    if digits.startswith('0'):
        return '+254' + digits[1:]
    if digits.startswith('254'):
        return '+' + digits
    return '+' + digits if digits else ''


def mailto_url(subject=None, body=None):
    subject = subject or FIRM_INQUIRY_SUBJECT
    body = body or FIRM_INQUIRY_BODY
    return (
        f'mailto:{FIRM_EMAIL}'
        f'?subject={quote(subject)}'
        f'&body={quote(body)}'
    )


def consultation_mailto(member_name):
    subject = f'Consultation Request - {member_name}'
    return mailto_url(subject=subject)


def whatsapp_url(text=None):
    text = text or FIRM_INQUIRY_BODY
    return f'https://wa.me/{FIRM_WHATSAPP_NUMBER}?text={quote(text)}'


def split_phone_parts(phone_str):
    """Split stored phone strings like '0729 090 411 / 0734 090 411' into link pairs."""
    if not phone_str:
        return []
    parts = []
    for chunk in phone_str.replace(',', '/').split('/'):
        display = chunk.strip()
        if not display:
            continue
        href = tel_href(display)
        parts.append({'display': display, 'href': href})
    return parts
