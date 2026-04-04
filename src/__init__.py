"""
Flask-Django Application Package
Uygulamanın src klasörü için Python paketi başlatma dosyası
"""

import os
import sys
from pathlib import Path

# Paket yolunu ayarla
PACKAGE_DIR = Path(__file__).parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

# Yapılandırmayı yükle
try:
    from .config import current_config, get_config, setup_logging, create_directories
    from .settings import *

    # İlk çalıştırma işlemleri
    create_directories(current_config)
    setup_logging(current_config)

except ImportError as e:
    print(f"Uyarı: Yapılandırma yüklenirken hata oluştu: {e}")
    print("Temel yapılandırma kullanılacak.")

# Paket bilgileri
__version__ = "1.0.0"
__author__ = "Flask-Django-SDK"
__description__ = "Flask ve Django frameworklerini birleştiren uygulama"

# Kullanılabilir modüller
__all__ = [
    'config',
    'settings',
    'api_demo',
    'app',
    'class',
    'mailer',
    'mysql_protection',
]

def get_app_info():
    """Uygulama bilgilerini döndürür"""
    return {
        'name': __author__,
        'version': __version__,
        'description': __description__,
        'package_dir': str(PACKAGE_DIR),
        'python_version': sys.version,
        'platform': sys.platform,
    }

def initialize_app(environment=None):
    """Uygulamayı belirtilen ortam için başlatır"""
    config = get_config(environment)
    create_directories(config)
    setup_logging(config)
    return config