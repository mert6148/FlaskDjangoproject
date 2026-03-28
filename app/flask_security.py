"""
flask_security.py — Flask Uygulama Koruma Katmanı
JWT kimlik doğrulama, rate limiting, CORS, güvenli header'lar,
SQL enjeksiyon / XSS koruması, şifreli oturum yönetimi.
"""

import os
import re
import time
import hashlib
import secrets
import logging
from functools import wraps
from datetime import datetime, timedelta, timezone

from flask import (
    Flask, request, jsonify, g, current_app
)
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# JWT için: pip install PyJWT
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

# Argon2 için: pip install argon2-cffi
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    ARGON2_AVAILABLE = True
except ImportError:
    import hmac
    ARGON2_AVAILABLE = False

logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# VERİTABANI MODELLERİ
# ═════════════════════════════════════════════════════════════════════════════

db = SQLAlchemy()


class Kullanici(db.Model):
    __tablename__ = "kullanicilar"

    id              = db.Column(db.Integer, primary_key=True)
    kullanici_adi   = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    email           = db.Column(db.String(120), unique=True, nullable=False, index=True)
    sifre_hash      = db.Column(db.String(256), nullable=False)
    sifre_tuzu      = db.Column(db.String(64),  nullable=False)
    aktif           = db.Column(db.Boolean, default=True, nullable=False)
    rol             = db.Column(db.String(20), default="user", nullable=False)
    basarisiz_giris = db.Column(db.Integer, default=0, nullable=False)
    kilitli_kadar   = db.Column(db.DateTime, nullable=True)
    son_giris       = db.Column(db.DateTime, nullable=True)
    olusturulma     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Denetim
    __table_args__ = (
        db.CheckConstraint("rol IN ('user','admin','moderator')", name="ck_rol"),
        db.CheckConstraint("basarisiz_giris >= 0", name="ck_basarisiz"),
    )

    def to_dict(self):
        return {
            "id":            self.id,
            "kullanici_adi": self.kullanici_adi,
            "email":         self.email,
            "aktif":         self.aktif,
            "rol":           self.rol,
            "son_giris":     self.son_giris.isoformat() if self.son_giris else None,
        }


class KaraListeToken(db.Model):
    """İptal edilen JWT token'larının kara listesi."""
    __tablename__ = "kara_liste_tokenlar"

    id         = db.Column(db.Integer, primary_key=True)
    jti        = db.Column(db.String(64), unique=True, nullable=False, index=True)
    iptal_zamanı = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    bitis_zamanı = db.Column(db.DateTime, nullable=False)


class GirisDeneme(db.Model):
    """Brute-force koruması için giriş denemeleri kaydı."""
    __tablename__ = "giris_denemeler"

    id         = db.Column(db.Integer, primary_key=True)
    ip_adresi  = db.Column(db.String(45), nullable=False, index=True)
    kullanici  = db.Column(db.String(80), nullable=True)
    basarili   = db.Column(db.Boolean, nullable=False)
    zaman      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_agent = db.Column(db.String(256), nullable=True)


# ═════════════════════════════════════════════════════════════════════════════
# ŞİFRE YÖNETİCİSİ
# ═════════════════════════════════════════════════════════════════════════════

class SifreYoneticisi:
    """Güçlü şifre hashleme ve doğrulama."""

    MIN_UZUNLUK   = 8
    OZEL_KARAKTERLER = set("!@#$%^&*()_+-=[]{}|;:,.<>?")

    # Argon2 varsa kullan, yoksa PBKDF2-HMAC-SHA256
    if ARGON2_AVAILABLE:
        _ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)

    @classmethod
    def hashle(cls, sifre: str) -> tuple[str, str]:
        """Şifreyi hashle → (hash, tuz)."""
        tuz = secrets.token_hex(32)
        if ARGON2_AVAILABLE:
            h = cls._ph.hash(sifre + tuz)
        else:
            dk = hashlib.pbkdf2_hmac(
                'sha256',
                (sifre + tuz).encode('utf-8'),
                tuz.encode('utf-8'),
                iterations=260_000,
            )
            h = dk.hex()
        return h, tuz

    @classmethod
    def dogrula(cls, sifre: str, sifre_hash: str, tuz: str) -> bool:
        """Şifreyi hash ile karşılaştır."""
        try:
            if ARGON2_AVAILABLE:
                return cls._ph.verify(sifre_hash, sifre + tuz)
            dk = hashlib.pbkdf2_hmac(
                'sha256',
                (sifre + tuz).encode('utf-8'),
                tuz.encode('utf-8'),
                iterations=260_000,
            )
            return hmac.compare_digest(dk.hex(), sifre_hash)
        except Exception:
            return False

    @classmethod
    def guclu_mu(cls, sifre: str) -> tuple[bool, list[str]]:
        """Şifre güç kurallarını kontrol eder."""
        hatalar = []
        if len(sifre) < cls.MIN_UZUNLUK:
            hatalar.append(f"En az {cls.MIN_UZUNLUK} karakter olmalı")
        if not any(c.isupper() for c in sifre):
            hatalar.append("En az bir büyük harf gerekli")
        if not any(c.islower() for c in sifre):
            hatalar.append("En az bir küçük harf gerekli")
        if not any(c.isdigit() for c in sifre):
            hatalar.append("En az bir rakam gerekli")
        if not any(c in cls.OZEL_KARAKTERLER for c in sifre):
            hatalar.append("En az bir özel karakter gerekli")
        return (len(hatalar) == 0), hatalar


