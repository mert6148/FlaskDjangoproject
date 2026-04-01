"""
flaskcontroller.py — Flask REST API Denetleyicisi
==================================================
flaskmodel.py modelleri üzerinde tam CRUD API sağlar.

Endpoint'ler:
  Kullanıcı  → /api/kullanicilar
  Ürün       → /api/urunler
  Kategori   → /api/kategoriler
  Sipariş    → /api/siparisler

Kullanım::

    from flask import Flask
    from flaskmodel import create_flask_models
    from flaskcontroller import register_controllers

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    create_flask_models(app)
    register_controllers(app)
    app.run()
"""

from __future__ import annotations

import logging
from functools import wraps
from datetime import datetime

from flask import Blueprint, request, jsonify, abort, current_app

from flaskmodel import db, Kullanici, Kategori, Urun, Siparis, SiparisKalem, SiparisStatu

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# YARDIMCILAR
# ═════════════════════════════════════════════════════════════════════════════

def basari(veri, mesaj: str = "Başarılı", kod: int = 200):
    """Standart başarı yanıtı: {mesaj, veri}"""
    return jsonify({"mesaj": mesaj, "veri": veri}), kod


def hata(mesaj: str, kod: int = 400):
    """Standart hata yanıtı: {hata}"""
    return jsonify({"hata": mesaj}), kod


