#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Endpoint Testleri
/api/kullanicilar ve /api/urunler için kapsamlı test suite
"""

import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from app import create_flask_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# ── Test sabit değerleri ──────────────────────────────────────────────────────
VALID_USER   = {"ad": "Ahmet Yılmaz", "email": "ahmet@example.com"}
VALID_URUN   = {"isim": "Test Ürünü", "fiyat": 99.90, "stok": 50, "kullanici_id": 1}
INVALID_USER = {"ad": ""}            # email eksik
INVALID_URUN = {"isim": "Eksik Fiyat"}  # fiyat ve kullanici_id eksik


def get_client():
    """Test istemcisi oluşturur."""
    if not FLASK_AVAILABLE:
        return None
    app = create_flask_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    return app.test_client(), app


# =============================================================================
# ─── SAĞLIK KONTROLÜ ─────────────────────────────────────────────────────────
# =============================================================================

class TestFlaskHealth(unittest.TestCase):
    """Flask uygulama sağlık kontrolleri"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask uygulaması mevcut değil")
        result = get_client()
        if result is None:
            self.skipTest("Test istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def test_anasayfa_200(self):
        """Ana sayfa 200 döndürmeli"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_status_endpoint(self):
        """GET /api/status 200 ve JSON döndürmeli"""
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")

    def test_bilinmeyen_rota_404(self):
        """Bilinmeyen rota 404 döndürmeli"""
        resp = self.client.get("/api/bilinmeyen_endpoint")
        self.assertEqual(resp.status_code, 404)
        data = json.loads(resp.data)
        self.assertIn("hata", data)

    def test_yanit_json_content_type(self):
        """API yanıtları application/json döndürmeli"""
        resp = self.client.get("/api/status")
        self.assertIn("application/json", resp.content_type)


# =============================================================================
# ─── KULLANICI ENDPOINT'LERİ ─────────────────────────────────────────────────
# =============================================================================

class TestKullaniciListele(unittest.TestCase):
    """GET /api/kullanicilar"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask uygulaması mevcut değil")
        result = get_client()
        if result is None:
            self.skipTest("Test istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def test_bos_liste_200(self):
        """Kullanıcı yokken boş liste ve 200 döndürmeli"""
        resp = self.client.get("/api/kullanicilar")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("veri", data)
        self.assertIsInstance(data["veri"], list)

    def test_liste_yapisi(self):
        """Yanıt yapısı doğru anahtarları içermeli"""
        resp = self.client.get("/api/kullanicilar")
        data = json.loads(resp.data)
        self.assertIn("mesaj", data)
        self.assertIn("veri", data)

    def test_kullanici_ekledikten_sonra_liste(self):
        """Eklenen kullanıcı listede görünmeli"""
        self.client.post(
            "/api/kullanicilar",
            data=json.dumps(VALID_USER),
            content_type="application/json",
        )
        resp = self.client.get("/api/kullanicilar")
        data = json.loads(resp.data)
        self.assertGreater(len(data["veri"]), 0)

    def test_sadece_aktif_kullanicilar(self):
        """Silinen kullanıcılar listede görünmemeli"""
        # Kullanıcı oluştur
        post = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(VALID_USER),
            content_type="application/json",
        )
        uid = json.loads(post.data)["veri"]["id"]
        # Sil
        self.client.delete(f"/api/kullanicilar/{uid}")
        # Listede olmamalı
        resp = self.client.get("/api/kullanicilar")
        ids = [u["id"] for u in json.loads(resp.data)["veri"]]
        self.assertNotIn(uid, ids)


