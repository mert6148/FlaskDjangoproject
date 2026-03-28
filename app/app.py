"""
app.py — Flask Web Uygulaması
Düzeltmeler:
  - 'from Flask import' → 'from flask import' (büyük/küçük harf)
  - setDocumentLocator geçersiz class tanımı kaldırıldı
  - def_prog_mode / locator referansları temizlendi
  - Fabrika deseni (create_app) ile yeniden yapılandırıldı
"""

import os
import json
import logging
from datetime import datetime
from flask import (
    Flask, render_template, request,
    redirect, url_for, jsonify, flash, session
)

# ── Loglama ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Basit bellek içi veri deposu (demo) ───────────────────────────────────────
_mesajlar: list[dict] = []
_sayac: int = 0


# ═════════════════════════════════════════════════════════════════════════════
# UYGULAMA FABRİKASI
# ═════════════════════════════════════════════════════════════════════════════

def create_app() -> Flask:
    """Flask uygulamasını oluşturup yapılandırır."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "gelistirme-gizli-anahtari")
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    # ── Yardımcı ──────────────────────────────────────────────────────────────
    def simdi() -> str:
        return datetime.now().strftime("%H:%M:%S")

    # ── Ana sayfa ─────────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        return render_template("index.html", mesajlar=_mesajlar)

    # ── Form gönderimi ────────────────────────────────────────────────────────
    @app.route("/submit", methods=["POST"])
    def submit():
        global _sayac
        veri = request.form.get("data", "").strip()
        if not veri:
            flash("Lütfen bir mesaj girin.", "warn")
            return redirect(url_for("index"))
        if len(veri) > 500:
            flash("Mesaj en fazla 500 karakter olabilir.", "error")
            return redirect(url_for("index"))

        _sayac += 1
        kayit = {
            "id":    _sayac,
            "veri":  veri,
            "zaman": simdi(),
        }
        _mesajlar.insert(0, kayit)
        logger.info("Yeni mesaj #%d: %s", _sayac, veri[:50])
        flash("Mesaj başarıyla gönderildi!", "success")
        return redirect(url_for("index"))

    # ── Mesajı sil ────────────────────────────────────────────────────────────
    @app.route("/sil/<int:mesaj_id>", methods=["POST"])
    def sil(mesaj_id: int):
        global _mesajlar
        once = len(_mesajlar)
        _mesajlar = [m for m in _mesajlar if m["id"] != mesaj_id]
        if len(_mesajlar) < once:
            flash("Mesaj silindi.", "info")
        return redirect(url_for("index"))

    # ── Tümünü temizle ────────────────────────────────────────────────────────
    @app.route("/temizle", methods=["POST"])
    def temizle():
        _mesajlar.clear()
        flash("Tüm mesajlar temizlendi.", "info")
        return redirect(url_for("index"))

    # ── API: durum ────────────────────────────────────────────────────────────
    @app.route("/api/status")
    def api_status():
        return jsonify({
            "status":       "ok",
            "version":      "1.0.0",
            "mesaj_sayisi": len(_mesajlar),
            "zaman":        simdi(),
        })

    # ── API: mesajlar ─────────────────────────────────────────────────────────
    @app.route("/api/mesajlar")
    def api_mesajlar():
        return jsonify(_mesajlar)

    # ── API: mesaj ekle (JSON) ────────────────────────────────────────────────
    @app.route("/api/mesaj", methods=["POST"])
    def api_mesaj_ekle():
        global _sayac
        body = request.get_json(silent=True) or {}
        veri = str(body.get("veri", "")).strip()
        if not veri:
            return jsonify({"hata": "'veri' alanı zorunludur."}), 400
        _sayac += 1
        kayit = {"id": _sayac, "veri": veri, "zaman": simdi()}
        _mesajlar.insert(0, kayit)
        return jsonify({"mesaj": "Eklendi", "kayit": kayit}), 201

    # ── Hata işleyiciler ──────────────────────────────────────────────────────
    @app.errorhandler(404)
    def sayfa_bulunamadi(e):
        return render_template("index.html", mesajlar=_mesajlar, hata="Sayfa bulunamadı."), 404

    @app.errorhandler(500)
    def sunucu_hatasi(e):
        logger.error("Sunucu hatası: %s", e)
        return render_template("index.html", mesajlar=_mesajlar, hata="Sunucu hatası."), 500

    return app


# ═════════════════════════════════════════════════════════════════════════════
# UYGULAMA SARMALAYICI
# ═════════════════════════════════════════════════════════════════════════════

class App:
    """Flask uygulamasını saran yönetici sınıf."""

    def __init__(self):
        self.flask_app = create_app()

    def run(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        logger.info("Uygulama başlatılıyor → http://%s:%d", host, port)
        self.flask_app.run(
            host=host,
            port=port,
            debug=self.flask_app.config["DEBUG"],
        )

    def main(self) -> None:
        self.run()


class Main:
    """Giriş noktası yöneticisi."""

    def __init__(self):
        self.app = App()

    def main(self) -> None:
        self.app.main()


# ═════════════════════════════════════════════════════════════════════════════
# GİRİŞ NOKTASI
# ═════════════════════════════════════════════════════════════════════════════

# Gunicorn / uWSGI için WSGI nesnesi
application = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    Main().main()