# ═════════════════════════════════════════════════════════════════════════════
# GİRİŞ DOĞRULAMA
# ═════════════════════════════════════════════════════════════════════════════

EMAIL_RE    = re.compile(r'^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$')
KAD_RE      = re.compile(r'^[a-zA-Z0-9_\-]{3,30}$')
XSS_PATTERN = re.compile(r'<[^>]*>|javascript:|data:', re.IGNORECASE)
SQL_PATTERN = re.compile(
    r"(--|;|\'|\"|\bOR\b|\bAND\b|\bDROP\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bUNION\b)",
    re.IGNORECASE
)


def temizle(deger: str, max_uzunluk: int = 500) -> str:
    """XSS ve SQL özel karakterlerini temizler."""
    if not isinstance(deger, str):
        return ""
    d = deger.strip()[:max_uzunluk]
    d = XSS_PATTERN.sub('', d)
    return d


def email_gecerli(email: str) -> bool:
    return bool(EMAIL_RE.match(email)) if email else False


def kullanici_adi_gecerli(kad: str) -> bool:
    return bool(KAD_RE.match(kad)) if kad else False


def sql_enjeksiyonu_var_mi(deger: str) -> bool:
    return bool(SQL_PATTERN.search(deger)) if isinstance(deger, str) else False


# ═════════════════════════════════════════════════════════════════════════════
# JWT YÖNETİCİSİ
# ═════════════════════════════════════════════════════════════════════════════

class JWTYoneticisi:
    """JWT üretimi, doğrulaması ve iptal yönetimi."""

    @staticmethod
    def token_uret(kullanici_id: int, rol: str, sure_dk: int = 60) -> str:
        if not JWT_AVAILABLE:
            raise RuntimeError("PyJWT kurulu değil: pip install PyJWT")
        jti = secrets.token_hex(32)
        bitis = datetime.now(timezone.utc) + timedelta(minutes=sure_dk)
        payload = {
            "sub":  str(kullanici_id),
            "rol":  rol,
            "jti":  jti,
            "iat":  datetime.now(timezone.utc),
            "exp":  bitis,
            "iss":  "flaskdjango-app",
        }
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def token_dogrula(token: str) -> dict | None:
        if not JWT_AVAILABLE:
            return None
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
                issuer="flaskdjango-app",
            )
            # Kara liste kontrolü
            kara = KaraListeToken.query.filter_by(jti=payload.get("jti")).first()
            if kara:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Süresi dolmuş token")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Geçersiz token: {e}")
        return None

    @staticmethod
    def token_iptal_et(jti: str, bitis: datetime) -> None:
        kara = KaraListeToken(jti=jti, bitis_zamanı=bitis)
        db.session.add(kara)
        db.session.commit()

    @staticmethod
    def kara_liste_temizle() -> int:
        """Süresi geçmiş kara liste kayıtlarını siler."""
        simdi = datetime.utcnow()
        silinen = KaraListeToken.query.filter(
            KaraListeToken.bitis_zamanı < simdi
        ).delete()
        db.session.commit()
        return silinen


# ═════════════════════════════════════════════════════════════════════════════
# KİLİTLEME YÖNETİCİSİ
# ═════════════════════════════════════════════════════════════════════════════

MAX_BASARISIZ   = 5    # ardışık başarısız giriş limiti
KILIT_SURE_DK   = 15   # dakika cinsinden kilit süresi