class TestKullaniciOlustur(unittest.TestCase):
    """POST /api/kullanicilar"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask uygulaması mevcut değil")
        result = get_client()
        if result is None:
            self.skipTest("Test istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def _post(self, payload):
        return self.client.post(
            "/api/kullanicilar",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_gecerli_kullanici_201(self):
        """Geçerli veriyle kullanıcı oluşturma 201 döndürmeli"""
        resp = self._post(VALID_USER)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertIn("veri", data)
        self.assertIn("id", data["veri"])

    def test_eksik_alan_400(self):
        """Zorunlu alan eksikken 400 döndürmeli"""
        resp = self._post(INVALID_USER)
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("hata", data)

    def test_bos_body_400(self):
        """Boş gövde ile 400 döndürmeli"""
        resp = self.client.post(
            "/api/kullanicilar",
            data="",
            content_type="application/json",
        )
        self.assertIn(resp.status_code, [400, 415])

    def test_duplikat_email_409(self):
        """Aynı e-posta ile ikinci kayıt 409 döndürmeli"""
        self._post(VALID_USER)
        resp = self._post(VALID_USER)
        self.assertEqual(resp.status_code, 409)

    def test_yanit_alanlari(self):
        """Oluşturulan kullanıcı yanıtı doğru alanları içermeli"""
        resp = self._post({"ad": "Test User", "email": "test@x.com"})
        data = json.loads(resp.data)["veri"]
        for alan in ["id", "ad", "email", "aktif"]:
            self.assertIn(alan, data, f"'{alan}' alanı yanıtta bulunmalı")

    def test_kullanici_varsayilan_aktif(self):
        """Yeni kullanıcı varsayılan olarak aktif olmalı"""
        resp = self._post({"ad": "Aktif Test", "email": "aktif@x.com"})
        data = json.loads(resp.data)["veri"]
        self.assertTrue(data.get("aktif"), "Yeni kullanıcı aktif olmalı")

    def test_email_bosluklu_400(self):
        """Boşluk içeren e-posta 400 döndürmeli"""
        resp = self._post({"ad": "Test", "email": "bad email@x.com"})
        self.assertEqual(resp.status_code, 400)


class TestKullaniciGetir(unittest.TestCase):
    """GET /api/kullanicilar/<id>"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask uygulaması mevcut değil")
        result = get_client()
        if result is None:
            self.skipTest("Test istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()
        # Test kullanıcısı oluştur
        post = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(VALID_USER),
            content_type="application/json",
        )
        self.user_id = json.loads(post.data)["veri"]["id"]

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def test_mevcut_kullanici_200(self):
        """Mevcut kullanıcı ID'siyle 200 döndürmeli"""
        resp = self.client.get(f"/api/kullanicilar/{self.user_id}")
        self.assertEqual(resp.status_code, 200)

    def test_olmayan_kullanici_404(self):
        """Var olmayan ID için 404 döndürmeli"""
        resp = self.client.get("/api/kullanicilar/99999")
        self.assertEqual(resp.status_code, 404)

    def test_yanit_veri_yapisi(self):
        """Yanıt veri alanları tam olmalı"""
        resp = self.client.get(f"/api/kullanicilar/{self.user_id}")
        data = json.loads(resp.data)["veri"]
        for alan in ["id", "ad", "email", "aktif"]:
            self.assertIn(alan, data)

    def test_gecersiz_id_tipi_404(self):
        """Sayısal olmayan ID 404 döndürmeli"""
        resp = self.client.get("/api/kullanicilar/abc")
        self.assertEqual(resp.status_code, 404)


class TestKullaniciGuncelle(unittest.TestCase):
    """PUT /api/kullanicilar/<id>"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask uygulaması mevcut değil")
        result = get_client()
        if result is None:
            self.skipTest("Test istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()
        post = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(VALID_USER),
            content_type="application/json",
        )
        self.user_id = json.loads(post.data)["veri"]["id"]

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def _put(self, payload):
        return self.client.put(
            f"/api/kullanicilar/{self.user_id}",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_ad_guncelleme_200(self):
        """Ad güncellemesi 200 döndürmeli"""
        resp = self._put({"ad": "Yeni Ad"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)["veri"]
        self.assertEqual(data["ad"], "Yeni Ad")

    def test_email_guncelleme_200(self):
        """E-posta güncellemesi 200 döndürmeli"""
        resp = self._put({"email": "yeni@example.com"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)["veri"]
        self.assertEqual(data["email"], "yeni@example.com")

    def test_olmayan_kullanici_put_404(self):
        """Var olmayan kullanıcı güncellemesi 404 döndürmeli"""
        resp = self.client.put(
            "/api/kullanicilar/99999",
            data=json.dumps({"ad": "X"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_bos_body_200(self):
        """Boş güncelleme gövdesi değişiklik yapmadan 200 döndürmeli"""
        resp = self._put({})
        self.assertEqual(resp.status_code, 200)


class TestKullaniciSil(unittest.TestCase):
    """DELETE /api/kullanicilar/<id>"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask uygulaması mevcut değil")
        result = get_client()
        if result is None:
            self.skipTest("Test istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()
        post = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(VALID_USER),
            content_type="application/json",
        )
        self.user_id = json.loads(post.data)["veri"]["id"]

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def test_silme_200(self):
        """Silme işlemi 200 döndürmeli"""
        resp = self.client.delete(f"/api/kullanicilar/{self.user_id}")
        self.assertEqual(resp.status_code, 200)

    def test_soft_delete_listeden_cikar(self):
        """Silinen kullanıcı aktif listede görünmemeli"""
        self.client.delete(f"/api/kullanicilar/{self.user_id}")
        resp = self.client.get("/api/kullanicilar")
        ids = [u["id"] for u in json.loads(resp.data)["veri"]]
        self.assertNotIn(self.user_id, ids)

    def test_olmayan_kullanici_sil_404(self):
        """Var olmayan kullanıcı silinmeye çalışılırsa 404 döndürmeli"""
        resp = self.client.delete("/api/kullanicilar/99999")
        self.assertEqual(resp.status_code, 404)


