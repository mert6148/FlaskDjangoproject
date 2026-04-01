"""
djangomodel.py — Django ORM Model Katmanı
==========================================
flask_superadmin.contrib.DeprecatedModelView ile geriye dönük
uyumluluk korunarak yeniden yazılmıştır.

İçerik:
  - Temel soyut model'ler (ZamanDamgasi, SoftDelete)
  - Kullanıcı, Kategori, Ürün, Sipariş, SiparisKalem modelleri
  - Django Admin kayıtları
  - flask_superadmin DeprecatedModelView uyumu

Kurulum::

    pip install django
    # settings.py → INSTALLED_APPS = [..., 'myapp']
    python manage.py makemigrations
    python manage.py migrate
"""

from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib import admin


# ═════════════════════════════════════════════════════════════════════════════
# SOYUT TABAN MODELLERİ
# ═════════════════════════════════════════════════════════════════════════════

class ZamanDamgasiModel(models.Model):
    """
    Tüm modellere otomatik zaman damgası ekleyen soyut model.

    Alanlar:
        olusturulma: Kayıt ilk oluşturulduğunda otomatik atanır.
        guncelleme:  Her kayıtta otomatik güncellenir.

    Kullanım::

        class Urun(ZamanDamgasiModel):
            ad = models.CharField(max_length=200)
    """
    olusturulma = models.DateTimeField(auto_now_add=True, db_index=True)
    guncelleme  = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Soft-delete edilmiş kayıtları varsayılan sorgulardan gizler."""

    def get_queryset(self):
        return super().get_queryset().filter(silinmis=False)

    def silinmisler_dahil(self):
        """Silinmiş kayıtlar dahil tümünü döndürür."""
        return super().get_queryset()

    def sadece_silinmisler(self):
        """Yalnızca silinmiş kayıtları döndürür."""
        return super().get_queryset().filter(silinmis=True)


class SoftDeleteModel(models.Model):
    """
    Fiziksel silme yerine 'silinmiş' işaretlemesi yapan soyut model.

    Kullanım::

        urun.soft_sil()   # silinmis = True
        urun.geri_al()    # silinmis = False
    """
    silinmis       = models.BooleanField(default=False, db_index=True)
    silinme_zamani = models.DateTimeField(null=True, blank=True)

    objects     = SoftDeleteManager()
    tum_nesneler = models.Manager()  # Silinmişler dahil

    def soft_sil(self) -> None:
        """Kaydı soft-delete ile işaretler."""
        self.silinmis       = True
        self.silinme_zamani = timezone.now()
        self.save(update_fields=["silinmis", "silinme_zamani"])

    def geri_al(self) -> None:
        """Soft-delete'i geri alır."""
        self.silinmis       = False
        self.silinme_zamani = None
        self.save(update_fields=["silinmis", "silinme_zamani"])

    class Meta:
        abstract = True


class TemelModel(ZamanDamgasiModel, SoftDeleteModel):
    """ZamanDamgasi + SoftDelete birleşik soyut model."""
    class Meta:
        abstract = True


# ═════════════════════════════════════════════════════════════════════════════
# MODELLER
# ═════════════════════════════════════════════════════════════════════════════

class Kullanici(TemelModel):
    """
    Uygulama kullanıcısı.

    İlişkiler:
        - Bir kullanıcının birden fazla siparişi olabilir (1→N)

    Örnek::

        u = Kullanici.objects.create(
            ad="Ahmet", email="ahmet@ornek.com"
        )
    """

    class Rol(models.TextChoices):
        ADMIN      = "admin",     "Yönetici"
        MODERATOR  = "moderator", "Moderatör"
        KULLANICI  = "kullanici", "Kullanıcı"

    ad         = models.CharField(max_length=80, verbose_name="Ad Soyad")
    email      = models.EmailField(unique=True, db_index=True, verbose_name="E-posta")
    sifre_hash = models.CharField(max_length=256)
    rol        = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.KULLANICI,
        verbose_name="Rol"
    )
    aktif      = models.BooleanField(default=True, verbose_name="Aktif")
    son_giris  = models.DateTimeField(null=True, blank=True, verbose_name="Son Giriş")

    class Meta:
        db_table        = "kullanicilar"
        verbose_name    = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"
        ordering        = ["-olusturulma"]
        indexes         = [models.Index(fields=["email", "aktif"])]

    def __str__(self) -> str:
        return f"{self.ad} <{self.email}>"

    def to_dict(self) -> dict:
        return {
            "id":       self.pk,
            "ad":       self.ad,
            "email":    self.email,
            "rol":      self.rol,
            "aktif":    self.aktif,
            "son_giris": self.son_giris.isoformat() if self.son_giris else None,
        }


