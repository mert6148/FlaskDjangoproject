#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Şema, Güvenlik ve Entegrasyon Testleri
Flask + Django ortak katman ve system.json bütünlük kontrolleri
"""

import sys
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Opsiyonel import'lar ──────────────────────────────────────────────────────
try:
    from app import create_flask_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    import django
    from django.conf import settings as dj_settings
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

JSON_CT = "application/json"


def get_flask_client():
    if not FLASK_AVAILABLE:
        return None, None
    app = create_flask_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    return app.test_client(), app


# =============================================================================
# ─── ŞEMATİK YAPI DOĞRULAMASI ────────────────────────────────────────────────
# =============================================================================

class TestFlaskResponseSchema(unittest.TestCase):
    """Flask API yanıt şeması tutarlılığı"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask mevcut değil")
        result = get_flask_client()
        if result[0] is None:
            self.skipTest("Flask istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def _post_user(self, ad="Schema Test", email="schema@x.com"):
        return self.client.post(
            "/api/kullanicilar",
            data=json.dumps({"ad": ad, "email": email}),
            content_type=JSON_CT,
        )

    def test_basarili_yanit_sarmalayici(self):
        """Başarılı yanıtlar {mesaj, veri} zarfını içermeli"""
        resp = self.client.get("/api/kullanicilar")
        data = json.loads(resp.data)
        self.assertIn("mesaj", data, "Başarılı yanıtta 'mesaj' alanı bulunmalı")
        self.assertIn("veri", data, "Başarılı yanıtta 'veri' alanı bulunmalı")

    def test_hata_yanit_sarmalayici(self):
        """Hata yanıtları {hata} zarfını içermeli"""
        resp = self.client.post(
            "/api/kullanicilar",
            data=json.dumps({}),
            content_type=JSON_CT,
        )
        data = json.loads(resp.data)
        self.assertIn("hata", data, "Hata yanıtında 'hata' alanı bulunmalı")

    def test_kullanici_sarmalayici_alanlari(self):
        """Kullanıcı nesnesi zorunlu alanları içermeli"""
        self._post_user()
        resp = self.client.get("/api/kullanicilar")
        kullanicilar = json.loads(resp.data)["veri"]
        if kullanicilar:
            for alan in ["id", "ad", "email", "aktif"]:
                self.assertIn(alan, kullanicilar[0])

    def test_id_tipi_integer(self):
        """id alanı integer olmalı"""
        resp = self._post_user()
        uid = json.loads(resp.data)["veri"]["id"]
        self.assertIsInstance(uid, int)

    def test_aktif_tipi_boolean(self):
        """aktif alanı boolean olmalı"""
        resp = self._post_user()
        aktif = json.loads(resp.data)["veri"]["aktif"]
        self.assertIsInstance(aktif, bool)

    def test_urun_fiyat_float(self):
        """Ürün fiyatı float olmalı"""
        user_resp = self._post_user("Satıcı", "satici_schema@x.com")
        uid = json.loads(user_resp.data)["veri"]["id"]
        urun_resp = self.client.post(
            "/api/urunler",
            data=json.dumps({"isim": "Fiyat Test", "fiyat": 49.99, "kullanici_id": uid}),
            content_type=JSON_CT,
        )
        if urun_resp.status_code == 201:
            fiyat = json.loads(urun_resp.data)["veri"]["fiyat"]
            self.assertIsInstance(fiyat, float)


# =============================================================================
# ─── GÜVENLİK TESTLERİ ───────────────────────────────────────────────────────
# =============================================================================

class TestFlaskSecurity(unittest.TestCase):
    """Flask API güvenlik kontrolleri"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask mevcut değil")
        result = get_flask_client()
        if result[0] is None:
            self.skipTest("Flask istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def test_xss_girisi_temizlenmeli(self):
        """XSS yükü içeren kullanıcı adı kabul edilmemeli veya temizlenmeli"""
        payload = {"ad": "<script>alert(1)</script>", "email": "xss@test.com"}
        resp = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(payload),
            content_type=JSON_CT,
        )
        if resp.status_code == 201:
            ad = json.loads(resp.data)["veri"]["ad"]
            self.assertNotIn("<script>", ad, "XSS içeriği temizlenmeli")

    def test_sql_enjeksiyon_reddedilmeli(self):
        """SQL enjeksiyonu içeren giriş 400 veya güvenli yanıt döndürmeli"""
        payload = {"ad": "'; DROP TABLE kullanici; --", "email": "sql@test.com"}
        resp = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(payload),
            content_type=JSON_CT,
        )
        # Uygulama çökmemeli
        self.assertIn(resp.status_code, [200, 201, 400, 422])

    def test_cok_uzun_alan_reddedilmeli(self):
        """Aşırı uzun giriş değeri 400 döndürmeli"""
        payload = {"ad": "A" * 10000, "email": "long@test.com"}
        resp = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(payload),
            content_type=JSON_CT,
        )
        self.assertIn(resp.status_code, [400, 413, 422])

    def test_null_alan_reddedilmeli(self):
        """null değerli zorunlu alan 400 döndürmeli"""
        payload = {"ad": None, "email": "null@test.com"}
        resp = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(payload),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 400)

    def test_fazla_alan_yoksayilmali(self):
        """Beklenmedik ekstra alanlar uygulamayı patlatmamalı"""
        payload = {
            "ad": "Ekstra Alan", "email": "extra@test.com",
            "bilinmeyen": "deger", "diger": 42,
        }
        resp = self.client.post(
            "/api/kullanicilar",
            data=json.dumps(payload),
            content_type=JSON_CT,
        )
        self.assertIn(resp.status_code, [200, 201, 400])

    def test_gecersiz_content_type(self):
        """text/plain ile gönderilen veri işlenemez ya da 400 döndürmeli"""
        resp = self.client.post(
            "/api/kullanicilar",
            data='{"ad": "CT Test", "email": "ct@test.com"}',
            content_type="text/plain",
        )
        self.assertIn(resp.status_code, [400, 415, 422])


# =============================================================================
# ─── E-POSTA DOĞRULAMA ───────────────────────────────────────────────────────
# =============================================================================

class TestEmailValidation(unittest.TestCase):
    """E-posta format doğrulaması (ortak kural seti)"""

    PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    GECERLI = [
        "user@example.com",
        "user.name@domain.co.uk",
        "user+tag@example.org",
        "ahmet@ornek.com.tr",
    ]
    GECERSIZ = [
        "invalid-email",
        "@example.com",
        "user@",
        "user@domain",
        "user name@example.com",
        "",
        "   ",
    ]

    def test_gecerli_emailler_kabul(self):
        for email in self.GECERLI:
            with self.subTest(email=email):
                self.assertTrue(
                    self.PATTERN.match(email),
                    f"Geçerli e-posta reddedildi: {email}",
                )

    def test_gecersiz_emailler_red(self):
        for email in self.GECERSIZ:
            with self.subTest(email=email):
                self.assertFalse(
                    self.PATTERN.match(email),
                    f"Geçersiz e-posta kabul edildi: {email}",
                )

    def test_flask_gecersiz_email_400(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask mevcut değil")
        client, app = get_flask_client()
        if client is None:
            self.skipTest("Flask istemcisi oluşturulamadı")
        with app.app_context():
            for email in self.GECERSIZ:
                resp = client.post(
                    "/api/kullanicilar",
                    data=json.dumps({"ad": "Email Test", "email": email}),
                    content_type=JSON_CT,
                )
                self.assertIn(
                    resp.status_code, [400, 409, 422],
                    f"Geçersiz e-posta kabul edildi: '{email}'",
                )


# =============================================================================
# ─── SİSTEM JSON BÜTÜNLÜK TESTLERİ ──────────────────────────────────────────
# =============================================================================

class TestSystemJsonIntegrity(unittest.TestCase):
    """system.json ve system_output.json bütünlük kontrolleri"""

    def _load(self, dosya: str) -> dict | None:
        path = ROOT / dosya
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_system_json_mevcut(self):
        data = self._load("system.json")
        if data is None:
            self.skipTest("system.json bulunamadı")
        self.assertIsInstance(data, dict)

    def test_system_json_zorunlu_alanlar(self):
        data = self._load("system.json")
        if data is None:
            self.skipTest("system.json bulunamadı")
        for alan in ["name", "version", "AWSTemplateFormatVersion"]:
            self.assertIn(alan, data, f"system.json '{alan}' içermeli")

    def test_system_json_versiyon_format(self):
        data = self._load("system.json")
        if data is None:
            self.skipTest("system.json bulunamadı")
        versiyon = data.get("version", "")
        self.assertTrue(
            re.match(r"^\d+\.\d+\.\d+$", versiyon),
            f"Versiyon 'MAJOR.MINOR.PATCH' formatında olmalı, alınan: {versiyon}",
        )

    def test_aws_template_format_version(self):
        data = self._load("system.json")
        if data is None:
            self.skipTest("system.json bulunamadı")
        aws = data.get("AWSTemplateFormatVersion", {})
        self.assertIn("version", aws)
        self.assertEqual(aws["version"], "2010-09-09")

    def test_system_output_tutarli(self):
        """system_output.json, system.json ile tutarlı olmalı"""
        sys_data    = self._load("system.json")
        output_data = self._load("system_output.json")
        if not sys_data or not output_data:
            self.skipTest("system.json veya system_output.json bulunamadı")
        nested = output_data.get("system", {})
        self.assertEqual(nested.get("name"),    sys_data.get("name"))
        self.assertEqual(nested.get("version"), sys_data.get("version"))

    def test_gecerli_json_encoding(self):
        """JSON dosyaları UTF-8 ile kodlanmış olmalı"""
        for dosya in ["system.json", "system_output.json"]:
            path = ROOT / dosya
            if path.exists():
                try:
                    with open(path, encoding="utf-8") as f:
                        json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    self.fail(f"{dosya} geçerli UTF-8 JSON değil: {e}")


# =============================================================================
# ─── ENTEGRASYON: FLASK + SYSTEM JSON ────────────────────────────────────────
# =============================================================================

class TestFlaskSystemIntegration(unittest.TestCase):
    """Flask uygulaması system.json verisiyle entegrasyon"""

    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask mevcut değil")
        result = get_flask_client()
        if result[0] is None:
            self.skipTest("Flask istemcisi oluşturulamadı")
        self.client, self.app = result
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.sys_json = (ROOT / "system.json")

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def test_status_versiyon_eslesmeli(self):
        """/api/status versiyonu system.json ile eşleşmeli"""
        if not self.sys_json.exists():
            self.skipTest("system.json bulunamadı")
        beklenen = json.loads(self.sys_json.read_text())["version"]
        resp = self.client.get("/api/status")
        api_versiyon = json.loads(resp.data).get("version")
        if api_versiyon:
            self.assertEqual(api_versiyon, beklenen,
                             "API versiyonu system.json ile eşleşmeli")

    def test_tam_crud_akis(self):
        """Oluştur → Getir → Güncelle → Sil akışı tutarlı olmalı"""
        # Oluştur
        resp = self.client.post(
            "/api/kullanicilar",
            data=json.dumps({"ad": "Akış Test", "email": "akis@test.com"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 201)
        uid = json.loads(resp.data)["veri"]["id"]

        # Getir
        resp = self.client.get(f"/api/kullanicilar/{uid}")
        self.assertEqual(resp.status_code, 200)

        # Güncelle
        resp = self.client.put(
            f"/api/kullanicilar/{uid}",
            data=json.dumps({"ad": "Güncel Ad"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)["veri"]["ad"], "Güncel Ad")

        # Sil
        resp = self.client.delete(f"/api/kullanicilar/{uid}")
        self.assertEqual(resp.status_code, 200)

        # Listede yok
        resp = self.client.get("/api/kullanicilar")
        ids = [u["id"] for u in json.loads(resp.data)["veri"]]
        self.assertNotIn(uid, ids)


# =============================================================================
# ─── TEST RUNNER ─────────────────────────────────────────────────────────────
# =============================================================================

def run_shared_tests():
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestFlaskResponseSchema,
        TestFlaskSecurity,
        TestEmailValidation,
        TestSystemJsonIntegrity,
        TestFlaskSystemIntegration,
    ]
    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(0 if run_shared_tests() else 1)