def json_zorunlu(f):
    """Content-Type: application/json kontrolü decorator'ı."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not request.is_json:
            return hata("Content-Type 'application/json' olmalıdır.", 415)
        return f(*args, **kwargs)
    return wrapped


def sayfalama_parametreleri() -> tuple[int, int]:
    """Sayfa numarası ve boyutunu döndürür."""
    sayfa     = max(1, request.args.get("sayfa", 1, type=int))
    boyut     = min(100, max(1, request.args.get("boyut", 20, type=int)))
    return sayfa, boyut


# ═════════════════════════════════════════════════════════════════════════════
# KULLANICI BLUEPRINT
# ═════════════════════════════════════════════════════════════════════════════

kullanici_bp = Blueprint("kullanicilar", __name__, url_prefix="/api/kullanicilar")


@kullanici_bp.get("/")
def kullanicilari_listele():
    """
    GET /api/kullanicilar/
    Aktif kullanıcıları sayfalı döndürür.

    Query params:
        sayfa (int): Sayfa numarası (varsayılan: 1)
        boyut (int): Sayfa boyutu (varsayılan: 20, max: 100)
    """
    sayfa, boyut = sayfalama_parametreleri()
    sorgu = Kullanici.query.filter_by(silinmis=False, aktif=True)
    sayfalanmis = sorgu.paginate(page=sayfa, per_page=boyut, error_out=False)
    return basari({
        "kullanicilar": [k.to_dict() for k in sayfalanmis.items],
        "toplam":       sayfalanmis.total,
        "sayfa":        sayfa,
        "boyut":        boyut,
    })


@kullanici_bp.post("/")
@json_zorunlu
def kullanici_olustur():
    """
    POST /api/kullanicilar/
    Yeni kullanıcı oluşturur.

    Body (JSON):
        ad    (str): Zorunlu
        email (str): Zorunlu, tekil
        sifre (str): Zorunlu, min 8 karakter
    """
    veri = request.get_json()
    for alan in ("ad", "email", "sifre"):
        if not veri.get(alan):
            return hata(f"'{alan}' alanı zorunludur.")

    if Kullanici.query.filter_by(email=veri["email"]).first():
        return hata("Bu e-posta adresi zaten kayıtlı.", 409)

    if len(veri["sifre"]) < 8:
        return hata("Şifre en az 8 karakter olmalıdır.")

    from werkzeug.security import generate_password_hash
    yeni = Kullanici(
        ad         = veri["ad"].strip(),
        email      = veri["email"].strip().lower(),
        sifre_hash = generate_password_hash(veri["sifre"]),
    )
    db.session.add(yeni)
    db.session.commit()
    logger.info("Yeni kullanıcı: %s", yeni.email)
    return basari(yeni.to_dict(), "Kullanıcı oluşturuldu.", 201)


@kullanici_bp.get("/<int:uid>")
def kullanici_getir(uid: int):
    """GET /api/kullanicilar/<id>"""
    k = db.get_or_404(Kullanici, uid)
    return basari(k.to_dict())


@kullanici_bp.put("/<int:uid>")
@json_zorunlu
def kullanici_guncelle(uid: int):
    """PUT /api/kullanicilar/<id>"""
    k    = db.get_or_404(Kullanici, uid)
    veri = request.get_json()
    if "ad"    in veri: k.ad    = veri["ad"].strip()
    if "email" in veri:
        if Kullanici.query.filter(Kullanici.email == veri["email"],
                                   Kullanici.id != uid).first():
            return hata("Bu e-posta başka bir kullanıcıya ait.", 409)
        k.email = veri["email"].strip().lower()
    if "aktif" in veri: k.aktif = bool(veri["aktif"])
    db.session.commit()
    return basari(k.to_dict(), "Güncellendi.")


@kullanici_bp.delete("/<int:uid>")
def kullanici_sil(uid: int):
    """DELETE /api/kullanicilar/<id> — Soft delete"""
    k = db.get_or_404(Kullanici, uid)
    k.soft_sil()
    db.session.commit()
    return basari({}, "Kullanıcı silindi.")


# ═════════════════════════════════════════════════════════════════════════════
# KATEGORİ BLUEPRINT
# ═════════════════════════════════════════════════════════════════════════════

kategori_bp = Blueprint("kategoriler", __name__, url_prefix="/api/kategoriler")


@kategori_bp.get("/")
def kategorileri_listele():
    """GET /api/kategoriler/ — Tüm kategoriler"""
    kategoriler = Kategori.query.order_by(Kategori.ad).all()
    return basari([k.to_dict() for k in kategoriler])


@kategori_bp.post("/")
@json_zorunlu
def kategori_olustur():
    """POST /api/kategoriler/"""
    veri = request.get_json()
    if not veri.get("ad"):
        return hata("'ad' alanı zorunludur.")
    if Kategori.query.filter_by(ad=veri["ad"]).first():
        return hata("Bu kategori adı zaten mevcut.", 409)
    yeni = Kategori(
        ad               = veri["ad"].strip(),
        aciklama         = veri.get("aciklama"),
        ust_kategori_id  = veri.get("ust_kategori_id"),
    )
    db.session.add(yeni)
    db.session.commit()
    return basari(yeni.to_dict(), "Kategori oluşturuldu.", 201)


@kategori_bp.put("/<int:kid>")
@json_zorunlu
def kategori_guncelle(kid: int):
    """PUT /api/kategoriler/<id>"""
    k    = db.get_or_404(Kategori, kid)
    veri = request.get_json()
    if "ad"       in veri: k.ad       = veri["ad"].strip()
    if "aciklama" in veri: k.aciklama = veri["aciklama"]
    db.session.commit()
    return basari(k.to_dict(), "Güncellendi.")


@kategori_bp.delete("/<int:kid>")
def kategori_sil(kid: int):
    """DELETE /api/kategoriler/<id>"""
    k = db.get_or_404(Kategori, kid)
    if k.urunler:
        return hata("Kategoriye ait ürünler var, önce ürünleri taşıyın.", 409)
    db.session.delete(k)
    db.session.commit()
    return basari({}, "Kategori silindi.")


# ═════════════════════════════════════════════════════════════════════════════
# ÜRÜN BLUEPRINT
# ═════════════════════════════════════════════════════════════════════════════

urun_bp = Blueprint("urunler", __name__, url_prefix="/api/urunler")


@urun_bp.get("/")
def urunleri_listele():
    """
    GET /api/urunler/
    Query params: kategori_id, aktif, stok_yok, arama, sayfa, boyut
    """
    sayfa, boyut = sayfalama_parametreleri()
    sorgu = Urun.query.filter_by(silinmis=False)

    if kid := request.args.get("kategori_id", type=int):
        sorgu = sorgu.filter_by(kategori_id=kid)
    if request.args.get("aktif"):
        sorgu = sorgu.filter_by(aktif=True)
    if request.args.get("stok_yok"):
        sorgu = sorgu.filter(Urun.stok == 0)
    if arama := request.args.get("arama"):
        sorgu = sorgu.filter(Urun.ad.ilike(f"%{arama}%"))

    sayfalanmis = sorgu.paginate(page=sayfa, per_page=boyut, error_out=False)
    return basari({
        "urunler": [u.to_dict() for u in sayfalanmis.items],
        "toplam":  sayfalanmis.total,
        "sayfa":   sayfa,
        "boyut":   boyut,
    })


@urun_bp.post("/")
@json_zorunlu
def urun_olustur():
    """POST /api/urunler/  Body: ad, fiyat, [stok, kategori_id, aciklama]"""
    veri = request.get_json()
    for alan in ("ad", "fiyat"):
        if alan not in veri:
            return hata(f"'{alan}' alanı zorunludur.")
    try:
        fiyat = float(veri["fiyat"])
        assert fiyat > 0
    except (ValueError, AssertionError):
        return hata("Fiyat pozitif bir sayı olmalıdır.")

    yeni = Urun(
        ad           = veri["ad"].strip(),
        fiyat        = fiyat,
        stok         = int(veri.get("stok", 0)),
        aciklama     = veri.get("aciklama"),
        kategori_id  = veri.get("kategori_id"),
    )
    db.session.add(yeni)
    db.session.commit()
    return basari(yeni.to_dict(), "Ürün oluşturuldu.", 201)


@urun_bp.get("/<int:uid>")
def urun_getir(uid: int):
    """GET /api/urunler/<id>"""
    u = db.get_or_404(Urun, uid)
    return basari(u.to_dict())


@urun_bp.put("/<int:uid>")
@json_zorunlu
def urun_guncelle(uid: int):
    """PUT /api/urunler/<id>"""
    u    = db.get_or_404(Urun, uid)
    veri = request.get_json()
    if "ad"          in veri: u.ad          = veri["ad"].strip()
    if "fiyat"       in veri: u.fiyat       = float(veri["fiyat"])
    if "stok"        in veri: u.stok        = int(veri["stok"])
    if "aktif"       in veri: u.aktif       = bool(veri["aktif"])
    if "kategori_id" in veri: u.kategori_id = veri["kategori_id"]
    db.session.commit()
    return basari(u.to_dict(), "Güncellendi.")


@urun_bp.post("/<int:uid>/stok")
@json_zorunlu
def stok_guncelle(uid: int):
    """POST /api/urunler/<id>/stok  Body: miktar (+/-) """
    u     = db.get_or_404(Urun, uid)
    veri  = request.get_json()
    delta = int(veri.get("miktar", 0))
    if u.stok + delta < 0:
        return hata("Stok negatif olamaz.")
    u.stok += delta
    db.session.commit()
    return basari({"yeni_stok": u.stok}, "Stok güncellendi.")


@urun_bp.delete("/<int:uid>")
def urun_sil(uid: int):
    """DELETE /api/urunler/<id> — Soft delete"""
    u = db.get_or_404(Urun, uid)
    u.soft_sil()
    db.session.commit()
    return basari({}, "Ürün silindi.")


# ═════════════════════════════════════════════════════════════════════════════
# SİPARİŞ BLUEPRINT
# ═════════════════════════════════════════════════════════════════════════════

siparis_bp = Blueprint("siparisler", __name__, url_prefix="/api/siparisler")


@siparis_bp.post("/")
@json_zorunlu
def siparis_olustur():
    """
    POST /api/siparisler/
    Body::

        {
          "kullanici_id": 1,
          "kalemler": [
            {"urun_id": 3, "miktar": 2},
            {"urun_id": 7, "miktar": 1}
          ]
        }
    """
    veri = request.get_json()
    if not veri.get("kullanici_id"):
        return hata("'kullanici_id' zorunludur.")
    if not veri.get("kalemler"):
        return hata("En az bir 'kalem' girilmelidir.")

    kullanici = db.get_or_404(Kullanici, veri["kullanici_id"])

    siparis = Siparis(kullanici_id=kullanici.id)
    db.session.add(siparis)

    toplam = 0.0
    for kalem_veri in veri["kalemler"]:
        urun   = db.get_or_404(Urun, kalem_veri["urun_id"])
        miktar = int(kalem_veri.get("miktar", 1))
        if miktar < 1:
            return hata(f"Ürün #{urun.id} için miktar en az 1 olmalıdır.")
        if not urun.stok_yeterli(miktar):
            return hata(f"Ürün #{urun.id} için yeterli stok yok (mevcut: {urun.stok}).")

        kalem = SiparisKalem(
            siparis    = siparis,
            urun_id    = urun.id,
            miktar     = miktar,
            birim_fiyat = urun.fiyat,
        )
        urun.stok -= miktar
        toplam    += kalem.ara_toplam
        db.session.add(kalem)

    siparis.toplam_tutar = toplam
    db.session.commit()
    logger.info("Sipariş oluşturuldu #%d, tutar=%.2f", siparis.id, toplam)
    return basari(siparis.to_dict(), "Sipariş oluşturuldu.", 201)


@siparis_bp.get("/<int:sid>")
def siparis_getir(sid: int):
    """GET /api/siparisler/<id>"""
    s = db.get_or_404(Siparis, sid)
    veri = s.to_dict()
    veri["kalemler"] = [
        {"urun_id": k.urun_id, "miktar": k.miktar,
         "birim_fiyat": k.birim_fiyat, "ara_toplam": k.ara_toplam}
        for k in s.kalemler
    ]
    return basari(veri)


@siparis_bp.put("/<int:sid>/statu")
@json_zorunlu
def statu_guncelle(sid: int):
    """PUT /api/siparisler/<id>/statu  Body: {"statu": "onaylandi"}"""
    s    = db.get_or_404(Siparis, sid)
    veri = request.get_json()
    try:
        s.statu = SiparisStatu(veri.get("statu", ""))
    except ValueError:
        gecerli = [e.value for e in SiparisStatu]
        return hata(f"Geçersiz statu. Geçerliler: {gecerli}")
    db.session.commit()
    return basari(s.to_dict(), f"Statu '{s.statu.value}' olarak güncellendi.")


# ═════════════════════════════════════════════════════════════════════════════
# KAYIT FONKSİYONU
# ═════════════════════════════════════════════════════════════════════════════

def register_controllers(app: Flask) -> None:
    """
    Tüm blueprint'leri Flask uygulamasına kaydeder.

    Kullanım::

        from flaskcontroller import register_controllers
        register_controllers(app)
    """
    app.register_blueprint(kullanici_bp)
    app.register_blueprint(kategori_bp)
    app.register_blueprint(urun_bp)
    app.register_blueprint(siparis_bp)

    @app.get("/api/status")
    def api_status():
        return jsonify({"status": "ok", "version": "1.0.0",
                        "zaman": datetime.utcnow().isoformat()})

    logger.info("Tüm blueprint'ler kaydedildi.")