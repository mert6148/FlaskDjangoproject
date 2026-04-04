# =============================================================================
# main.py — Flask & Django Uygulama Örneği
# =============================================================================
# Kullanım:
#   Flask  →  MODE=flask  python main.py
#   Django →  MODE=django python main.py  (veya python main.py migrate/runserver)
# =============================================================================

import os
import sys

MODE = os.environ.get("MODE", "flask")  # "flask" veya "django"


# =============================================================================
# ─── FLASK UYGULAMASI ────────────────────────────────────────────────────────
# =============================================================================

def create_flask_app():
    """
    Fabrika fonksiyonu: Flask uygulamasını oluşturur ve yapılandırır.
    Kurulum: pip install flask flask-sqlalchemy flask-login
    """
    from flask import Flask, request, jsonify, render_template_string
    from flask_sqlalchemy import SQLAlchemy

    app = Flask(__name__)

    # ── Yapılandırma ──────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "gizli-anahtar-degistir")

    mysql_url = os.environ.get("MYSQL_DATABASE_URL")
    sqlite_url = "sqlite:///flask_app.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = mysql_url or os.environ.get("DATABASE_URL", sqlite_url)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    db = SQLAlchemy(app)

    # ── Modeller ─────────────────────────────────────────────────────────────
    class Kullanici(db.Model):
        __tablename__ = "kullanici"
        id = db.Column(db.Integer, primary_key=True)
        ad = db.Column(db.String(80), nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        aktif = db.Column(db.Boolean, default=True)
        urunler = db.relationship("Urun", backref="sahip", lazy=True)

        def to_dict(self):
            return {"id": self.id, "ad": self.ad, "email": self.email, "aktif": self.aktif}

    class Urun(db.Model):
        __tablename__ = "urun"
        id = db.Column(db.Integer, primary_key=True)
        isim = db.Column(db.String(120), nullable=False)
        fiyat = db.Column(db.Float, nullable=False)
        stok = db.Column(db.Integer, default=0)
        kullanici_id = db.Column(db.Integer, db.ForeignKey("kullanici.id"), nullable=False)

        def to_dict(self):
            return {
                "id": self.id,
                "isim": self.isim,
                "fiyat": self.fiyat,
                "stok": self.stok,
                "kullanici_id": self.kullanici_id,
            }

    # ── Veritabanı başlatma ───────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    # ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────
    def hata_yaniti(mesaj, kod=400):
        return jsonify({"hata": mesaj}), kod

    def basari_yaniti(veri, mesaj="Başarılı", kod=200):
        return jsonify({"mesaj": mesaj, "veri": veri}), kod

    # ── Güvenlik ve koruma ─────────────────────────────────────────────────────
    IP_BLACKLIST = set(os.environ.get("IP_BLACKLIST", "").split(",")) if os.environ.get("IP_BLACKLIST") else set()

    @app.before_request
    def ip_kontrolu():
        ip = request.remote_addr
        if ip in IP_BLACKLIST:
            return hata_yaniti("Erişim engellendi.", 403)

    @app.after_request
    def guvenlik_basliklari(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    # ── Rotalar: Ana Sayfa ────────────────────────────────────────────────────
    @app.route("/")
    def ana_sayfa():
        html = """
        <h1>Flask Uygulaması Çalışıyor 🚀</h1>
        <ul>
          <li>GET  /api/kullanicilar</li>
          <li>POST /api/kullanicilar</li>
          <li>GET  /api/kullanicilar/&lt;id&gt;</li>
          <li>PUT  /api/kullanicilar/&lt;id&gt;</li>
          <li>DELETE /api/kullanicilar/&lt;id&gt;</li>
          <li>GET  /api/urunler</li>
          <li>POST /api/urunler</li>
          <li>GET  /api/db-check</li>
        </ul>
        """
        return render_template_string(html)

    @app.route("/api/db-check")
    def db_check():
        try:
            result = db.session.execute("SELECT 1").scalar()
            engine_url = str(db.engine.url)
            return basari_yaniti({"db_url": engine_url, "ok": result == 1}, "Veritabanı bağlantısı sağlandı")
        except Exception as error:
            return hata_yaniti(f"Veritabanı bağlantı hatası: {error}", 500)

    # ── Rotalar: Kullanıcı CRUD ───────────────────────────────────────────────
    @app.route("/api/kullanicilar", methods=["GET"])
    def kullanicilari_listele():
        kullanicilar = Kullanici.query.filter_by(aktif=True).all()
        return basari_yaniti([k.to_dict() for k in kullanicilar])

    @app.route("/api/kullanicilar", methods=["POST"])
    def kullanici_olustur():
        veri = request.get_json()
        if not veri or not veri.get("ad") or not veri.get("email"):
            return hata_yaniti("'ad' ve 'email' alanları zorunludur.")
        if Kullanici.query.filter_by(email=veri["email"]).first():
            return hata_yaniti("Bu e-posta zaten kayıtlı.", 409)
        yeni = Kullanici(ad=veri["ad"], email=veri["email"])
        db.session.add(yeni)
        db.session.commit()
        return basari_yaniti(yeni.to_dict(), "Kullanıcı oluşturuldu.", 201)

    @app.route("/api/kullanicilar/<int:kullanici_id>", methods=["GET"])
    def kullanici_getir(kullanici_id):
        kullanici = Kullanici.query.get_or_404(kullanici_id)
        return basari_yaniti(kullanici.to_dict())

    @app.route("/api/kullanicilar/<int:kullanici_id>", methods=["PUT"])
    def kullanici_guncelle(kullanici_id):
        kullanici = Kullanici.query.get_or_404(kullanici_id)
        veri = request.get_json() or {}
        if "ad" in veri:
            kullanici.ad = veri["ad"]
        if "email" in veri:
            kullanici.email = veri["email"]
        db.session.commit()
        return basari_yaniti(kullanici.to_dict(), "Güncellendi.")

    @app.route("/api/kullanicilar/<int:kullanici_id>", methods=["DELETE"])
    def kullanici_sil(kullanici_id):
        kullanici = Kullanici.query.get_or_404(kullanici_id)
        kullanici.aktif = False  # Soft delete
        db.session.commit()
        return basari_yaniti({}, "Kullanıcı silindi.")

    # ── Rotalar: Ürün CRUD ────────────────────────────────────────────────────
    @app.route("/api/urunler", methods=["GET"])
    def urunleri_listele():
        urunler = Urun.query.all()
        return basari_yaniti([u.to_dict() for u in urunler])

    @app.route("/api/urunler", methods=["POST"])
    def urun_olustur():
        veri = request.get_json()
        zorunlu = ["isim", "fiyat", "kullanici_id"]
        if not veri or not all(k in veri for k in zorunlu):
            return hata_yaniti(f"Zorunlu alanlar: {zorunlu}")
        if not Kullanici.query.get(veri["kullanici_id"]):
            return hata_yaniti("Kullanıcı bulunamadı.", 404)
        urun = Urun(
            isim=veri["isim"],
            fiyat=float(veri["fiyat"]),
            stok=veri.get("stok", 0),
            kullanici_id=veri["kullanici_id"],
        )
        db.session.add(urun)
        db.session.commit()
        return basari_yaniti(urun.to_dict(), "Ürün oluşturuldu.", 201)

    # ── Hata İşleyiciler ──────────────────────────────────────────────────────
    @app.errorhandler(404)
    def bulunamadi(e):
        return hata_yaniti("Kayıt bulunamadı.", 404)

    @app.errorhandler(500)
    def sunucu_hatasi(e):
        return hata_yaniti("Sunucu hatası.", 500)

    return app


# =============================================================================
# ─── DJANGO UYGULAMASI ───────────────────────────────────────────────────────
# =============================================================================

def django_yapilandir():
    """
    Django'yu tek-dosya modunda yapılandırır.
    Kurulum: pip install django djangorestframework
    Kullanım:
      python main.py migrate
      python main.py runserver
      python main.py createsuperuser
    """
    import django
    from django.conf import settings

    if settings.configured:
        return  # Zaten yapılandırılmış

    settings.configure(
        DEBUG=True,
        SECRET_KEY=os.environ.get("SECRET_KEY", "django-gizli-anahtar-degistir"),
        ALLOWED_HOSTS=["*"],
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "rest_framework",
            # Tek-dosya uygulaması için __main__ kullanılır
        ],
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF=__name__,  # Bu dosya URL tanımlarını içerir
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(os.getcwd(), "django_app.db"),
            }
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        REST_FRAMEWORK={
            "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
            "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
            "PAGE_SIZE": 10,
        },
        STATIC_URL="/static/",
    )
    django.setup()


