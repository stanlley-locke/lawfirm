import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = 1
worker_class = "eventlet"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
# Entry point: wsgi:app  (monkey_patch runs in wsgi.py before Flask imports)
