"""
db_config.py — Veritabanı Konfigürasyon Modülü
SQLite (geliştirme) → PostgreSQL (üretim) geçişi destekli.
app.py → create_app() tarafından import edilir.
"""

import os
from dataclasses import dataclass, field


@dataclass
class DBKonfigurasyonu:
    """
    Veritabanı bağlantı ayarları.
    Ortam değişkenlerinden otomatik yüklenir.
    """

    # Bağlantı URI — ortama göre seçilir
    uri: str = field(default_factory=lambda: _uri_sec())

    # Bağlantı havuzu
    pool_size:         int  = int(os.environ.get("DB_POOL_SIZE", "5"))
    max_overflow:      int  = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
    pool_timeout:      int  = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
    pool_recycle:      int  = int(os.environ.get("DB_POOL_RECYCLE", "300"))
    pool_pre_ping:     bool = True

    # SQLite için özel ayar
    check_same_thread: bool = True

    def sqlalchemy_ayarlari(self) -> dict:
        """Flask app.config'e doğrudan aktarılabilir sözlük."""
        engine_opts: dict = {
            "pool_pre_ping": self.pool_pre_ping,
        }

        if self.uri.startswith("sqlite"):
            # SQLite: bağlantı havuzu gerekmez
            engine_opts["connect_args"] = {"check_same_thread": False}
        else:
            # PostgreSQL / MySQL: havuz ayarları
            engine_opts.update({
                "pool_size":    self.pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
            })

        return {
            "SQLALCHEMY_DATABASE_URI":        self.uri,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SQLALCHEMY_ENGINE_OPTIONS":      engine_opts,
        }

    @property
    def ozet(self) -> str:
        """Şifre gizlenerek bağlantı özeti."""
        if "://" in self.uri:
            parcalar = self.uri.split("://", 1)
            return f"{parcalar[0]}://***"
        return self.uri


def _uri_sec() -> str:
    """Ortama göre doğru DB URI'sını seçer."""
    # 1. Açıkça verilmişse kullan
    if db_url := os.environ.get("DATABASE_URL"):
        # Heroku/Railway eski postgres:// formatını düzelt
        return db_url.replace("postgres://", "postgresql://", 1)

    ortam = os.environ.get("FLASK_ENV", "development")

    if ortam == "production":
        raise EnvironmentError(
            "Üretim ortamında DATABASE_URL ortam değişkeni zorunludur!\n"
            "Örnek: DATABASE_URL=postgresql://kullanici:sifre@host:5432/dbadi"
        )

    # Geliştirme: SQLite
    db_yolu = os.environ.get("SQLITE_PATH", "mesajlar.db")
    return f"sqlite:///{db_yolu}"


# ── Hazır konfigürasyonlar ────────────────────────────────────────────────────

GELISTIRME = DBKonfigurasyonu(
    uri=f"sqlite:///{os.environ.get('SQLITE_PATH', 'mesajlar.db')}",
)

URETIM = DBKonfigurasyonu(
    uri=os.environ.get("DATABASE_URL", ""),
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

TEST = DBKonfigurasyonu(
    uri="sqlite:///:memory:",
)

# ── Ortama göre otomatik seç ──────────────────────────────────────────────────
_ORTAM_HARITASI = {
    "development": GELISTIRME,
    "production":  URETIM,
    "testing":     TEST,
}


def aktif_konfigurasyon() -> DBKonfigurasyonu:
    ortam = os.environ.get("FLASK_ENV", "development")
    return _ORTAM_HARITASI.get(ortam, GELISTIRME)


if __name__ == "__main__":
    k = aktif_konfigurasyon()
    print(f"Aktif DB konfigürasyonu: {k.ozet}")
    print(f"Ayarlar: {k.sqlalchemy_ayarlari()}")
