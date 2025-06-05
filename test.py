# test_email.py

import os
from flask import Flask
from flask_mail import Mail
from dotenv import load_dotenv

# 1) Load .env so MAIL_USERNAME, MAIL_PASSWORD, etc. are available
load_dotenv()

# 2) Create a fresh Flask app for testing
test_app = Flask(__name__)
test_app.config['MAIL_SERVER'] = os.getenv('SMTP_HOST', 'smtp.gmail.com')
test_app.config['MAIL_PORT'] = int(os.getenv('SMTP_PORT', 587))
test_app.config['MAIL_USE_TLS'] = os.getenv('SMTP_USE_TLS', 'True').lower() in ['true', '1', 't']
test_app.config['MAIL_USE_SSL'] = False
test_app.config['MAIL_USERNAME'] = os.getenv('SMTP_USER')
test_app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASS')
test_app.config['MAIL_DEFAULT_SENDER'] = os.getenv('SMTP_USER')

mail = Mail(test_app)

# 3) Import send_email from utils (no circular import because we are not loading app.py)
from utils.email_utils import send_email

with test_app.app_context():
    send_email(
        subject="Test Email from Flask",
        recipients=[os.getenv('TEST_RECIPIENT')],
        text_body="If you see this, SMTP is working correctly.",
        html_body="<p><strong>If you see this, SMTP has been implemented correctly and its working</strong></p>",
        reply_to=os.getenv('TEST_RECIPIENT')
    )
    print("Test email triggered. Check your inbox.")
