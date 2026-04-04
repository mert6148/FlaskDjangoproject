"""
Python Configuration Module for Flask-Django Application
Uygulamanın src klasörü için kapsamlı yapılandırma dosyası
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging
import logging.config
from datetime import datetime

# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent.parent

# Src dizini
SRC_DIR = Path(__file__).parent

class Config:
    """Ana yapılandırma sınıfı"""

    # ==========================================
    # TEMEL UYGULAMA AYARLARI
    # ==========================================

    # Uygulama bilgileri
    APP_NAME = "Flask-Django-SDK"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Flask ve Django frameworklerini birleştiren uygulama"

    # Çalışma ortamı
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'

    # ==========================================
    # WEB FRAMEWORK AYARLARI
    # ==========================================

    # Flask ayarları
    FLASK_CONFIG = {
        'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key-change-in-production'),
        'DEBUG': DEBUG,
        'TESTING': TESTING,
        'SESSION_COOKIE_SECURE': ENVIRONMENT == 'production',
        'REMEMBER_COOKIE_SECURE': ENVIRONMENT == 'production',
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
    }

    # Django ayarları
    DJANGO_CONFIG = {
        'SECRET_KEY': os.getenv('SECRET_KEY', 'your-django-secret-key'),
        'DEBUG': DEBUG,
        'ALLOWED_HOSTS': os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(','),
        'TIME_ZONE': 'Europe/Istanbul',
        'USE_TZ': True,
        'USE_I18N': True,
        'USE_L10N': True,
        'LANGUAGE_CODE': 'tr',
        'LANGUAGES': [
            ('tr', 'Türkçe'),
            ('en', 'English'),
        ],
    }

    # ==========================================
    # VERİTABANI AYARLARI
    # ==========================================

    # MySQL veritabanı ayarları
    DATABASE_CONFIG = {
        'ENGINE': os.getenv('DB_ENGINE', 'mysql'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': int(os.getenv('DB_PORT', '3306')),
        'NAME': os.getenv('DB_NAME', 'flask_django_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'CHARSET': 'utf8mb4',
        'COLLATION': 'utf8mb4_unicode_ci',
    }

    # SQLAlchemy URI (Flask için)
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DATABASE_CONFIG['USER']}:{DATABASE_CONFIG['PASSWORD']}"
        f"@{DATABASE_CONFIG['HOST']}:{DATABASE_CONFIG['PORT']}/{DATABASE_CONFIG['NAME']}"
    )

    # Django DATABASES ayarı
    DJANGO_DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DATABASE_CONFIG['NAME'],
            'USER': DATABASE_CONFIG['USER'],
            'PASSWORD': DATABASE_CONFIG['PASSWORD'],
            'HOST': DATABASE_CONFIG['HOST'],
            'PORT': DATABASE_CONFIG['PORT'],
            'OPTIONS': {
                'charset': DATABASE_CONFIG['CHARSET'],
                'init_command': f"SET sql_mode='STRICT_TRANS_TABLES', collation_connection='{DATABASE_CONFIG['COLLATION']}'",
            },
            'TEST': {
                'NAME': f"test_{DATABASE_CONFIG['NAME']}",
            },
        }
    }

    # ==========================================
    # LOGGING AYARLARI
    # ==========================================

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'INFO',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': str(SRC_DIR / 'logs' / 'app.log'),
                'formatter': 'detailed',
                'level': 'DEBUG',
            },
            'error_file': {
                'class': 'logging.FileHandler',
                'filename': str(SRC_DIR / 'logs' / 'error.log'),
                'formatter': 'detailed',
                'level': 'ERROR',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG' if DEBUG else 'INFO',
                'propagate': True,
            },
            'werkzeug': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
        }
    }

    # ==========================================
    # API AYARLARI
    # ==========================================

    API_CONFIG = {
        'VERSION': 'v1',
        'PREFIX': '/api',
        'HOST': os.getenv('API_HOST', '0.0.0.0'),
        'PORT': int(os.getenv('API_PORT', '5000')),
        'WORKERS': int(os.getenv('API_WORKERS', '4')),
        'TIMEOUT': int(os.getenv('API_TIMEOUT', '30')),
        'RATE_LIMIT': os.getenv('RATE_LIMIT', '100 per minute'),
        'CORS_ORIGINS': os.getenv('CORS_ORIGINS', '*').split(','),
    }

    # ==========================================
    # DOSYA VE KLASÖR YOLLARI
    # ==========================================

    # Dizin yapısı
    DIRECTORIES = {
        'LOGS': SRC_DIR / 'logs',
        'UPLOADS': SRC_DIR / 'uploads',
        'STATIC': SRC_DIR / 'static',
        'TEMPLATES': SRC_DIR / 'templates',
        'TEMP': SRC_DIR / 'temp',
        'BACKUPS': SRC_DIR / 'backups',
        'CONFIG': SRC_DIR / 'config',
    }

    # ==========================================
    # GÜVENLİK AYARLARI
    # ==========================================

    SECURITY_CONFIG = {
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'your-jwt-secret'),
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRATION_HOURS': int(os.getenv('JWT_EXPIRATION_HOURS', '24')),
        'BCRYPT_ROUNDS': int(os.getenv('BCRYPT_ROUNDS', '12')),
        'SESSION_TIMEOUT': int(os.getenv('SESSION_TIMEOUT', '3600')),
        'MAX_LOGIN_ATTEMPTS': int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
        'LOCKOUT_TIME': int(os.getenv('LOCKOUT_TIME', '900')),
    }

    # ==========================================
    # HARİCİ SERVİSLER
    # ==========================================

    EXTERNAL_SERVICES = {
        'REDIS': {
            'HOST': os.getenv('REDIS_HOST', 'localhost'),
            'PORT': int(os.getenv('REDIS_PORT', '6379')),
            'DB': int(os.getenv('REDIS_DB', '0')),
            'PASSWORD': os.getenv('REDIS_PASSWORD'),
        },
        'EMAIL': {
            'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'SMTP_PORT': int(os.getenv('SMTP_PORT', '587')),
            'USERNAME': os.getenv('EMAIL_USERNAME'),
            'PASSWORD': os.getenv('EMAIL_PASSWORD'),
            'USE_TLS': True,
        },
    }

    # ==========================================
    # ÖZEL AYARLAR
    # ==========================================

    CUSTOM_CONFIG = {
        'CACHE_ENABLED': os.getenv('CACHE_ENABLED', 'True').lower() == 'true',
        'CACHE_TTL': int(os.getenv('CACHE_TTL', '3600')),
        'FILE_UPLOAD_MAX_SIZE': int(os.getenv('FILE_UPLOAD_MAX_SIZE', '10485760')),  # 10MB
        'ALLOWED_EXTENSIONS': ['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.zip'],
        'BACKUP_RETENTION_DAYS': int(os.getenv('BACKUP_RETENTION_DAYS', '30')),
    }


class DevelopmentConfig(Config):
    """Geliştirme ortamı yapılandırması"""
    DEBUG = True
    ENVIRONMENT = 'development'

    FLASK_CONFIG = Config.FLASK_CONFIG.copy()
    FLASK_CONFIG.update({
        'DEBUG': True,
        'TEMPLATES_AUTO_RELOAD': True,
    })

    DJANGO_CONFIG = Config.DJANGO_CONFIG.copy()
    DJANGO_CONFIG.update({
        'DEBUG': True,
        'INSTALLED_APPS': [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework',
        ],
    })


class ProductionConfig(Config):
    """Üretim ortamı yapılandırması"""
    DEBUG = False
    ENVIRONMENT = 'production'

    FLASK_CONFIG = Config.FLASK_CONFIG.copy()
    FLASK_CONFIG.update({
        'DEBUG': False,
        'TESTING': False,
    })

    DJANGO_CONFIG = Config.DJANGO_CONFIG.copy()
    DJANGO_CONFIG.update({
        'DEBUG': False,
    })


class TestingConfig(Config):
    """Test ortamı yapılandırması"""
    DEBUG = True
    TESTING = True
    ENVIRONMENT = 'testing'

    DATABASE_CONFIG = Config.DATABASE_CONFIG.copy()
    DATABASE_CONFIG['NAME'] = 'test_flask_django_db'


# Yapılandırma haritası
CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config(environment: Optional[str] = None) -> Config:
    """Belirtilen ortama göre yapılandırma döndürür"""
    env = environment or os.getenv('ENVIRONMENT', 'development')
    config_class = CONFIG_MAP.get(env.lower(), CONFIG_MAP['default'])
    return config_class()


def setup_logging(config: Optional[Config] = None):
    """Logging yapılandırmasını kurar"""
    if config is None:
        config = get_config()

    # Logs klasörünü oluştur
    config.DIRECTORIES['LOGS'].mkdir(exist_ok=True)

    # Logging yapılandırmasını uygula
    logging.config.dictConfig(config.LOGGING_CONFIG)


def create_directories(config: Optional[Config] = None):
    """Gerekli klasörleri oluşturur"""
    if config is None:
        config = get_config()

    for dir_path in config.DIRECTORIES.values():
        dir_path.mkdir(exist_ok=True)


def load_env_file(filepath: str = None):
    """.env dosyasından ortam değişkenlerini yükler"""
    if filepath is None:
        filepath = SRC_DIR / '.env'

    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def save_config_to_file(config: Config, filepath: str = None):
    """Yapılandırmayı JSON dosyasına kaydeder"""
    if filepath is None:
        filepath = config.DIRECTORIES['CONFIG'] / 'config.json'

    config.DIRECTORIES['CONFIG'].mkdir(exist_ok=True)

    config_dict = {
        'app_name': config.APP_NAME,
        'app_version': config.APP_VERSION,
        'environment': config.ENVIRONMENT,
        'debug': config.DEBUG,
        'database': config.DATABASE_CONFIG,
        'api': config.API_CONFIG,
        'security': config.SECURITY_CONFIG,
        'saved_at': datetime.now().isoformat(),
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)


def load_config_from_file(filepath: str = None) -> Dict[str, Any]:
    """JSON dosyasından yapılandırmayı yükler"""
    if filepath is None:
        config = get_config()
        filepath = config.DIRECTORIES['CONFIG'] / 'config.json'

    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    return {}


# Global yapılandırma örneği
current_config = get_config()

# İlk çalıştırma işlemleri
if __name__ != '__main__':
    create_directories(current_config)
    setup_logging(current_config)