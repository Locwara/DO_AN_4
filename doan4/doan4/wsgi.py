"""
WSGI config for doan4 project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doan4.settings')

# Vercel yêu cầu biến 'app' 
app = get_wsgi_application()

# Để tương thích ngược
application = app