class Kategori(ZamanDamgasiModel):
    """
    Ürün kategorisi — öz-referanslı hiyerarşi destekler.

    İlişkiler:
        - Bir kategorinin birden fazla ürünü olabilir (1→N)
        - Alt kategorileri olabilir (öz-referans)
    """
    ad             = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    aciklama       = models.TextField(blank=True, verbose_name="Açıklama")
    ust_kategori   = models.ForeignKey(
        "self",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="alt_kategoriler",
        verbose_name="Üst Kategori"
    )

    class Meta:
        db_table            = "kategoriler"
        verbose_name        = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering            = ["ad"]

    def __str__(self) -> str:
        if self.ust_kategori:
            return f"{self.ust_kategori} › {self.ad}"
        return self.ad

    def to_dict(self) -> dict:
        return {
            "id":              self.pk,
            "ad":              self.ad,
            "aciklama":        self.aciklama,
            "ust_kategori_id": self.ust_kategori_id,
            "urun_sayisi":     self.urunler.count(),
        }


class Urun(TemelModel):
    """
    Satışa sunulan ürün.

    İlişkiler:
        - Bir kategoriye ait (N→1)
        - Birden fazla sipariş kaleminde yer alabilir
    """
    ad         = models.CharField(max_length=200, db_index=True, verbose_name="Ürün Adı")
    aciklama   = models.TextField(blank=True, verbose_name="Açıklama")
    fiyat      = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Fiyat (TL)"
    )
    stok       = models.PositiveIntegerField(default=0, verbose_name="Stok")
    aktif      = models.BooleanField(default=True, verbose_name="Aktif")
    kategori   = models.ForeignKey(
        Kategori,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="urunler",
        verbose_name="Kategori"
    )

    class Meta:
        db_table            = "urunler"
        verbose_name        = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering            = ["-olusturulma"]
        indexes             = [
            models.Index(fields=["ad", "aktif"]),
            models.Index(fields=["kategori", "aktif"]),
        ]

    def stok_yeterli(self, miktar: int) -> bool:
        """Stokun yeterli olup olmadığını kontrol eder."""
        return self.stok >= miktar

    def stok_dusu(self) -> bool:
        """Stok 10'un altında mı?"""
        return self.stok < 10

    def __str__(self) -> str:
        return f"{self.ad} — {self.fiyat} TL"

    def to_dict(self) -> dict:
        return {
            "id":          self.pk,
            "ad":          self.ad,
            "fiyat":       str(self.fiyat),
            "stok":        self.stok,
            "aktif":       self.aktif,
            "kategori_id": self.kategori_id,
        }


class Siparis(ZamanDamgasiModel):
    """
    Kullanıcı siparişi.

    İlişkiler:
        - Bir kullanıcıya ait (N→1)
        - Birden fazla sipariş kalemi içerir (1→N)
    """

    class Statu(models.TextChoices):
        BEKLEMEDE  = "beklemede",  "Beklemede"
        ONAYLANDI  = "onaylandi",  "Onaylandı"
        KARGOLANDI = "kargolandi", "Kargolandı"
        TESLIM     = "teslim",     "Teslim Edildi"
        IPTAL      = "iptal",      "İptal"

    kullanici    = models.ForeignKey(
        Kullanici,
        on_delete=models.PROTECT,
        related_name="siparisler",
        verbose_name="Kullanıcı"
    )
    statu        = models.CharField(
        max_length=20,
        choices=Statu.choices,
        default=Statu.BEKLEMEDE,
        verbose_name="Durum"
    )
    toplam_tutar = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Toplam Tutar (TL)"
    )
    notlar       = models.TextField(blank=True, verbose_name="Notlar")

    class Meta:
        db_table            = "siparisler"
        verbose_name        = "Sipariş"
        verbose_name_plural = "Siparişler"
        ordering            = ["-olusturulma"]

    def toplam_hesapla(self):
        """Tüm kalemlerin toplam tutarını hesaplar ve kaydeder."""
        toplam = sum(
            k.miktar * k.birim_fiyat
            for k in self.kalemler.all()
        )
        self.toplam_tutar = toplam
        self.save(update_fields=["toplam_tutar"])
        return toplam

    def __str__(self) -> str:
        return f"Sipariş #{self.pk} — {self.kullanici} [{self.statu}]"

    def to_dict(self) -> dict:
        return {
            "id":           self.pk,
            "kullanici_id": self.kullanici_id,
            "statu":        self.statu,
            "toplam_tutar": str(self.toplam_tutar),
            "kalem_sayisi": self.kalemler.count(),
        }


