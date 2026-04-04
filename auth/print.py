import json
import os
import pathlib
import sys
from sqlalchemy import create_engine, text


def get_database_url() -> str:
    """Aynı veritabanı URL'sini main.py ile paylaşmak için kullan."""
    mysql_url = os.environ.get("MYSQL_DATABASE_URL")
    sqlite_url = "sqlite:///flask_app.db"
    return mysql_url or os.environ.get("DATABASE_URL", sqlite_url)


def ensure_tables_exist(engine):
    """Flask uygulamasındaki tabloların var olduğundan emin ol (ilk başlangıç için)."""
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS kullanici (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad VARCHAR(80) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            aktif BOOLEAN DEFAULT 1
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS urun (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim VARCHAR(120) NOT NULL,
            fiyat FLOAT NOT NULL,
            stok INTEGER DEFAULT 0,
            kullanici_id INTEGER NOT NULL,
            FOREIGN KEY(kullanici_id) REFERENCES kullanici(id)
        );
        """,
    ]
    with engine.begin() as conn:
        for stmt in ddl_statements:
            conn.execute(text(stmt))


def read_data_from_db(engine):
    """Veritabanındaki kullanici ve urun verilerini çek."""
    with engine.connect() as conn:
        kullanicilar = [dict(row._mapping) for row in conn.execute(text("SELECT * FROM kullanici WHERE aktif=1"))]
        urunler = [dict(row._mapping) for row in conn.execute(text("SELECT * FROM urun"))]
    return {"kullanicilar": kullanicilar, "urunler": urunler}


def dump_to_auth_folder(data, output_filename="auth_data.json"):
    """Veriyi auth klasörüne JSON olarak kaydet."""
    auth_dir = pathlib.Path(__file__).resolve().parent
    auth_dir.mkdir(parents=True, exist_ok=True)
    dst = auth_dir / output_filename
    with dst.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return str(dst)


def add_sample_data(engine):
    """Çalışma için bazı örnek veriler ekle."""
    with engine.begin() as conn:
        mevcut = conn.execute(text("SELECT COUNT(*) as c FROM kullanici")).scalar_one()
        if mevcut == 0:
            conn.execute(text("INSERT INTO kullanici (ad, email, aktif) VALUES (:ad, :email, 1)"), [
                {"ad": "Alper", "email": "alper@example.com"},
                {"ad": "Melis", "email": "melis@example.com"},
            ])
            conn.execute(text("INSERT INTO urun (isim, fiyat, stok, kullanici_id) VALUES (:isim, :fiyat, :stok, :kullanici_id)"), [
                {"isim": "Kalem", "fiyat": 3.5, "stok": 100, "kullanici_id": 1},
                {"isim": "Defter", "fiyat": 12.0, "stok": 50, "kullanici_id": 2},
            ])


def main():
    """Ana komut dosyası akışı."""
    db_url = get_database_url()
    engine = create_engine(db_url, echo=False, future=True)

    print(f"Veritabanı URL'si: {db_url}")
    ensure_tables_exist(engine)
    add_sample_data(engine)
    data = read_data_from_db(engine)
    output_file = dump_to_auth_folder(data)
    print(f"Veri başarıyla aktarılıp kaydedildi: {output_file}")


if __name__ == "__main__":
    main()