def kaydet_django_modeller():
    """Django model ve view tanımlarını dinamik olarak oluşturur."""
    from django.db import models as dj_models

    # ── Modeller ─────────────────────────────────────────────────────────────
    class Kategori(dj_models.Model):
        ad = dj_models.CharField(max_length=100)
        aciklama = dj_models.TextField(blank=True)
        olusturulma = dj_models.DateTimeField(auto_now_add=True)

        class Meta:
            app_label = "auth"  # Tek-dosya için mevcut app etiketini ödünç alıyoruz
            db_table = "kategori"
            verbose_name = "Kategori"
            verbose_name_plural = "Kategoriler"

        def __str__(self):
            return self.ad

    class Urun(dj_models.Model):
        DURUM_SECENEKLERI = [
            ("aktif", "Aktif"),
            ("pasif", "Pasif"),
            ("stok_yok", "Stok Yok"),
        ]
        isim = dj_models.CharField(max_length=200)
        aciklama = dj_models.TextField(blank=True)
        fiyat = dj_models.DecimalField(max_digits=10, decimal_places=2)
        stok = dj_models.PositiveIntegerField(default=0)
        durum = dj_models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default="aktif")
        kategori = dj_models.ForeignKey(
            Kategori, on_delete=dj_models.SET_NULL, null=True, related_name="urunler"
        )
        olusturulma = dj_models.DateTimeField(auto_now_add=True)
        guncelleme = dj_models.DateTimeField(auto_now=True)

        class Meta:
            app_label = "auth"
            db_table = "urun"
            ordering = ["-olusturulma"]
            verbose_name = "Ürün"
            verbose_name_plural = "Ürünler"

        def __str__(self):
            return f"{self.isim} ({self.fiyat} TL)"

    return Kategori, Urun


