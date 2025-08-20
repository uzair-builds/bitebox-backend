

from pathlib import Path
from datetime import timedelta
import os
import dj_database_url
from decouple import config as env
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-_zk=9yl=ul!po@_z-)wq&x4=&!(ons2(pogyu52+f7f37v3j$y'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['bite-box.bitebox.live','www.bite-box.bitebox.live',]
# ALLOWED_HOSTS = ['bite-box.edu2skill.online']
ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'daphne',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'account',
    'restaurants',
    'store',
    'customers',
    'channels',
    'tracking',
    'whitenoise.runserver_nostatic',  # Add this line
]

ASGI_APPLICATION = "backend.asgi.application"

# Redis configuration for real-time updates
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [("127.0.0.1", 6379)],
#         },
#     },
# }


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"  # Use Redis in production
    },
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this line
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CSRF_TRUSTED_ORIGINS = ['https://bitebox-backend-production.up.railway.app']

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'





# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'bitebox-final',  # The name of your PostgreSQL database
#         'USER': 'bitebox_final',      # The PostgreSQL username
#         'PASSWORD': 'bitebox-final',  # The PostgreSQL password
#         'HOST': 'bitebox-final.cy5we2w0kngu.us-east-1.rds.amazonaws.com',   # The host (leave as 'localhost' for local databases)
#         'PORT': '5432',        # The PostgreSQL port (5432 is the default)
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'Bitebox',  # The name of your PostgreSQL database
        'USER': 'Bitebox',      # The PostgreSQL username
        'PASSWORD': 'Bitebox',  # The PostgreSQL password
        'HOST': 'localhost',   # The host (leave as 'localhost' for local databases)
        'PORT': '5432',        # The PostgreSQL port (5432 is the default)
    }
}

POSTGRES_LOCALLY= False
ENVIRONMENT = env("ENVIRONMENT", default="development")
# If using PostgreSQL locally, set POSTGRES_LOCALLY to True
if ENVIRONMENT == 'production' or POSTGRES_LOCALLY:
    DATABASES['default']=dj_database_url.parse(env('DATABASE_URL'))
    

# JWT Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# settings.py

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'  # URL to access static files
STATICFILES_DIRS = [BASE_DIR / "static"]  # Directory for static files in development
STATIC_ROOT = BASE_DIR / "staticfiles"  # Directory for static files in production

# settings.py

MEDIA_URL = '/media/'  # URL to access media files
MEDIA_ROOT = BASE_DIR / "media"  # Directory to store uploaded media files


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'account.User'

# Email Configuration
# EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASS')
# # EMAIL_PORT = 587
# # EMAIL_USE_TLS = True
# EMAIL_PORT = 465
# EMAIL_USE_TLS = False
# EMAIL_USE_SSL = True
# EMAIL_TIMEOUT = 30

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'uzairnew15@gmail.com'
EMAIL_HOST_PASSWORD = 'zahkmkrxbgekvkfj'  # Not your Gmail password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER






# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=20),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=90),

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

}

# settings.py
PASSWORD_RESET_TIMEOUT = 60 * 30  # 30 minutes

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    'https://bitebox.live',
    "https://www.bitebox.live",
]