class KilitleyiciYoneticisi:

    @staticmethod
    def giris_basarisiz(kullanici: Kullanici) -> None:
        kullanici.basarisiz_giris += 1
        if kullanici.basarisiz_giris >= MAX_BASARISIZ:
            kullanici.kilitli_kadar = datetime.utcnow() + timedelta(minutes=KILIT_SURE_DK)
            logger.warning(f"Hesap kilitlendi: {kullanici.kullanici_adi}")
        db.session.commit()

    @staticmethod
    def giris_basarili(kullanici: Kullanici) -> None:
        kullanici.basarisiz_giris = 0
        kullanici.kilitli_kadar  = None
        kullanici.son_giris      = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def kilitli_mi(kullanici: Kullanici) -> bool:
        if kullanici.kilitli_kadar and kullanici.kilitli_kadar > datetime.utcnow():
            return True
        if kullanici.kilitli_kadar:
            kullanici.kilitli_kadar  = None
            kullanici.basarisiz_giris = 0
            db.session.commit()
        return False


# ═════════════════════════════════════════════════════════════════════════════
# GÜVENLİK DECORATOR'LARI
# ═════════════════════════════════════════════════════════════════════════════

def giris_zorunlu(f):
    """JWT doğrulaması gerektiren endpoint'ler için decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"hata": "Yetkilendirme başlığı eksik"}), 401
        token = auth.split(" ", 1)[1]
        payload = JWTYoneticisi.token_dogrula(token)
        if not payload:
            return jsonify({"hata": "Geçersiz veya süresi dolmuş token"}), 401
        g.kullanici_id  = int(payload["sub"])
        g.kullanici_rol = payload["rol"]
        g.jti           = payload["jti"]
        return f(*args, **kwargs)
    return decorated


def rol_zorunlu(*roller):
    """Belirli rolleri gerektiren endpoint'ler için decorator."""
    def decorator(f):
        @wraps(f)
        @giris_zorunlu
        def decorated(*args, **kwargs):
            if g.kullanici_rol not in roller:
                return jsonify({"hata": "Bu işlem için yetkiniz yok"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def json_zorunlu(f):
    """Content-Type: application/json kontrolü."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            return jsonify({"hata": "Content-Type application/json olmalı"}), 415
        return f(*args, **kwargs)
    return decorated


def giris_kaydet(basarili: bool, kullanici_adi: str = None) -> None:
    try:
        kayit = GirisDeneme(
            ip_adresi  = request.remote_addr or "bilinmiyor",
            kullanici  = kullanici_adi,
            basarili   = basarili,
            user_agent = request.user_agent.string[:256] if request.user_agent else None,
        )
        db.session.add(kayit)
        db.session.commit()
    except Exception as e:
        logger.error(f"Giriş kaydı hatası: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# FLASK UYGULAMA FABRİKASI
# ═════════════════════════════════════════════════════════════════════════════

def create_flask_app() -> Flask:
    app = Flask(__name__)

    # ── Yapılandırma ──────────────────────────────────────────────────────────
    app.config.update(
        SECRET_KEY                          = os.environ.get("SECRET_KEY", secrets.token_hex(32)),
        SQLALCHEMY_DATABASE_URI             = os.environ.get("DATABASE_URL", "sqlite:///guvenli_app.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS      = False,
        SQLALCHEMY_ENGINE_OPTIONS           = {
            "pool_pre_ping": True,
            "pool_recycle":  300,
            "connect_args":  {"check_same_thread": False},
        },
        # Oturum güvenliği
        SESSION_COOKIE_HTTPONLY             = True,
        SESSION_COOKIE_SECURE               = os.environ.get("FLASK_ENV") == "production",
        SESSION_COOKIE_SAMESITE             = "Lax",
        PERMANENT_SESSION_LIFETIME          = timedelta(hours=1),
        # JSON
        JSON_SORT_KEYS                      = False,
    )

    db.init_app(app)

    # ── Rate Limiter ──────────────────────────────────────────────────────────
    limiter = Limiter(
        key_func    = get_remote_address,
        app         = app,
        default_limits = ["200 per day", "50 per hour"],
        storage_uri = "memory://",
    )

    # ── Güvenlik Başlıkları ───────────────────────────────────────────────────
    @app.after_request
    def guvenlik_basliklari(response):
        response.headers["X-Content-Type-Options"]        = "nosniff"
        response.headers["X-Frame-Options"]               = "DENY"
        response.headers["X-XSS-Protection"]              = "1; mode=block"
        response.headers["Strict-Transport-Security"]     = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"]       = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        )
        response.headers["Referrer-Policy"]               = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]            = "geolocation=(), microphone=()"
        response.headers.pop("Server", None)
        return response

    # ── Rotalar ───────────────────────────────────────────────────────────────

    @app.route("/api/auth/kayit", methods=["POST"])
    @limiter.limit("5 per minute")
    @json_zorunlu
    def kayit():
        veri = request.get_json()
        kad  = temizle(veri.get("kullanici_adi", ""))
        email = temizle(veri.get("email", ""))
        sifre = veri.get("sifre", "")

        hatalar = []
        if not kullanici_adi_gecerli(kad):
            hatalar.append("Kullanıcı adı 3-30 karakter, sadece harf/rakam/_ içermeli")
        if not email_gecerli(email):
            hatalar.append("Geçerli bir e-posta adresi girin")
        if sql_enjeksiyonu_var_mi(kad) or sql_enjeksiyonu_var_mi(email):
            hatalar.append("Geçersiz karakter tespit edildi")

        guclu, sifre_hatalari = SifreYoneticisi.guclu_mu(sifre)
        hatalar.extend(sifre_hatalari)

        if hatalar:
            return jsonify({"hata": hatalar}), 400

        if Kullanici.query.filter(
            (Kullanici.kullanici_adi == kad) | (Kullanici.email == email)
        ).first():
            return jsonify({"hata": "Kullanıcı adı veya e-posta zaten kayıtlı"}), 409

        sifre_hash, tuz = SifreYoneticisi.hashle(sifre)
        yeni = Kullanici(
            kullanici_adi=kad, email=email,
            sifre_hash=sifre_hash, sifre_tuzu=tuz,
        )
        db.session.add(yeni)
        db.session.commit()
        logger.info(f"Yeni kullanıcı kaydı: {kad}")
        return jsonify({"mesaj": "Kayıt başarılı", "id": yeni.id}), 201

    @app.route("/api/auth/giris", methods=["POST"])
    @limiter.limit("10 per minute")
    @json_zorunlu
    def giris():
        veri = request.get_json()
        kad  = temizle(veri.get("kullanici_adi", ""))
        sifre = veri.get("sifre", "")

        if not kad or not sifre:
            return jsonify({"hata": "Kullanıcı adı ve şifre zorunlu"}), 400

        kullanici = Kullanici.query.filter_by(kullanici_adi=kad, aktif=True).first()

        if not kullanici:
            giris_kaydet(False, kad)
            # Zamanlama saldırısını önlemek için sahte hash
            SifreYoneticisi.dogrula("dummy", "0" * 64, "0" * 64)
            return jsonify({"hata": "Geçersiz kimlik bilgileri"}), 401

        if KilitleyiciYoneticisi.kilitli_mi(kullanici):
            return jsonify({"hata": f"Hesap geçici olarak kilitlendi. Lütfen {KILIT_SURE_DK} dakika sonra tekrar deneyin"}), 423

        if not SifreYoneticisi.dogrula(sifre, kullanici.sifre_hash, kullanici.sifre_tuzu):
            KilitleyiciYoneticisi.giris_basarisiz(kullanici)
            giris_kaydet(False, kad)
            kalan = MAX_BASARISIZ - kullanici.basarisiz_giris
            return jsonify({"hata": f"Geçersiz kimlik bilgileri. {max(kalan,0)} deneme hakkınız kaldı"}), 401

        KilitleyiciYoneticisi.giris_basarili(kullanici)
        giris_kaydet(True, kad)

        token = JWTYoneticisi.token_uret(kullanici.id, kullanici.rol)
        return jsonify({
            "mesaj": "Giriş başarılı",
            "token": token,
            "kullanici": kullanici.to_dict(),
        }), 200

    @app.route("/api/auth/cikis", methods=["POST"])
    @giris_zorunlu
    def cikis():
        JWTYoneticisi.token_iptal_et(g.jti, datetime.utcnow() + timedelta(hours=1))
        return jsonify({"mesaj": "Çıkış yapıldı"}), 200

    @app.route("/api/kullanici/profil", methods=["GET"])
    @giris_zorunlu
    def profil():
        kullanici = Kullanici.query.get_or_404(g.kullanici_id)
        return jsonify(kullanici.to_dict()), 200

    @app.route("/api/admin/kullanicilar", methods=["GET"])
    @rol_zorunlu("admin")
    def admin_kullanici_listesi():
        kullanicilar = Kullanici.query.filter_by(aktif=True).all()
        return jsonify([k.to_dict() for k in kullanicilar]), 200

    @app.errorhandler(429)
    def cok_fazla_istek(e):
        return jsonify({"hata": "Çok fazla istek. Lütfen bekleyin."}), 429

    @app.errorhandler(404)
    def bulunamadi(e):
        return jsonify({"hata": "Kaynak bulunamadı"}), 404

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    uygulama = create_flask_app()
    uygulama.run(host="0.0.0.0", port=5000, debug=False)
