# Proje hakkında

Flask ve Django ile oluşturulan bu proje Python ve Javascript ile yazılmış olup uygulamalar arası sistemsel geçiş yapmak için kullanılacak bir programdır.

- [Proje hakkında araştırma yapmak için](https://docs.github.com/en/copilot/tutorials/migrate-a-project)
- [Projenin Github reposuna ulaşmak için](https://github.com/mert6148/FlaskDjangoproject.git)
- [Yerel dokümantasyon](docs/index.html) (API, Kurulum, Proje Açıklaması)
- [Sistem koruma scripti (PowerShell)](sys/sys_protection.ps1) ve [Batch](src/src_protection.bat)
- [MySQL koruma scripti](sys/mysql_protection.ps1), [Python MySQL test modülü](src/mysql_protection.py), [test](test/test_mysql_protection.py)
- [Front-end otomasyon geçiş aracı](frontend_integration.py)
- [Python kod dökümantasyonu (app/auth ve root)](docs/python_overview.md)

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

# İletişim
Numara: +90 533 472 75 61
Gmail: mertdoganay437@gmail.com
