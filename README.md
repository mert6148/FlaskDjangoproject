# Proje hakkında

Flask ve Django ile oluşturulan bu proje Python ve Javascript ile yazılmış olup uygulamalar arası sistemsel geçiş yapmak için kullanılacak bir programdır.

- [Proje hakkında araştırma yapmak için](https://docs.github.com/en/copilot/tutorials/migrate-a-project)
- [Projenin Github reposuna ulaşmak için](https://github.com/mert6148/FlaskDjangoproject.git)
- [Yerel dokümantasyon](docs/index.html) (API, Kurulum, Proje Açıklaması)
- [Sistem koruma scripti (PowerShell)](sys/sys_protection.ps1) ve [Batch](src/src_protection.bat)
- [MySQL koruma scripti](sys/mysql_protection.ps1), [Python MySQL test modülü](src/mysql_protection.py), [test](test/test_mysql_protection.py)
- [Front-end otomasyon geçiş aracı](frontend_integration.py)
- [Python kod dökümantasyonu (app/auth ve root)](docs/python_overview.md)

# İletişim
Numara: +90 533 472 75 61
Gmail: mertdoganay437@gmail.com


## Docker ile Çalıştırma

1. `docker compose build`
2. `docker compose up`
3. `http://localhost:9000` adresinden frontend kontrol

## Sanal Ortam (venv) kurulum

Linux:
```bash
bash scripts/setup_venv.sh
source .venv/bin/activate
```

Windows PowerShell:
```powershell
powershell -File scripts/activate_venv.ps1
```

## Test çalıştırma

`pytest test/test_infra.py test/test_mysql_protection.py`

## Flask + Django + Veritabanı + JS + Docker entegrasyon rehberi

1. Python ortamını aktif et

   - Linux:
     ```bash
     bash scripts/setup_venv.sh
     source .venv/bin/activate
     ```
   - Windows:
     ```powershell
     powershell -File scripts/activate_venv.ps1
     ```

2. Gerekli paketleri yükle

   ```bash
   pip install -r requirements.txt
   pip install flask flask-sqlalchemy flask-login django djangorestframework
   ```

3. `auth/main.py` içindeki Flask ve Django fonksiyonlarını kullanarak API başlat

   - Flask modu:
     ```bash
     set MODE=flask
     python auth/main.py
     ```
   - Django modu:
     ```bash
     set MODE=django
     python auth/main.py migrate
     python auth/main.py runserver
     ```

4. `auth/print.py` ile veritabanı tablosu oluşturma, veri ekleme ve `auth/auth_data.json` içine döküm

   ```bash
   python auth/print.py
   ```

5. JavaScript tarafı (frontend entegrasyon örneği)

   - `index.js` veya `app/app.js` içinde API istekleri:

     ```javascript
     async function apiGetKullanicilar(){
       const res = await fetch('/api/kullanicilar');
       return await res.json();
     }

     async function apiCreateUrun(payload){
       const res = await fetch('/api/urunler', {
         method: 'POST',
         headers: {'Content-Type': 'application/json'},
         body: JSON.stringify(payload),
       });
       return await res.json();
     }
     ```

6. Docker ile çalıştır

   - `Dockerfile` ve `docker-compose.yml` hazırlanmışsa:
     ```bash
     docker compose build
     docker compose up -d
     ```
   - Ardından API'ye eriş:
     `http://localhost:9000/api/kullanicilar`

7. Front-End klasörlerine python framework iskeleti kur

   - Bu adım, `app`, `assets`, `src` klasörlerine kolay çalışacak frontend scaffolding ekler.
     ```bash
     python app/fastadmin/api/frameworks/frontend_frameworks.py
     ```
   - `frontend_frameworks_manifest.json` ve `frontend_readme.md` dosyaları oluşturulur.

8. Markdown güncelleme tesbiti:

   - Bu README, talebiniz doğrultusunda Flask/Django + DB + JS + Docker akışını merkezi belge olarak güncelledi.
