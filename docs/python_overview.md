# Flask/Django Python Kod Dokümantasyonu

Bu doküman, `app/`, `auth/` ve ana proje düzeyindeki Flask/Django uygulama kod tabanını özetler. Amaç: frontendsel hızlı kılavuz elde etmek ve tüm önemli kod noktalarını merkezi bir .md dosyada birleştirmek.

## 1. Ana Uygulama (root/app.py)

- `Flask` tabanlı servis
- `/` rotası: `index.html` render
- `/api/status` rotası: durum, versiyon ve MySQL konfigürasyon durumu
- `/api/db-check` rotası: SQLAlchemy `SELECT 1` testi
- `MYSQL_DATABASE_URL` veya `DATABASE_URL` ortam değişkeni ile bağlantı
- `SafeZipFile`, `SafeZipInfo` sınıflarıyla zip güvenliği

### Önemli fonksiyonlar
- `v4_int_to_packed(address: int)`
- `OP_NO_COMPRESSION` sınıfı
- `SafeZipFile` wrapper
- `db_check` ve `status` endpointleri

## 2. `auth/main.py` (Flask + Django dönüşümlü)

- `MODE` ortam değişkeni (`flask` / `django`)
- `create_flask_app()` :
  - SQLAlchemy modelleri `Kullanici`, `Urun`
  - veri doğrulama, CRUD endpointleri
  - güvenlik: IP blacklist + headers + CORS gibi genel kontrol noktaları
  - `/api/db-check` ile MySQL/SQLite bağlantı
- `django_yapilandir()`:
  - Tek-dosya Django ayarı, REST Framework
  - Modeller: `Kategori`, `Urun`
  - ViewSet ve Serializerlerle `Kategori` ve `Urun` API
- Main giriş noktası: `MODE`'e göre Flask veya Django başlatma

## 3. `app/fastadmin` (adapter + ORM destekleri)

- `api/frameworks/flask`, `api/frameworks/django`, `api/frameworks/fastapi` kökleri
- modüler admin/CRUD desteği
- `models/orms` backend adapterleri: `django`, `sqlalchemy`, `ponyorm`, `tortoise`
- uygulama çalıştırma, servis ve DSL tabanlı model

## 4. `sys/api` (API controller + server)

- `sys/api/api_server.py`, `sys/api/api_controller.py`
- sistem-level API (monitor, yönetim)

## 5. `src` ve `test` kısımlarında koruma

- `src/mysql_protection.py`: MySQL URL ayrıştırma, `SELECT 1` testi
- `test/test_mysql_protection.py`: pytest test senaryoları
- `sys/mysql_protection.ps1` + `src/src_protection.bat`: MySQL servis kontrol, `my.ini` bind-address kontrol, yedekleme

## 6. Dökümantasyon ve Front-end konu bağlantısı

- Bu doküman `docs/index.html` içine menü aksiyonu olarak eklenmiştir.
- Frontend entegrasyon noktası: `frontend_integration.py`, `index.js` fonksiyonları (`getIntegrationStatus`, `setIntegrationMode`, `proxyApi`).

---

### Kullanım

1. Dokümanı açın: `docs/python_overview.md`
2. `frontend_integration.py` ile servisleri başlatın:
   - `python frontend_integration.py`
3. Front-end kontrol: `http://127.0.0.1:9000` veya `docs/index.html`
4. MySQL URL:
   - `set MYSQL_DATABASE_URL=mysql+mysqlconnector://user:pass@127.0.0.1:3306/db`
5. DB testleri:
   - Flask `GET /api/db-check`
   - Python `python src/mysql_protection.py`
   - PowerShell `sys/mysql_protection.ps1`

