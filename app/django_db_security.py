"""
django_db_security.py — Django Veritabanı Koruma Katmanı
Row-level security, şifreli alanlar, denetim izleri,
sorgu filtreleme, bağlantı havuzu koruması.
"""

import os
import re
import hmac
import hashlib
import logging
import secrets
from base64 import b64encode, b64decode
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Kriptografi: pip install cryptography ─────────────────────────────────────
try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ── Django importları ─────────────────────────────────────────────────────────
try:
    import django
    from django.db import models
    from django.db.models import Q, Manager, QuerySet
    from django.contrib.auth.hashers import make_password, check_password
    from django.utils import timezone
    from django.core.exceptions import PermissionDenied, ValidationError
    from django.db import connection
    from django.conf import settings
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False


# ═════════════════════════════════════════════════════════════════════════════
# 1. ŞİFRELİ ALAN (FIELD-LEVEL ENCRYPTION)
# ═════════════════════════════════════════════════════════════════════════════

class SifreliAlanYoneticisi:
    """Fernet simetrik şifreleme ile alan düzeyinde koruma."""

    def __init__(self, anahtar: bytes | None = None):
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography kurulu değil: pip install cryptography")
        if anahtar is None:
            anahtar = os.environ.get("DB_ENCRYPTION_KEY", "").encode()
            if not anahtar:
                anahtar = Fernet.generate_key()
                logger.warning("Şifreleme anahtarı ortam değişkeninden alınamadı; geçici anahtar üretildi")
        self._fernet = Fernet(anahtar)

    def sifrele(self, deger: str) -> str:
        """Metni şifrele → base64 string."""
        return b64encode(self._fernet.encrypt(deger.encode("utf-8"))).decode("utf-8")

    def coz(self, sifreli: str) -> str:
        """base64 şifreli metni çöz."""
        try:
            return self._fernet.decrypt(b64decode(sifreli)).decode("utf-8")
        except (InvalidToken, Exception) as e:
            logger.error(f"Şifre çözme hatası: {e}")
            raise ValueError("Şifre çözülemedi — veri bozuk veya anahtar yanlış")

    def alan_imzala(self, deger: str, gizli: str) -> str:
        """HMAC-SHA256 ile alan bütünlüğünü imzala."""
        return hmac.new(
            gizli.encode("utf-8"),
            deger.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def imza_dogrula(self, deger: str, imza: str, gizli: str) -> bool:
        beklenen = self.alan_imzala(deger, gizli)
        return hmac.compare_digest(beklenen, imza)


# ═════════════════════════════════════════════════════════════════════════════
# 2. DENETİM İZİ MİXİN (AUDIT TRAIL)
# ═════════════════════════════════════════════════════════════════════════════

if DJANGO_AVAILABLE:

    class DenetimIziMixin(models.Model):
        """Tüm modellere otomatik denetim alanları ekler."""

        olusturulma   = models.DateTimeField(auto_now_add=True, db_index=True)
        guncelleme    = models.DateTimeField(auto_now=True)
        olusturan_id  = models.IntegerField(null=True, blank=True, db_index=True)
        guncelleyen_id = models.IntegerField(null=True, blank=True)
        silinmis      = models.BooleanField(default=False, db_index=True)
        silinme_zamani = models.DateTimeField(null=True, blank=True)

        class Meta:
            abstract = True

        def soft_sil(self, silen_id: int | None = None) -> None:
            """Kayıtı fiziksel silmek yerine işaretle."""
            self.silinmis      = True
            self.silinme_zamani = timezone.now()
            self.guncelleyen_id = silen_id
            self.save(update_fields=["silinmis", "silinme_zamani", "guncelleyen_id"])

        def geri_yukle(self) -> None:
            """Soft-silinen kaydı geri al."""
            self.silinmis      = False
            self.silinme_zamani = None
            self.save(update_fields=["silinmis", "silinme_zamani"])


    # ── Denetim Olayı Modeli ──────────────────────────────────────────────────
    class DenetimOlayi(models.Model):
        """Her veri değişikliğini takip eder."""

        EYLEMLER = [
            ("CREATE", "Oluşturma"),
            ("UPDATE", "Güncelleme"),
            ("DELETE", "Silme"),
            ("VIEW",   "Görüntüleme"),
            ("LOGIN",  "Giriş"),
            ("LOGOUT", "Çıkış"),
            ("FAIL",   "Başarısız İşlem"),
        ]

        tablo_adi   = models.CharField(max_length=100, db_index=True)
        kayit_id    = models.IntegerField(null=True, db_index=True)
        eylem       = models.CharField(max_length=20, choices=EYLEMLER, db_index=True)
        kullanici_id = models.IntegerField(null=True, db_index=True)
        ip_adresi   = models.GenericIPAddressField(null=True)
        eski_deger  = models.JSONField(null=True, blank=True)
        yeni_deger  = models.JSONField(null=True, blank=True)
        degisen_alanlar = models.JSONField(default=list)
        zaman       = models.DateTimeField(auto_now_add=True, db_index=True)
        aciklama    = models.TextField(blank=True)

        class Meta:
            app_label = "auth"
            db_table  = "denetim_olaylari"
            ordering  = ["-zaman"]
            indexes   = [
                models.Index(fields=["tablo_adi", "kayit_id"]),
                models.Index(fields=["kullanici_id", "zaman"]),
            ]

        @classmethod
        def kaydet(
            cls,
            tablo: str,
            eylem: str,
            kayit_id: int | None = None,
            kullanici_id: int | None = None,
            ip: str | None = None,
            eski: dict | None = None,
            yeni: dict | None = None,
            aciklama: str = "",
        ) -> "DenetimOlayi":
            degisen = (
                [k for k in set(list((eski or {}).keys()) + list((yeni or {}).keys()))
                 if (eski or {}).get(k) != (yeni or {}).get(k)]
                if eski and yeni else []
            )
            return cls.objects.create(
                tablo_adi=tablo, kayit_id=kayit_id, eylem=eylem,
                kullanici_id=kullanici_id, ip_adresi=ip,
                eski_deger=eski, yeni_deger=yeni,
                degisen_alanlar=degisen, aciklama=aciklama,
            )


    # ═══════════════════════════════════════════════════════════════════════════
    # 3. GÜVENLİ SORGU YÖNETİCİSİ (SAFE QUERY MANAGER)
    # ═══════════════════════════════════════════════════════════════════════════

    class SilinmeyenlerManager(Manager):
        """Soft-silinmiş kayıtları otomatik filtreler."""

        def get_queryset(self) -> QuerySet:
            return super().get_queryset().filter(silinmis=False)

        def silinmisler_dahil(self) -> QuerySet:
            return super().get_queryset()

        def sadece_silinmisler(self) -> QuerySet:
            return super().get_queryset().filter(silinmis=True)


    class SatirDuzeyiGuvenlikManager(Manager):
        """Satır düzeyinde erişim denetimi."""

        def __init__(self, kullanici_id_alani: str = "kullanici_id"):
            super().__init__()
            self._kullanici_id_alani = kullanici_id_alani
            self._mevcut_kullanici_id: int | None = None

        def kullanici_icin(self, kullanici_id: int) -> "SatirDuzeyiGuvenlikManager":
            mgr = self.__class__(self._kullanici_id_alani)
            mgr.model = self.model
            mgr._mevcut_kullanici_id = kullanici_id
            return mgr

        def get_queryset(self) -> QuerySet:
            qs = super().get_queryset()
            if self._mevcut_kullanici_id is not None:
                qs = qs.filter(**{self._kullanici_id_alani: self._mevcut_kullanici_id})
            return qs


    # ═══════════════════════════════════════════════════════════════════════════
    # 4. VERİTABANI GÜVENLİK KONTROL ARACI
    # ═══════════════════════════════════════════════════════════════════════════

    class DBGuvenlikKontrolcu:
        """Veritabanı bağlantısı ve şema güvenlik denetimleri."""

        @staticmethod
        def ham_sorgu_denetle(sorgu: str) -> tuple[bool, list[str]]:
            """Ham SQL sorgusunu SQL enjeksiyonu açısından inceler."""
            tehlikeli = re.compile(
                r"(--|;|/\*|\*/|xp_|EXEC\s*\(|INTO\s+OUTFILE|LOAD_FILE"
                r"|\bDROP\b|\bTRUNCATE\b|\bALTER\b|\bGRANT\b|\bREVOKE\b"
                r"|\bINFORMATION_SCHEMA\b|\bSYSTEM_USER\b|\bUSER\s*\(\s*\))",
                re.IGNORECASE,
            )
            uyarilar = []
            for eslesme in tehlikeli.finditer(sorgu):
                uyarilar.append(f"Tehlikeli ifade: '{eslesme.group()}' konum {eslesme.start()}")
            return (len(uyarilar) == 0), uyarilar

        @staticmethod
        def parametre_sayisi_dogrula(sorgu: str, parametreler: tuple | list) -> bool:
            """Parametre sayısını placeholder sayısıyla karşılaştırır."""
            ph_sayisi = sorgu.count("%s") + sorgu.count("?")
            return ph_sayisi == len(parametreler)

        @staticmethod
        def guvenli_ham_calistir(sorgu: str, parametreler: tuple = ()) -> list:
            """Denetimden geçirilmiş ham sorgu çalıştırır."""
            temiz, uyarilar = DBGuvenlikKontrolcu.ham_sorgu_denetle(sorgu)
            if not temiz:
                raise PermissionDenied(f"Tehlikeli SQL engellendi: {uyarilar}")
            if not DBGuvenlikKontrolcu.parametre_sayisi_dogrula(sorgu, parametreler):
                raise ValueError("Parametre sayısı uyuşmuyor")
            with connection.cursor() as cur:
                cur.execute(sorgu, parametreler)
                return cur.fetchall()

        @staticmethod
        def tablo_istatistikleri() -> dict:
            """SQLite için basit tablo istatistikleri."""
            try:
                with connection.cursor() as cur:
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tablolar = [r[0] for r in cur.fetchall()]
                istatistikler = {}
                for tablo in tablolar:
                    with connection.cursor() as cur:
                        cur.execute(f"SELECT COUNT(*) FROM {tablo}")  # noqa: S608
                        istatistikler[tablo] = cur.fetchone()[0]
                return istatistikler
            except Exception as e:
                logger.error(f"İstatistik hatası: {e}")
                return {}


    # ═══════════════════════════════════════════════════════════════════════════
    # 5. GÜVENLİ MODEL TABANI (BASE MODEL)
    # ═══════════════════════════════════════════════════════════════════════════

    class GuvenliModelTabani(DenetimIziMixin):
        """Tüm güvenlik katmanlarını birleştiren soyut model tabanı."""

        objects      = SilinmeyenlerManager()
        tum_nesneler = Manager()  # Silinmişler dahil erişim

        class Meta:
            abstract = True

        def kaydet_denetim(
            self,
            eylem: str,
            kullanici_id: int | None = None,
            ip: str | None = None,
            eski_durum: dict | None = None,
        ) -> None:
            DenetimOlayi.kaydet(
                tablo        = self.__class__._meta.db_table,
                eylem        = eylem,
                kayit_id     = self.pk,
                kullanici_id = kullanici_id,
                ip           = ip,
                eski         = eski_durum,
                yeni         = self._mevcut_dict(),
            )

        def _mevcut_dict(self) -> dict:
            """Model alanlarını dict olarak döndürür (hassas alanlar hariç)."""
            hassas = {"sifre", "sifre_hash", "sifre_tuzu", "token", "kart_no"}
            return {
                f.name: str(getattr(self, f.name, ""))
                for f in self.__class__._meta.get_fields()
                if hasattr(f, "name") and f.name not in hassas
            }

        def guvenli_sil(self, kullanici_id: int | None = None, ip: str | None = None) -> None:
            self.kaydet_denetim("DELETE", kullanici_id, ip, self._mevcut_dict())
            self.soft_sil(silen_id=kullanici_id)

        def guvenli_kaydet(
            self,
            kullanici_id: int | None = None,
            ip: str | None = None,
            *args, **kwargs
        ) -> None:
            eylem = "UPDATE" if self.pk else "CREATE"
            eski  = None
            if self.pk:
                try:
                    eski = self.__class__.objects.get(pk=self.pk)._mevcut_dict()
                except self.__class__.DoesNotExist:
                    pass
            super().save(*args, **kwargs)
            self.kaydet_denetim(eylem, kullanici_id, ip, eski)


    # ═══════════════════════════════════════════════════════════════════════════
    # 6. ÖRNEK GÜVENLI MODELLER
    # ═══════════════════════════════════════════════════════════════════════════

    class GuvenliKullanici(GuvenliModelTabani):
        """Güvenlik katmanları ile donatılmış kullanıcı modeli."""

        kullanici_adi   = models.CharField(max_length=80,  unique=True, db_index=True)
        email           = models.EmailField(unique=True,  db_index=True)
        sifre_hash      = models.CharField(max_length=256)
        rol             = models.CharField(
            max_length=20, default="user",
            choices=[("user","Kullanıcı"),("admin","Yönetici"),("mod","Moderatör")],
        )
        aktif           = models.BooleanField(default=True, db_index=True)
        basarisiz_giris = models.PositiveSmallIntegerField(default=0)
        kilitli_kadar   = models.DateTimeField(null=True, blank=True)
        son_giris       = models.DateTimeField(null=True, blank=True)

        row_security = SatirDuzeyiGuvenlikManager()

        class Meta:
            app_label = "auth"
            db_table  = "guvenli_kullanicilar"
            indexes   = [models.Index(fields=["kullanici_adi", "aktif"])]

        def sifre_ayarla(self, ham_sifre: str) -> None:
            self.sifre_hash = make_password(ham_sifre)

        def sifre_dogrula(self, ham_sifre: str) -> bool:
            return check_password(ham_sifre, self.sifre_hash)

        def kilitli_mi(self) -> bool:
            if self.kilitli_kadar and self.kilitli_kadar > timezone.now():
                return True
            return False

        def __str__(self):
            return f"{self.kullanici_adi} ({self.rol})"


    class GuvenliVeri(GuvenliModelTabani):
        """Şifreli alan örneği."""

        sahip         = models.ForeignKey(
            GuvenliKullanici, on_delete=models.PROTECT, related_name="veriler"
        )
        baslik        = models.CharField(max_length=200)
        _sifreli_icerik = models.TextField(db_column="sifreli_icerik")
        kategori      = models.CharField(max_length=50, db_index=True)
        imza          = models.CharField(max_length=64, blank=True)

        row_security = SatirDuzeyiGuvenlikManager("sahip_id")

        class Meta:
            app_label = "auth"
            db_table  = "guvenli_veriler"

        def icerik_ayarla(self, ham: str, yonetici: SifreliAlanYoneticisi) -> None:
            self._sifreli_icerik = yonetici.sifrele(ham)

        def icerik_al(self, yonetici: SifreliAlanYoneticisi) -> str:
            return yonetici.coz(self._sifreli_icerik)

        def __str__(self):
            return f"{self.baslik} [{self.kategori}]"


# ═════════════════════════════════════════════════════════════════════════════
# 7. HIZLI BAŞLATMA
# ═════════════════════════════════════════════════════════════════════════════

def django_guvenlik_kur(db_url: str = "sqlite:///guvenli_django.db") -> None:
    """Django'yu minimal güvenlik ayarlarıyla yapılandırır."""
    if not DJANGO_AVAILABLE:
        raise RuntimeError("Django kurulu değil: pip install django")
    if django.conf.settings.configured:
        return
    django.conf.settings.configure(
        SECRET_KEY             = os.environ.get("SECRET_KEY", secrets.token_hex(32)),
        INSTALLED_APPS         = ["django.contrib.auth", "django.contrib.contenttypes"],
        DATABASES              = {
            "default": {
                "ENGINE":    "django.db.backends.sqlite3",
                "NAME":      "guvenli_django.db",
                "OPTIONS":   {"timeout": 20},
                "CONN_MAX_AGE": 60,
            }
        },
        AUTH_PASSWORD_VALIDATORS = [
            {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
             "OPTIONS": {"min_length": 8}},
            {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
            {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
        ],
        DEFAULT_AUTO_FIELD     = "django.db.models.BigAutoField",
        LOGGING                = {
            "version": 1,
            "handlers": {"console": {"class": "logging.StreamHandler"}},
            "root":     {"handlers": ["console"], "level": "INFO"},
        },
    )
    django.setup()


if __name__ == "__main__":
    print("Django DB Güvenlik Katmanı yüklendi.")
    print(f"Cryptography: {'✓' if CRYPTO_AVAILABLE else '✗ (pip install cryptography)'}")
    print(f"Django:       {'✓' if DJANGO_AVAILABLE else '✗ (pip install django)'}")
