"""
app.py — Flask + SQLite Veritabanı Konfigürasyonu
JS istemci katmanı ile tam entegrasyon:
  - SQLAlchemy ORM
  - CRUD API endpoint'leri (app.js ile uyumlu)
  - Arama, istatistik, güncelleme rotaları
  - CORS başlıkları (JS fetch için)
"""

import os
import re
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# ── Loglama ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Veritabanı nesnesi (fabrika dışında tanımla → test edilebilir) ────────────
db = SQLAlchemy()


# ═════════════════════════════════════════════════════════════════════════════
# MODEL
# ═════════════════════════════════════════════════════════════════════════════

class Mesaj(db.Model):
    """Mesaj tablosu — app.js DB katmanıyla eşleşir."""
    __tablename__ = "mesajlar"

    id         = db.Column(db.Integer, primary_key=True)
    veri       = db.Column(db.String(500), nullable=False)
    zaman      = db.Column(db.String(20),  nullable=False, default=lambda: _simdi())
    olusturma  = db.Column(db.DateTime,    default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "veri": self.veri, "zaman": self.zaman}

    def __repr__(self):
        return f"<Mesaj #{self.id}: {self.veri[:30]}>"


def _simdi() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _temizle(metin: str) -> str:
    """Temel XSS koruması."""
    return re.sub(r"<[^>]*>", "", metin).strip()


# ═════════════════════════════════════════════════════════════════════════════
# UYGULAMA FABRİKASI
# ═════════════════════════════════════════════════════════════════════════════

