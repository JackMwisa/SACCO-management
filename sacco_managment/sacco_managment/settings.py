"""
Django settings for sacco_managment project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
import dj_database_url


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-_xw^7ywak0*p2gyt4&5@27)-^(p(2c8n9b=l*6p4rup6iih4dv"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['sacco-management.onrender.com', '127.0.0.1', 'localhost']

LANGUAGE_CODE = 'en'

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('fr', 'French'),
    ('sw', 'Swahili'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale', 
    
]

# Application definition

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    'django.contrib.sites',
    # 'django.contrib.sites',
    

    
    # My Apps
    "core",
    "user_auths",
    "account",
    "financial_services",
    "reports",
    "support",
    "api",
    
    # PWA
    "pwa",
    # 'sass_processor',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  
    "django.contrib.auth.middleware.AuthenticationMiddleware",   
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
]

# Logout settings
LOGOUT_REDIRECT_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGIN_URL = '/admin/login/'

# CSRF settings
CSRF_USE_SESSIONS = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG  # True in production
CSRF_TRUSTED_ORIGINS = ['https://sacco-management.onrender.com'] 



STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',  # Add this line
]

SASS_PROCESSOR_INCLUDE_DIRS = [
    os.path.join(BASE_DIR, 'static/assets2/scss'),
]


# User agent
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

USER_AGENTS_CACHE = 'default'



ROOT_URLCONF = "sacco_managment.urls"

LOGOUT_REDIRECT_URL = '/admin/login/'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'custom_filters': 'financial_services.templatetags.custom_filters',
            }
        },
    },
]

WSGI_APPLICATION = "sacco_managment.wsgi.application"




# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES['default'].update(db_from_env)



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # For production


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



AUTH_USER_MODEL = "user_auths.User"




# PWA Settings
PWA_APP_NAME = 'Prime SACCO'
PWA_APP_DESCRIPTION = "Prime SACCO Management System"
PWA_APP_THEME_COLOR = '#4a90e2'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'portrait'
PWA_APP_START_URL = '/'
PWA_APP_ICONS = [
    {
        'src': '/static/icon/icon-192x192.png',
        'sizes': '192x192',
        'type': 'image/png'
    },
    {
        'src': '/static/icon/icon-512x512.png',
        'sizes': '512x512',
        'type': 'image/png'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/icons/splash-640x1136.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'


PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static', 'serviceworker.js')


JAZZMIN_SETTINGS = {
    # General Settings
    "site_title": "SACCO Admin Pro",
    "site_header": "Gem SACCO Management",
    "site_brand": "Gem SACCO",
    "site_logo": "assets/images/logo1.png",
    # "site_logo_classes": "img-circle",
    "site_icon": "img/favicon.ico",
    "welcome_sign": "Welcome to Gems SACCO Administration Portal",
    "copyright": "Prime SACCO Ltd ",


    # Theme Settings
    "theme": "flatly",
    "dark_mode_theme": "cyborg",
    "show_ui_builder": True,

    # Custom Icons & Styling
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user-shield",
        "auth.group": "fas fa-users",
        "sacco.Member": "fas fa-user-tie",
        "sacco.Account": "fas fa-wallet",
        "sacco.Transaction": "fas fa-money-check-alt",
        "sacco.Loan": "fas fa-hand-holding-usd",
        "sacco.Branch": "fas fa-university",
        "admin.LogEntry": "fas fa-file",
        "user_auths.User": "fas fa-user",
        "user_auths.Profile": "fas fa-address-card",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-dot-circle",
    "logout_url": "/admin/logout/",
    "logout_redirect_url": "/admin/login/",

    # Top Menu Configuration
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Public Site", "url": "/", "new_window": True},
        {"app": "sacco"},
        {"model": "sacco.Member"},
        {"model": "sacco.Transaction"},
        {"name": "Support", "url": "https://support.gemsacco.com", "new_window": True},
        {
            "name": "Logout", 
            "url": "/admin/logout/",
            "new_window": False,
            "icon": "fas fa-sign-out-alt",
        },
    ],

    # Sidebar Customization
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": [
        "sacco",
        "sacco.Member", 
        "sacco.Account",
        "sacco.Transaction",
        "sacco.Loan",
        "auth",
        "store",
        "store.product",
        "store.cartorder",
        "store.cartorderitem",
        "store.category",
        "store.brand",
        "store.productfaq",
        "store.productoffers",
        "store.productbidders",
        "store.review",
        "vendor",
        "user_auths",
        "addons",
        "addons.Company",
        "addons.BasicAddon",
    ],
    
    "custom_links": {
        "sacco": [{
            "name": "Financial Reports", 
            "url": "financial_reports",
            "icon": "fas fa-chart-line",
            "permissions": ["sacco.view_transaction"]
        }]
    },

    # Advanced UI Configuration
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
        "sacco.Transaction": "single",
    },
    "related_modal_active": True,
    "use_google_fonts_cdn": True,

    # Custom CSS/JS
    "custom_css": "css/admin-custom.css",
    "custom_js": "js/admin-custom.js",

    # Additional Features
    # "search_model": ["sacco.Member", "sacco.Account", "auth.User"],
    "language_chooser": False,
    "user_avatar": "avatar",
}



JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,  # Better readability
    "brand_small_text": False,
    "brand_colour": "navbar-dark",  # Dark navbar for a professional look
    "accent": "accent-gold",  # Gold accent for premium feel
    "navbar": "navbar-dark navbar-navy",  # Navy blue navbar for a corporate look
    "no_navbar_border": True,  # Cleaner look
    "navbar_fixed": True,  # Keep navbar fixed for easy navigation
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,  # Fixed sidebar for easy access to menu items
    "sidebar": "sidebar-dark-primary",  # Dark sidebar for contrast
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,  # More structured sidebar
    "sidebar_nav_compact_style": True,  # Clean and modern compact style
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,  # Flat UI for modern look
    "theme": "superhero",  # Premium banking UI feel
    "dark_mode_theme": "solar",  # Optimized dark mode for finance/admin users
    "button_classes": {
        "primary": "btn-primary btn-lg",  # Larger buttons for easier interaction
        "secondary": "btn-outline-secondary",
        "info": "btn-outline-info",
        "warning": "btn-outline-warning",
        "danger": "btn-outline-danger",
        "success": "btn-outline-success",
    },
}