def olustur_django_views(Kategori, Urun):
    """Django REST Framework ViewSet ve Serializer tanımları."""
    from rest_framework import serializers, viewsets, status
    from rest_framework.decorators import action
    from rest_framework.response import Response

    # ── Serializers ───────────────────────────────────────────────────────────
    class KategoriSerializer(serializers.ModelSerializer):
        urun_sayisi = serializers.SerializerMethodField()

        class Meta:
            model = Kategori
            fields = ["id", "ad", "aciklama", "olusturulma", "urun_sayisi"]
            read_only_fields = ["id", "olusturulma"]

        def get_urun_sayisi(self, obj):
            return obj.urunler.count()

    class UrunSerializer(serializers.ModelSerializer):
        kategori_adi = serializers.CharField(source="kategori.ad", read_only=True)

        class Meta:
            model = Urun
            fields = [
                "id", "isim", "aciklama", "fiyat", "stok",
                "durum", "kategori", "kategori_adi", "olusturulma", "guncelleme",
            ]
            read_only_fields = ["id", "olusturulma", "guncelleme"]

        def validate_fiyat(self, deger):
            if deger <= 0:
                raise serializers.ValidationError("Fiyat sıfırdan büyük olmalıdır.")
            return deger

    # ── ViewSets ──────────────────────────────────────────────────────────────
    class KategoriViewSet(viewsets.ModelViewSet):
        queryset = Kategori.objects.all()
        serializer_class = KategoriSerializer

        @action(detail=True, methods=["get"])
        def urunler(self, request, pk=None):
            """Kategoriye ait ürünleri döndürür: GET /api/kategoriler/<id>/urunler/"""
            kategori = self.get_object()
            urunler = kategori.urunler.all()
            serializer = UrunSerializer(urunler, many=True)
            return Response(serializer.data)

    class UrunViewSet(viewsets.ModelViewSet):
        queryset = Urun.objects.select_related("kategori").all()
        serializer_class = UrunSerializer

        def get_queryset(self):
            qs = super().get_queryset()
            durum = self.request.query_params.get("durum")
            kategori_id = self.request.query_params.get("kategori")
            if durum:
                qs = qs.filter(durum=durum)
            if kategori_id:
                qs = qs.filter(kategori_id=kategori_id)
            return qs

        @action(detail=False, methods=["get"])
        def stok_yok(self, request):
            """Stoğu tükenen ürünler: GET /api/urunler/stok_yok/"""
            urunler = Urun.objects.filter(stok=0)
            serializer = self.get_serializer(urunler, many=True)
            return Response(serializer.data)

        @action(detail=True, methods=["post"])
        def stok_ekle(self, request, pk=None):
            """Stok güncelle: POST /api/urunler/<id>/stok_ekle/ {"miktar": 50}"""
            urun = self.get_object()
            miktar = int(request.data.get("miktar", 0))
            if miktar <= 0:
                return Response(
                    {"hata": "Miktar pozitif olmalıdır."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            urun.stok += miktar
            urun.save(update_fields=["stok"])
            return Response({"yeni_stok": urun.stok})

    return KategoriViewSet, UrunViewSet


def olustur_django_urls(KategoriViewSet, UrunViewSet):
    """URL yapılandırmasını oluşturur."""
    from django.urls import path, include
    from rest_framework.routers import DefaultRouter
    from django.http import JsonResponse

    router = DefaultRouter()
    router.register(r"kategoriler", KategoriViewSet)
    router.register(r"urunler", UrunViewSet)

    def ana_sayfa(request):
        return JsonResponse({
            "mesaj": "Django REST API Çalışıyor 🚀",
            "uç_noktalar": {
                "kategoriler": "/api/kategoriler/",
                "urunler": "/api/urunler/",
                "stok_yok": "/api/urunler/stok_yok/",
                "admin": "/admin/",
            },
        })

    urlpatterns = [
        path("", ana_sayfa),
        path("api/", include(router.urls)),
    ]
    return urlpatterns


# Bu değişken Django'nun ROOT_URLCONF'u çözmesi için gereklidir.
urlpatterns = []


# =============================================================================
# ─── GİRİŞ NOKTASI ───────────────────────────────────────────────────────────
# =============================================================================

if __name__ == "__main__":
    if MODE == "flask":
        # ── Flask başlat ───────────────────────────────────────────────────
        print("=" * 50)
        print("  Flask Uygulaması Başlatılıyor...")
        print("  http://127.0.0.1:5000")
        print("=" * 50)
        try:
            flask_app = create_flask_app()
            flask_app.run(
                host="0.0.0.0",
                port=int(os.environ.get("PORT", 5000)),
                debug=flask_app.config["DEBUG"],
            )
        except ImportError as e:
            print(f"[HATA] Eksik kütüphane: {e}")
            print("Çözüm: pip install flask flask-sqlalchemy")

    elif MODE == "django":
        # ── Django başlat ──────────────────────────────────────────────────
        print("=" * 50)
        print("  Django Uygulaması Başlatılıyor...")
        print("=" * 50)
        try:
            django_yapilandir()
            Kategori, Urun = kaydet_django_modeller()
            KategoriViewSet, UrunViewSet = olustur_django_views(Kategori, Urun)

            # URL'leri global alana yaz (ROOT_URLCONF için)
            import __main__
            __main__.urlpatterns = olustur_django_urls(KategoriViewSet, UrunViewSet)

            from django.core.management import execute_from_command_line
            args = sys.argv[1:] if len(sys.argv) > 1 else ["runserver", "0.0.0.0:8000"]
            execute_from_command_line(["manage.py"] + args)

        except ImportError as e:
            print(f"[HATA] Eksik kütüphane: {e}")
            print("Çözüm: pip install django djangorestframework")

    else:
        print(f"[HATA] Geçersiz MODE='{MODE}'. 'flask' veya 'django' kullanın.")
        sys.exit(1)