# =============================================================================
# ─── ÜRÜN ENDPOINT'LERİ ──────────────────────────────────────────────────────
# =============================================================================

class TestUrunListele(unittest.TestCase):
    """GET /api/urunler"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask uygulaması mevcut değil")
        result = get_client()
        if result is None:
            self.skipTest("Test istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def test_bos_liste_200(self):
        resp = self.client.get("/api/urunler")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIsInstance(data["veri"], list)

    def test_urun_ekledikten_sonra_liste(self):
        """Eklenen ürün listede görünmeli"""
        # Önce kullanıcı oluştur
        post_u = self.client.post(
            "/api/kullanicilar",
            data=json.dumps({"ad": "Satıcı", "email": "s@x.com"}),
            content_type="application/json",
        )
        uid = json.loads(post_u.data)["veri"]["id"]
        payload = {**VALID_URUN, "kullanici_id": uid}
        self.client.post(
            "/api/urunler",
            data=json.dumps(payload),
            content_type="application/json",
        )
        resp = self.client.get("/api/urunler")
        self.assertGreater(len(json.loads(resp.data)["veri"]), 0)


class TestUrunOlustur(unittest.TestCase):
    """POST /api/urunler"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask uygulaması mevcut değil")
        result = get_client()
        if result is None:
            self.skipTest("Test istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()
        # Sahip kullanıcı oluştur
        post_u = self.client.post(
            "/api/kullanicilar",
            data=json.dumps({"ad": "Satıcı", "email": "satici@x.com"}),
            content_type="application/json",
        )
        self.uid = json.loads(post_u.data)["veri"]["id"]

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def _post_urun(self, payload):
        return self.client.post(
            "/api/urunler",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_gecerli_urun_201(self):
        payload = {**VALID_URUN, "kullanici_id": self.uid}
        resp = self._post_urun(payload)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertIn("id", data["veri"])

    def test_eksik_alan_400(self):
        resp = self._post_urun(INVALID_URUN)
        self.assertEqual(resp.status_code, 400)

    def test_olmayan_kullanici_ile_404(self):
        payload = {**VALID_URUN, "kullanici_id": 99999}
        resp = self._post_urun(payload)
        self.assertEqual(resp.status_code, 404)

    def test_negatif_fiyat_400(self):
        payload = {"isim": "Negatif", "fiyat": -10, "kullanici_id": self.uid}
        resp = self._post_urun(payload)
        self.assertEqual(resp.status_code, 400)

    def test_urun_alanlari_tam(self):
        payload = {**VALID_URUN, "kullanici_id": self.uid}
        resp = self._post_urun(payload)
        data = json.loads(resp.data)["veri"]
        for alan in ["id", "isim", "fiyat", "stok", "kullanici_id"]:
            self.assertIn(alan, data)

    def test_varsayilan_stok_sifir(self):
        """Stok belirtilmezse 0 olmalı"""
        payload = {"isim": "Stoksuz", "fiyat": 10.0, "kullanici_id": self.uid}
        resp = self._post_urun(payload)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)["veri"]
        self.assertEqual(data["stok"], 0)


# =============================================================================
# ─── TEST RUNNER ─────────────────────────────────────────────────────────────
# =============================================================================

def run_flask_tests():
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestFlaskHealth,
        TestKullaniciListele,
        TestKullaniciOlustur,
        TestKullaniciGetir,
        TestKullaniciGuncelle,
        TestKullaniciSil,
        TestUrunListele,
        TestUrunOlustur,
    ]
    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(0 if run_flask_tests() else 1)