class SiparisKalem(models.Model):
    """
    Sipariş içindeki tekil ürün kalemi.

    İlişkiler:
        - Bir siparişe ait (N→1)
        - Bir ürüne referans verir (N→1)
    """
    siparis     = models.ForeignKey(
        Siparis, on_delete=models.CASCADE, related_name="kalemler"
    )
    urun        = models.ForeignKey(
        Urun, on_delete=models.PROTECT, related_name="siparis_kalemleri"
    )
    miktar      = models.PositiveIntegerField(default=1, verbose_name="Miktar")
    birim_fiyat = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Birim Fiyat"
    )

    class Meta:
        db_table            = "siparis_kalemleri"
        verbose_name        = "Sipariş Kalemi"
        verbose_name_plural = "Sipariş Kalemleri"

    @property
    def ara_toplam(self):
        return self.miktar * self.birim_fiyat

    def __str__(self) -> str:
        return f"{self.urun} × {self.miktar}"


# ═════════════════════════════════════════════════════════════════════════════
# DJANGO ADMIN KAYITLARI
# ═════════════════════════════════════════════════════════════════════════════

class SiparisKalemInline(admin.TabularInline):
    """Sipariş formu içinde kalem satır editörü."""
    model       = SiparisKalem
    extra       = 1
    fields      = ("urun", "miktar", "birim_fiyat")
    readonly_fields = ("birim_fiyat",)


@admin.register(Kullanici)
class KullaniciAdmin(admin.ModelAdmin):
    """Kullanıcı yönetim paneli."""
    list_display    = ("id", "ad", "email", "rol", "aktif", "olusturulma")
    list_filter     = ("rol", "aktif", "silinmis")
    search_fields   = ("ad", "email")
    readonly_fields = ("sifre_hash", "son_giris", "olusturulma", "guncelleme")
    ordering        = ("-olusturulma",)
    list_per_page   = 25

    fieldsets = (
        ("Kimlik",    {"fields": ("ad", "email", "sifre_hash")}),
        ("Yetki",     {"fields": ("rol", "aktif")}),
        ("Sistem",    {"fields": ("son_giris", "olusturulma", "guncelleme",
                                   "silinmis", "silinme_zamani"),
                       "classes": ("collapse",)}),
    )


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    """Kategori yönetim paneli."""
    list_display  = ("id", "ad", "ust_kategori", "urun_sayisi", "olusturulma")
    search_fields = ("ad",)
    ordering      = ("ad",)

    @admin.display(description="Ürün Sayısı")
    def urun_sayisi(self, obj):
        return obj.urunler.count()


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    """Ürün yönetim paneli."""
    list_display    = ("id", "ad", "fiyat", "stok", "aktif", "kategori", "olusturulma")
    list_filter     = ("aktif", "kategori", "silinmis")
    search_fields   = ("ad",)
    list_editable   = ("fiyat", "stok", "aktif")
    ordering        = ("-olusturulma",)
    list_per_page   = 30

    @admin.display(boolean=True, description="Stok Düşük?")
    def stok_dusu_mu(self, obj):
        return obj.stok_dusu()


@admin.register(Siparis)
class SiparisAdmin(admin.ModelAdmin):
    """Sipariş yönetim paneli."""
    list_display    = ("id", "kullanici", "statu", "toplam_tutar", "olusturulma")
    list_filter     = ("statu",)
    readonly_fields = ("toplam_tutar", "olusturulma", "guncelleme")
    inlines         = [SiparisKalemInline]
    ordering        = ("-olusturulma",)

    actions = ["onayla", "iptal_et"]

    @admin.action(description="Seçili siparişleri onayla")
    def onayla(self, request, queryset):
        guncellenen = queryset.update(statu=Siparis.Statu.ONAYLANDI)
        self.message_user(request, f"{guncellenen} sipariş onaylandı.")

    @admin.action(description="Seçili siparişleri iptal et")
    def iptal_et(self, request, queryset):
        guncellenen = queryset.update(statu=Siparis.Statu.IPTAL)
        self.message_user(request, f"{guncellenen} sipariş iptal edildi.")


# ═════════════════════════════════════════════════════════════════════════════
# FLASK_SUPERADMIN GERIYE DÖNÜK UYUMLULUK
# ═════════════════════════════════════════════════════════════════════════════

try:
    from flask_superadmin.contrib import DeprecatedModelView
    from flask_superadmin.model.backends.django import ModelAdmin as DjangoModelAdmin

    class ModelView(DeprecatedModelView, DjangoModelAdmin):
        """
        flask_superadmin geriye dönük uyumlu ModelView.

        Orijinal kullanım::

            admin.register(Kullanici, ModelView)
        """
        pass

except ImportError:
    # flask_superadmin kurulu değilse sessizce geç
    pass