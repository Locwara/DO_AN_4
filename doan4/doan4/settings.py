"""
Django settings for doan4 project.
"""

import os
from pathlib import Path
import cloudinary
import cloudinary.api
import cloudinary.uploader

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-2@0nlqs(9n2fvje)14!c*w2@!^2d#iha(@1*ucie-orlk&c^=)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-domain.com', '.vercel.app']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'cloudinary_storage',
    'cloudinary',
    'home',
    'uploads',
    
]


# Judge0 API configuration
JUDGE0_API_KEY = "30cd93ee1dmshd61ffa82465c463p152947jsn20ea0f13906a"
JUDGE0_BASE_URL = "judge0-ce.p.rapidapi.com"
AI_SETTINGS = {
    'GEMINI_API_KEY': 'AIzaSyB5r_8Ou0fDq-XHoBWHGIXWcblxkoa9VgM',  # Move to environment variable
    'MAX_DOCUMENT_SUGGESTIONS': 5,
    'MAX_CHATROOM_SUGGESTIONS': 5,
    'SEARCH_MIN_QUERY_LENGTH': 2,
    'ENABLE_AUTO_SUGGESTIONS': True,
}

# Google OAuth settings
GOOGLE_CLIENT_ID = '14310137293-ltolga7peevcmvb8jhq7al070416rrtm.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
AUTH_USER_MODEL = 'home.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'doan4.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'doan4.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres.jqdmwzgikcjxxcamafko',
        'PASSWORD': '280404',
        'HOST': 'aws-1-ap-southeast-1.pooler.supabase.com',
        'PORT': '6543',
    }
}

# Cloudinary configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dddpqvxzg',
    'API_KEY': '768143393531413',
    'API_SECRET': 'kvBPf1aaObw24uYYl_7gw6EZ2Aw'
}

cloudinary.config(
    cloud_name='dddpqvxzg',
    api_key='768143393531413', 
    api_secret='kvBPf1aaObw24uYYl_7gw6EZ2Aw'
)
# CLOUDINARY_STORAGE = {
#     'CLOUD_NAME': os.environ.get('CLOUD_NAME'),
#     'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
#     'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
# }

# cloudinary.config(
#     cloud_name=os.environ.get('CLOUD_NAME'),
#     api_key=os.environ.get('CLOUDINARY_API_KEY'),
#     api_secret=os.environ.get('CLOUDINARY_API_SECRET')
# )
# File storage configuration
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'static')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Vercel deployment configuration
if os.environ.get('VERCEL'):
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    DEBUG = False
else:
    STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'lethanhloc2612004@gmail.com'
EMAIL_HOST_PASSWORD = 'gqhn khbs wxzl ydgc'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'StudyBot <noreply@studybot.com>'

SITE_NAME = 'StudyBot'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o644

ALLOWED_UPLOAD_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', 
    '.txt', '.xls', '.xlsx', '.jpg', '.jpeg', 
    '.png', '.gif'
]

ALLOWED_UPLOAD_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png', 
    'image/gif'
]

# Session configuration
SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

SECURE_FILE_UPLOADS = True

# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Disable all custom logging - let Django use default console logging
LOGGING_CONFIG = None
# Production settings for Vercel
# Google OAuth settings for production
# Thêm vào cuối file settings.py
if os.environ.get('VERCEL'):
    DEBUG = False
    ALLOWED_HOSTS = ['.vercel.app', 'doan4-django.vercel.app']
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # CSRF settings for Vercel
    CSRF_TRUSTED_ORIGINS = ['https://doan4-django.vercel.app']
    SECURE_CROSS_ORIGIN_OPENER_POLICY = None
    
    # Logging để debug trên Vercel
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        },
    }
    

# HTTPS và Security settings cho Vercel
# Cloudinary configuration
if os.environ.get('VERCEL'):
    # Production - dùng environment variables
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'dddpqvxzg'),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY', '768143393531413'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', 'kvBPf1aaObw24uYYl_7gw6EZ2Aw'),
        'SECURE': True,
    }

    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dddpqvxzg'),
        api_key=os.environ.get('CLOUDINARY_API_KEY', '768143393531413'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'kvBPf1aaObw24uYYl_7gw6EZ2Aw'),
        secure=True
    )
else:
    # Local development - dùng hardcoded values
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': 'dddpqvxzg',
        'API_KEY': '768143393531413',
        'API_SECRET': 'kvBPf1aaObw24uYYl_7gw6EZ2Aw',
        'SECURE': True,
    }

    cloudinary.config(
        cloud_name='dddpqvxzg',
        api_key='768143393531413', 
        api_secret='kvBPf1aaObw24uYYl_7gw6EZ2Aw',
        secure=True
    )