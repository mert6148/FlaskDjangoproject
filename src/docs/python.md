# Python Dökümantasyonu

`src/python/` dizini Python uygulama kodlarını ve araçlarını içerir.

## İçerik

- `api_demo.py` - Flask tabanlı basit API demo
- `app.py` - Python framework başlatma dosyası
- `class.py` - temel sınıf ve sistem işlevleri örnekleri
- `mailer.py` - e-posta gönderim yardımcı fonksiyonları
- `mysql_protection.py` - MySQL koruma ve güvenlik betiği
- `print.py` - yazdırma ve raporlama yardımcı modülü

## Yapılandırma

Root seviyede `config.py`, `settings.py` ve `__init__.py` Python yapılandırma paketini oluşturur.

### Kullanım

```python
from src.config import current_config
from src import initialize_app

config = current_config
print(config.APP_NAME)
```

### Önerilen Geliştirme Akışı

1. `.env.example` dosyasını `src/.env` olarak kopyalayın.
2. `src/config.py` içinde `Config`, `DevelopmentConfig`, `ProductionConfig`, `TestingConfig` sınıflarını kullanın.
3. `src/python/` altındaki modülleri proje kodunuza import edin.
