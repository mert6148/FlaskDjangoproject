# Flask-Django Src Configuration

Bu dizin, Flask-Django uygulamasının Python yapılandırma dosyalarını içerir.

## Dosya Yapısı

```
src/
├── __init__.py          # Python paketi başlatma dosyası
├── config.py            # Ana yapılandırma sınıfı
├── settings.py          # Django ayarları
├── .env.example         # Ortam değişkenleri örneği
├── logs/                # Uygulama logları
├── uploads/             # Dosya yüklemeleri
├── static/              # Statik dosyalar
├── templates/           # HTML şablonları
├── temp/                # Geçici dosyalar
├── backups/             # Yedekler
└── config/              # Yapılandırma dosyaları
```

## Ek Dokümantasyon

- `src/README.md`: `src` klasörü genel düzeni ve dil bazlı yapılar
- `src/docs/README.md`: dil bazlı dokümantasyon indeks dosyası
- `src/docs/`: Python, C#, JavaScript, HTML ve C/C++ yapılandırma rehberleri

## Kurulum

1. `.env.example` dosyasını `.env` olarak kopyalayın:
   ```bash
   cp .env.example .env
   ```

2. `.env` dosyasındaki değerleri düzenleyin.

3. Gerekli Python paketlerini yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## Yapılandırma Kullanımı

### Python Kodunda Kullanım

```python
from src.config import get_config, current_config

# Geçerli yapılandırmayı al
config = get_config()

# Veya global yapılandırmayı kullan
app_name = current_config.APP_NAME
db_config = current_config.DATABASE_CONFIG
```

### Flask Uygulamasında

```python
from flask import Flask
from src.config import current_config

app = Flask(__name__)
app.config.update(current_config.FLASK_CONFIG)

# Veritabanı URI'si
app.config['SQLALCHEMY_DATABASE_URI'] = current_config.SQLALCHEMY_DATABASE_URI
```

### Django Uygulamasında

Django ayarları `settings.py` dosyasında otomatik olarak yüklenir:

```python
# settings.py otomatik olarak config.py'den ayarları yükler
from .config import get_config

config = get_config()
# Django ayarları config.DJANGO_CONFIG'den gelir
```

## Ortam Değişkenleri

### Temel Ayarlar
- `ENVIRONMENT`: Çalışma ortamı (development/production/testing)
- `DEBUG`: Debug modu
- `SECRET_KEY`: Flask gizli anahtarı

### Veritabanı
- `DB_HOST`: Veritabanı sunucusu
- `DB_PORT`: Veritabanı portu
- `DB_NAME`: Veritabanı adı
- `DB_USER`: Veritabanı kullanıcı adı
- `DB_PASSWORD`: Veritabanı şifresi

### API Ayarları
- `API_HOST`: API sunucu adresi
- `API_PORT`: API portu
- `API_WORKERS`: Worker sayısı
- `RATE_LIMIT`: İstek limiti

### Güvenlik
- `JWT_SECRET_KEY`: JWT anahtarı
- `JWT_EXPIRATION_HOURS`: JWT geçerlilik süresi
- `BCRYPT_ROUNDS`: Şifre hash rounds

## Yapılandırma Sınıfları

### Config (Ana Sınıf)
Temel yapılandırma sınıfı. Tüm ayarları içerir.

### DevelopmentConfig
Geliştirme ortamı için özelleştirilmiş ayarlar.

### ProductionConfig
Üretim ortamı için güvenlik odaklı ayarlar.

### TestingConfig
Test ortamı için ayarlar.

## Logging

Uygulama otomatik olarak logging yapılandırmasını kurar. Log dosyaları `logs/` klasöründe bulunur:

- `app.log`: Genel uygulama logları
- `error.log`: Hata logları

## Dizinler

- `logs/`: Uygulama logları
- `uploads/`: Kullanıcı yüklemeleri
- `static/`: CSS, JS, resim dosyaları
- `templates/`: HTML şablonları
- `temp/`: Geçici dosyalar
- `backups/`: Veritabanı yedekleri
- `config/`: Yapılandırma JSON dosyaları

## Özel Ayarlar

`config.CUSTOM_CONFIG` altında özel ayarlar bulunur:

- `CACHE_ENABLED`: Cache aktif/pasif
- `CACHE_TTL`: Cache geçerlilik süresi
- `FILE_UPLOAD_MAX_SIZE`: Maximum dosya yükleme boyutu
- `ALLOWED_EXTENSIONS`: İzin verilen dosya uzantıları

## Yardımcı Fonksiyonlar

```python
from src.config import (
    setup_logging,          # Logging kur
    create_directories,     # Klasörleri oluştur
    load_env_file,         # .env dosyasını yükle
    save_config_to_file,   # Yapılandırmayı JSON'a kaydet
    load_config_from_file  # JSON'dan yapılandırma yükle
)

# Logging kur
setup_logging()

# Gerekli klasörleri oluştur
create_directories()

# .env dosyasını yükle
load_env_file()

# Yapılandırmayı JSON'a kaydet
config = get_config()
save_config_to_file(config)
```

## Test

Yapılandırmayı test etmek için:

```bash
cd src
python -c "from config import current_config; print(f'App: {current_config.APP_NAME}, Env: {current_config.ENVIRONMENT}')"
```

## Notlar

- Hassas bilgiler (şifreler, anahtarlar) asla koda hardcode edilmemelidir
- `.env` dosyası `.gitignore`'a eklenmelidir
- Üretim ortamında `DEBUG=False` olmalıdır
- Güvenlik ayarları üretim ortamına göre yapılandırılmalıdır