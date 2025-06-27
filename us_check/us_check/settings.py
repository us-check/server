import os
from pathlib import Path
from dotenv import load_dotenv
import google.auth
from google.cloud import firestore

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-b8h8a4b(^*-p3*_@_cc@@a3d0$__a6trf3kdr-$(9mmsttb^v!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SERVER_ADDRESS = os.environ.get('SERVER_ADDRESS', 'localhost')
CLIENT_ADDRESS = os.environ.get('CLIENT_ADDRESS', 'http://localhost:3000')

ALLOWED_HOSTS = [SERVER_ADDRESS, '127.0.0.1', 'localhost']

CORS_ALLOWED_ORIGINS = [CLIENT_ADDRESS]

CSRF_TRUSTED_ORIGINS = [CLIENT_ADDRESS]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'rest_framework',
    'corsheaders',
    'tourism',
    'gemini_ai',
    'qr_service',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}



ROOT_URLCONF = 'us_check.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'us_check.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Google Cloud Settings
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Firestore Settings
FIRESTORE_PROJECT_ID = os.environ.get('FIRESTORE_PROJECT_ID', 'gen-lang-client-0000121060')
FIRESTORE_DATABASE_ID = os.environ.get('FIRESTORE_DATABASE_ID', 'us-check2')

# Initialize Firestore client
try:
    if GOOGLE_APPLICATION_CREDENTIALS:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS
    
    # Initialize Firestore client with specific database
    FIRESTORE_CLIENT = firestore.Client(project=FIRESTORE_PROJECT_ID, database=FIRESTORE_DATABASE_ID)
except Exception as e:
    print(f"Warning: Could not initialize Firestore client: {e}")
    FIRESTORE_CLIENT = None

# QR Code Settings
QR_CODE_STORAGE_PATH = os.path.join(BASE_DIR, 'qr_codes')
QR_CODE_BASE_URL = f"{os.environ.get('SERVER_ADDRESS', 'http://localhost:8000')}/qr/"

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'gemini_ai': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'tourism': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
