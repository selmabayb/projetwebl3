# monsite/settings.py

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# ENVIRONNEMENT
# =============================================================================
# Charger les variables d'environnement
# Pour utiliser un fichier .env, installer python-dotenv et décommenter:
# from dotenv import load_dotenv
# load_dotenv(BASE_DIR / '.env')

DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

# =============================================================================
# SÉCURITÉ
# =============================================================================
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-key-CHANGE-THIS-IN-PRODUCTION-7mz8x!k9j&h2w@4v'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# En production, définir DJANGO_ALLOWED_HOSTS='example.com,www.example.com'
ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1,testserver'
).split(',') if os.environ.get('DJANGO_ALLOWED_HOSTS') else ['localhost', '127.0.0.1', 'testserver']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Applications du projet - Architecture modulaire
    'garage.accounts',
    'garage.vehicles',
    'garage.catalog',
    'garage.cases',
    'garage.quotes',
    'garage.appointments',
    'garage.billing',
    'garage.notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'monsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            # Note: garage/templates est automatiquement détecté via APP_DIRS
        ],
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

WSGI_APPLICATION = 'monsite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Configuration via variables d'environnement
# Développement: SQLite (par défaut)
# Production: PostgreSQL (recommandé)

DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3')
DB_NAME = os.environ.get('DB_NAME', str(BASE_DIR / 'db.sqlite3'))

if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
        }
    }
else:
    # Configuration PostgreSQL/MySQL
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # BNF13: minimum 8 caractères
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = '/static/'

# En développement: utiliser STATICFILES_DIRS
# En production: utiliser STATIC_ROOT avec collectstatic
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'static']
else:
    STATIC_ROOT = BASE_DIR / 'staticfiles'


# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# CONFIGURATION EMAIL (BF35, BF36)
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Console en dev
DEFAULT_FROM_EMAIL = 'noreply@garage-auto-express.fr'
EMAIL_SUBJECT_PREFIX = '[Garage Auto Express] '

# En production, configurer SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@example.com'
# EMAIL_HOST_PASSWORD = 'your-password'


# =============================================================================
# CONFIGURATION AUTHENTIFICATION (BF1-4, BNF9)
# =============================================================================
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# =============================================================================
# CONFIGURATION SÉCURITÉ (BNF13)
# =============================================================================

# Session expire après 30 minutes d'inactivité
SESSION_COOKIE_AGE = 1800  # 30 minutes en secondes
SESSION_SAVE_EVERY_REQUEST = True  # Renouveler la session à chaque requête

# Sécurité des cookies (à activer en production avec HTTPS)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Protection contre le clickjacking
X_FRAME_OPTIONS = 'DENY'

# Protection XSS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True


# =============================================================================
# PARAMÈTRES MÉTIER DU GARAGE (BNF, Section 6.4)
# =============================================================================

# Taux horaire par défaut (modifiable via admin)
GARAGE_DEFAULT_HOURLY_RATE = 60.00  # euros/heure

# Taux de TVA par défaut
GARAGE_DEFAULT_VAT_RATE = 0.20  # 20%

# Validité des devis (en jours)
GARAGE_QUOTE_VALIDITY_DAYS = 15

# Délai minimum pour annuler/modifier un RDV (en heures)
GARAGE_APPOINTMENT_MIN_CANCEL_HOURS = 24

# Seuil de notification pour variation de devis (BF49)
GARAGE_QUOTE_VARIATION_THRESHOLD = 0.10  # 10%

# Informations du garage pour les documents
GARAGE_INFO = {
    'name': 'Garage Auto Express',
    'address': '123 Avenue de la Réparation',
    'postal_code': '75001',
    'city': 'Paris',
    'phone': '01 23 45 67 89',
    'email': 'contact@garage-auto-express.fr',
    'siret': '123 456 789 00012',
    'tva_number': 'FR12 123456789',
}

# Horaires d'ouverture pour les créneaux RDV
GARAGE_OPENING_HOURS = {
    'morning': {
        'start': '09:00',
        'end': '12:00',
    },
    'afternoon': {
        'start': '14:00',
        'end': '17:00',
    },
    'slot_duration': 60,  # minutes
}


# =============================================================================
# CONFIGURATION LOGGING
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'garage.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'garage': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Créer le dossier logs s'il n'existe pas
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
