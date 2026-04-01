"""
flaskmodel.py — Flask + SQLAlchemy Model Katmanı
=================================================
Proje: flask_superadmin uyumlu model arka ucu

İçerik:
  - Temel model mixin'leri (zaman damgası, soft delete, denetim)
  - Kullanıcı, Kategori, Ürün, Sipariş modelleri
  - flask_superadmin ModelAdmin entegrasyonu
  - Fabrika fonksiyonu: create_flask_models()
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, Enum, ForeignKey


# ═════════════════════════════════════════════════════════════════════════════
# VERİTABANI NESNE TABANL
# ═════════════════════════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """SQLAlchemy 2.0 deklaratif taban sınıfı."""
    pass


db = SQLAlchemy(model_class=Base)


# ═════════════════════════════════════════════════════════════════════════════
# MİXİN'LER — yeniden kullanılabilir davranış parçaları
# ═════════════════════════════════════════════════════════════════════════════

class ZamanDamgasiMixin:
    """
    Tüm modellere otomatik oluşturma ve güncelleme zaman damgası ekler.

    Kullanım::

        class Urun(ZamanDamgasiMixin, db.Model):
            ...
    """
    olusturulma: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    guncelleme: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SoftDeleteMixin:
    """
    Kayıtları fiziksel olarak silmek yerine 'silinmiş' olarak işaretler.

    Kullanım::

        kayit.soft_sil()   # silinmis = True
        kayit.geri_al()    # silinmis = False
    """
    silinmis: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    silinme_zamani: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def soft_sil(self) -> None:
        """Kaydı soft-delete ile işaretler."""
        self.silinmis = True
        self.silinme_zamani = datetime.utcnow()

    def geri_al(self) -> None:
        """Soft-delete'i geri alır."""
        self.silinmis = False
        self.silinme_zamani = None


class TemelMixin(ZamanDamgasiMixin, SoftDeleteMixin):
    """ZamanDamgasi + SoftDelete birleşik mixin."""
    pass


# ═════════════════════════════════════════════════════════════════════════════
# ENUM'LAR
# ═════════════════════════════════════════════════════════════════════════════

class KullaniciRol(str, enum.Enum):
    """Kullanıcı rolleri."""
    ADMIN      = "admin"
    MODERATOR  = "moderator"
    KULLANICI  = "kullanici"


class SiparisStatu(str, enum.Enum):
    """Sipariş durumları."""
    BEKLEMEDE  = "beklemede"
    ONAYLANDI  = "onaylandi"
    KARGOLANDI = "kargolandi"
    TESLIM     = "teslim_edildi"
    IPTAL      = "iptal"


# ═════════════════════════════════════════════════════════════════════════════
# MODELLER
# ═════════════════════════════════════════════════════════════════════════════

class Kullanici(TemelMixin, db.Model):
    """
    Uygulama kullanıcısı.

    İlişkiler:
        - Bir kullanıcının birden fazla siparişi olabilir (1→N)

    Örnek::

        u = Kullanici(ad="Ahmet", email="ahmet@ornek.com")
        db.session.add(u)
        db.session.commit()
    """
    __tablename__ = "kullanicilar"
    __table_args__ = {"comment": "Uygulama kullanıcıları"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    sifre_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    rol: Mapped[KullaniciRol] = mapped_column(
        Enum(KullaniciRol), default=KullaniciRol.KULLANICI, nullable=False
    )
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    son_giris: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # İlişkiler
    siparisler: Mapped[list["Siparis"]] = relationship(
        "Siparis", back_populates="kullanici", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id":       self.id,
            "ad":       self.ad,
            "email":    self.email,
            "rol":      self.rol.value,
            "aktif":    self.aktif,
            "son_giris": self.son_giris.isoformat() if self.son_giris else None,
        }

    def __repr__(self) -> str:
        return f"<Kullanici #{self.id} {self.email!r}>"


class Kategori(ZamanDamgasiMixin, db.Model):
    """
    Ürün kategorisi — öz-referanslı hiyerarşik yapı destekler.

    İlişkiler:
        - Bir kategorinin birden fazla ürünü olabilir (1→N)
        - Bir kategorinin alt kategorileri olabilir (öz-referans)
    """
    __tablename__ = "kategoriler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ust_kategori_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kategoriler.id"), nullable=True
    )

    # Öz-referanslı ilişki
    ust_kategori: Mapped[Optional["Kategori"]] = relationship(
        "Kategori", remote_side="Kategori.id", back_populates="alt_kategoriler"
    )
    alt_kategoriler: Mapped[list["Kategori"]] = relationship(
        "Kategori", back_populates="ust_kategori"
    )
    urunler: Mapped[list["Urun"]] = relationship("Urun", back_populates="kategori")

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "ad":              self.ad,
            "aciklama":        self.aciklama,
            "ust_kategori_id": self.ust_kategori_id,
            "urun_sayisi":     len(self.urunler),
        }

    def __repr__(self) -> str:
        return f"<Kategori #{self.id} {self.ad!r}>"