def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    # ── Yapılandırma ──────────────────────────────────────────────────────────
    app.config.update(
        SECRET_KEY                     = os.environ.get("SECRET_KEY", "dev-secret"),
        SQLALCHEMY_DATABASE_URI        = os.environ.get("DATABASE_URL", "sqlite:///mesajlar.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS = False,
        SQLALCHEMY_ENGINE_OPTIONS      = {
            "pool_pre_ping": True,
            "connect_args": {"check_same_thread": False},
        },
        JSON_SORT_KEYS = False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # ── Tablolar ──────────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        logger.info("Veritabanı hazır: %s", app.config["SQLALCHEMY_DATABASE_URI"])

    # ── CORS: app.js fetch() çağrıları için ──────────────────────────────────
    @app.after_request
    def cors_basliklari(response):
        response.headers["Access-Control-Allow-Origin"]  = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
        return response

    @app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def options_handler(path):
        return jsonify({}), 200

    # ─────────────────────────────────────────────────────────────────────────
    # HTML ROTALAR
    # ─────────────────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        mesajlar = Mesaj.query.order_by(Mesaj.olusturma.desc()).all()
        return render_template("index.html", mesajlar=[m.to_dict() for m in mesajlar])

    @app.route("/submit", methods=["POST"])
    def submit():
        """Form tabanlı gönderim (JS olmadan da çalışır)."""
        veri = _temizle(request.form.get("data", ""))
        if not veri:
            flash("Mesaj boş olamaz.", "warn")
        elif len(veri) > 500:
            flash("Mesaj 500 karakteri geçemez.", "error")
        else:
            yeni = Mesaj(veri=veri)
            db.session.add(yeni)
            db.session.commit()
            flash("Mesaj kaydedildi!", "success")
        return redirect(url_for("index"))

    @app.route("/temizle", methods=["POST"])
    def temizle():
        Mesaj.query.delete()
        db.session.commit()
        flash("Tüm mesajlar silindi.", "info")
        return redirect(url_for("index"))

    # ─────────────────────────────────────────────────────────────────────────
    # JSON API — app.js DB katmanıyla birebir eşleşir
    # ─────────────────────────────────────────────────────────────────────────

    @app.route("/api/status")
    def api_status():
        """GET /api/status — DB.kontrol() çağrısı"""
        sayi = Mesaj.query.count()
        return jsonify({
            "status":       "ok",
            "version":      "1.0.0",
            "mesaj_sayisi": sayi,
            "zaman":        _simdi(),
            "db_uri":       app.config["SQLALCHEMY_DATABASE_URI"].split("///")[-1],
        })

    @app.route("/api/mesajlar", methods=["GET"])
    def api_mesajlar():
        """GET /api/mesajlar — DB.mesajlariGetir()"""
        mesajlar = Mesaj.query.order_by(Mesaj.olusturma.desc()).all()
        return jsonify([m.to_dict() for m in mesajlar])

    @app.route("/api/mesajlar", methods=["DELETE"])
    def api_mesajlar_sil():
        """DELETE /api/mesajlar — DB.tumunuSil()"""
        silinen = Mesaj.query.count()
        Mesaj.query.delete()
        db.session.commit()
        return jsonify({"mesaj": f"{silinen} kayıt silindi"})

    @app.route("/api/mesaj", methods=["POST"])
    def api_mesaj_ekle():
        """POST /api/mesaj — DB.mesajEkle()"""
        body = request.get_json(silent=True) or {}
        veri = _temizle(str(body.get("veri", "")))
        if not veri:
            return jsonify({"hata": "'veri' alanı zorunludur."}), 400
        if len(veri) > 500:
            return jsonify({"hata": "500 karakter sınırı aşıldı."}), 400
        yeni = Mesaj(veri=veri)
        db.session.add(yeni)
        db.session.commit()
        logger.info("API: Mesaj eklendi #%d", yeni.id)
        return jsonify({"mesaj": "Eklendi", "kayit": yeni.to_dict()}), 201

    @app.route("/api/mesaj/<int:mid>", methods=["GET"])
    def api_mesaj_getir(mid: int):
        """GET /api/mesaj/<id>"""
        m = Mesaj.query.get_or_404(mid)
        return jsonify(m.to_dict())

    @app.route("/api/mesaj/<int:mid>", methods=["PUT"])
    def api_mesaj_guncelle(mid: int):
        """PUT /api/mesaj/<id> — DB.mesajGuncelle()"""
        m = Mesaj.query.get_or_404(mid)
        body = request.get_json(silent=True) or {}
        yeni_veri = _temizle(str(body.get("veri", "")))
        if not yeni_veri:
            return jsonify({"hata": "Yeni veri boş olamaz."}), 400
        m.veri  = yeni_veri
        m.zaman = _simdi()
        db.session.commit()
        return jsonify({"mesaj": "Güncellendi", "kayit": m.to_dict()})

    @app.route("/api/mesaj/<int:mid>", methods=["DELETE"])
    def api_mesaj_sil(mid: int):
        """DELETE /api/mesaj/<id> — DB.mesajSil()"""
        m = Mesaj.query.get_or_404(mid)
        db.session.delete(m)
        db.session.commit()
        return jsonify({"mesaj": f"#{mid} silindi"})

    @app.route("/api/mesajlar/ara")
    def api_ara():
        """GET /api/mesajlar/ara?q=... — DB.ara()"""
        sorgu = _temizle(request.args.get("q", ""))
        if not sorgu:
            return jsonify([])
        sonuclar = Mesaj.query.filter(
            Mesaj.veri.ilike(f"%{sorgu}%")
        ).order_by(Mesaj.olusturma.desc()).all()
        return jsonify([m.to_dict() for m in sonuclar])

    @app.route("/api/db/istatistik")
    def api_db_istatistik():
        """GET /api/db/istatistik — DB.istatistikler()"""
        toplam  = Mesaj.query.count()
        bugun   = Mesaj.query.filter(
            db.func.date(Mesaj.olusturma) == db.func.date(datetime.utcnow())
        ).count()
        ort_len = db.session.query(
            db.func.avg(db.func.length(Mesaj.veri))
        ).scalar() or 0
        return jsonify({
            "Toplam Mesaj":      toplam,
            "Bugün Eklenen":     bugun,
            "Ort. Uzunluk":      f"{ort_len:.0f} karakter",
            "Veritabanı":        app.config["SQLALCHEMY_DATABASE_URI"].split("///")[-1],
            "Tablo":             "mesajlar",
        })

    # ── Hata işleyiciler ──────────────────────────────────────────────────────
    @app.errorhandler(404)
    def bulunamadi(e):
        if request.path.startswith("/api/"):
            return jsonify({"hata": "Kaynak bulunamadı"}), 404
        return redirect(url_for("index"))

    @app.errorhandler(500)
    def sunucu_hatasi(e):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"hata": "Sunucu hatası"}), 500
        flash("Sunucu hatası oluştu.", "error")
        return redirect(url_for("index"))

    return app


# ═════════════════════════════════════════════════════════════════════════════
# GİRİŞ NOKTASI
# ═════════════════════════════════════════════════════════════════════════════

application = create_app()           # Gunicorn için

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Başlatılıyor → http://0.0.0.0:%d", port)
    application.run(host="0.0.0.0", port=port, debug=True)