class Urun(TemelMixin, db.Model):
    """
    Satışa sunulan ürün.

    İlişkiler:
        - Bir kategoriye ait (N→1)
        - Birden fazla sipariş kaleminde yer alabilir (N→N, SiparisKalem üzerinden)
    """
    __tablename__ = "urunler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fiyat: Mapped[float] = mapped_column(Float, nullable=False)
    stok: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    kategori_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kategoriler.id"), nullable=True
    )

    # İlişkiler
    kategori: Mapped[Optional[Kategori]] = relationship("Kategori", back_populates="urunler")
    siparis_kalemleri: Mapped[list["SiparisKalem"]] = relationship(
        "SiparisKalem", back_populates="urun"
    )

    def stok_yeterli(self, miktar: int) -> bool:
        """Stokun yeterli olup olmadığını kontrol eder."""
        return self.stok >= miktar

    def stok_dusu(self) -> bool:
        """Stok 10'un altında mı?"""
        return self.stok < 10

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "ad":          self.ad,
            "fiyat":       self.fiyat,
            "stok":        self.stok,
            "aktif":       self.aktif,
            "kategori_id": self.kategori_id,
        }

    def __repr__(self) -> str:
        return f"<Urun #{self.id} {self.ad!r} {self.fiyat} TL>"


class Siparis(ZamanDamgasiMixin, db.Model):
    """
    Kullanıcı siparişi.

    İlişkiler:
        - Bir kullanıcıya ait (N→1)
        - Birden fazla sipariş kalemi içerir (1→N)
    """
    __tablename__ = "siparisler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kullanici_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=False, index=True
    )
    statu: Mapped[SiparisStatu] = mapped_column(
        Enum(SiparisStatu), default=SiparisStatu.BEKLEMEDE, nullable=False
    )
    toplam_tutar: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notlar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # İlişkiler
    kullanici: Mapped[Kullanici] = relationship("Kullanici", back_populates="siparisler")
    kalemler: Mapped[list["SiparisKalem"]] = relationship(
        "SiparisKalem", back_populates="siparis", cascade="all, delete-orphan"
    )

    def toplam_hesapla(self) -> float:
        """Tüm kalemlerin toplam tutarını hesaplar."""
        return sum(k.miktar * k.birim_fiyat for k in self.kalemler)

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "kullanici_id": self.kullanici_id,
            "statu":        self.statu.value,
            "toplam_tutar": self.toplam_tutar,
            "kalem_sayisi": len(self.kalemler),
        }

    def __repr__(self) -> str:
        return f"<Siparis #{self.id} [{self.statu.value}]>"


class SiparisKalem(db.Model):
    """
    Sipariş içindeki tekil ürün kalemi (N→N köprü tablosu).
    """
    __tablename__ = "siparis_kalemleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    siparis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("siparisler.id"), nullable=False
    )
    urun_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("urunler.id"), nullable=False
    )
    miktar: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    birim_fiyat: Mapped[float] = mapped_column(Float, nullable=False)

    # İlişkiler
    siparis: Mapped[Siparis] = relationship("Siparis", back_populates="kalemler")
    urun: Mapped[Urun] = relationship("Urun", back_populates="siparis_kalemleri")

    @property
    def ara_toplam(self) -> float:
        return self.miktar * self.birim_fiyat

    def __repr__(self) -> str:
        return f"<SiparisKalem siparis={self.siparis_id} urun={self.urun_id} x{self.miktar}>"


# ═════════════════════════════════════════════════════════════════════════════
# FLASK_SUPERADMIN MODEL ADMİN ENTEGRASYONU
# ═════════════════════════════════════════════════════════════════════════════

try:
    from flask_superadmin.contrib import DeprecatedModelView
    from flask_superadmin.model.backends.sqlalchemy import ModelAdmin as SQLAModelAdmin

    class ModelView(DeprecatedModelView, SQLAModelAdmin):
        """Geriye dönük uyumlu ModelView (flask_superadmin.contrib)."""
        pass

    class KullaniciAdmin(SQLAModelAdmin):
        """Kullanıcı yönetimi için admin görünümü."""
        column_list        = ("id", "ad", "email", "rol", "aktif", "olusturulma")
        column_searchable  = ("ad", "email")
        column_filters     = ("rol", "aktif", "silinmis")
        column_sortable    = ("id", "ad", "email", "olusturulma")
        form_excluded_cols = ("sifre_hash", "silinmis", "silinme_zamani")

    class UrunAdmin(SQLAModelAdmin):
        """Ürün yönetimi için admin görünümü."""
        column_list       = ("id", "ad", "fiyat", "stok", "aktif", "kategori")
        column_searchable = ("ad",)
        column_filters    = ("aktif", "kategori_id", "silinmis")
        column_sortable   = ("id", "ad", "fiyat", "stok")

    class SiparisAdmin(SQLAModelAdmin):
        """Sipariş yönetimi için admin görünümü."""
        column_list      = ("id", "kullanici", "statu", "toplam_tutar", "olusturulma")
        column_filters   = ("statu",)
        column_sortable  = ("id", "toplam_tutar", "olusturulma")
        can_create       = False

    ADMIN_VIEWS = [
        (Kullanici, KullaniciAdmin),
        (Urun,      UrunAdmin),
        (Siparis,   SiparisAdmin),
        (Kategori,  SQLAModelAdmin),
    ]

except ImportError:
    ADMIN_VIEWS = []


# ═════════════════════════════════════════════════════════════════════════════
# FABRIKA FONKSİYONU
# ═════════════════════════════════════════════════════════════════════════════

def create_flask_models(app: Flask) -> SQLAlchemy:
    """
    Flask uygulamasına SQLAlchemy'yi bağlar ve tabloları oluşturur.

    Kullanım::

        from flask import Flask
        from flaskmodel import create_flask_models, db

        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
        create_flask_models(app)

    :param app: Flask uygulama nesnesi.
    :returns: Başlatılmış SQLAlchemy nesnesi.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return db


if __name__ == "__main__":
    # Hızlı test
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_flask.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    create_flask_models(app)
    print("Flask modelleri başarıyla oluşturuldu.")
    print("Tablolar:", [t for t in Base.metadata.tables.keys()])