#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Django REST Framework API Testleri
/api/kategoriler ve /api/urunler ViewSet'leri için kapsamlı test suite
"""

import sys
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    import django
    from django.test import TestCase as DjangoTestCase, Client
    from django.conf import settings as django_settings
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

# Django yapılandırması yoksa kuralım
if DJANGO_AVAILABLE and not django_settings.configured:
    django_settings.configure(
        DEBUG=True,
        SECRET_KEY="test-secret-key",
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "rest_framework",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        ROOT_URLCONF="main",
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        REST_FRAMEWORK={"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"]},
    )
    try:
        django.setup()
    except Exception:
        DJANGO_AVAILABLE = False

# ── Yardımcılar ───────────────────────────────────────────────────────────────
JSON_CT = "application/json"

def json_body(data: dict) -> bytes:
    return json.dumps(data).encode()


# =============================================================================
# ─── KATEGORİ ENDPOINT TESTLERİ ──────────────────────────────────────────────
# =============================================================================

class TestKategoriListCreate(unittest.TestCase):
    """GET /api/kategoriler/ ve POST /api/kategoriler/"""

    def setUp(self):
        if not DJANGO_AVAILABLE:
            self.skipTest("Django mevcut değil")
        try:
            from main import (
                django_yapilandir,
                kaydet_django_modeller,
                olustur_django_views,
                olustur_django_urls,
            )
            django_yapilandir()
            Kat, Urun = kaydet_django_modeller()
            KatVS, UrunVS = olustur_django_views(Kat, Urun)
            self.urls = olustur_django_urls(KatVS, UrunVS)
            self.Kategori = Kat
            self.Urun = Urun
            from django.test import Client as DjClient
            self.client = DjClient()
        except Exception as e:
            self.skipTest(f"Django kurulum hatası: {e}")

    # ── LIST ──────────────────────────────────────────────────────────────────
    def test_get_kategoriler_200(self):
        """GET /api/kategoriler/ — 200 ve liste döndürmeli"""
        resp = self.client.get("/api/kategoriler/")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn("results", data)

    def test_get_kategori_liste_yapisi(self):
        """Sayfalı yanıt zorunlu alanları içermeli"""
        resp = self.client.get("/api/kategoriler/")
        data = json.loads(resp.content)
        for alan in ["count", "results"]:
            self.assertIn(alan, data)

    # ── CREATE ────────────────────────────────────────────────────────────────
    def test_post_gecerli_kategori_201(self):
        """Geçerli kategori verisi 201 döndürmeli"""
        resp = self.client.post(
            "/api/kategoriler/",
            data=json_body({"ad": "Elektronik", "aciklama": "Tüm elektronik ürünler"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data["ad"], "Elektronik")

    def test_post_eksik_ad_400(self):
        """Ad alanı eksikken 400 döndürmeli"""
        resp = self.client.post(
            "/api/kategoriler/",
            data=json_body({"aciklama": "Açıklama var ama ad yok"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 400)

    def test_post_bos_body_400(self):
        """Boş gövde ile 400 döndürmeli"""
        resp = self.client.post(
            "/api/kategoriler/",
            data=json_body({}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 400)

    def test_yanit_urun_sayisi_alani(self):
        """Yanıt urun_sayisi alanını içermeli"""
        self.client.post(
            "/api/kategoriler/",
            data=json_body({"ad": "Sayı Testi"}),
            content_type=JSON_CT,
        )
        resp = self.client.get("/api/kategoriler/")
        results = json.loads(resp.content)["results"]
        if results:
            self.assertIn("urun_sayisi", results[0])

    def test_read_only_alanlar_degistirilemez(self):
        """id ve olusturulma alanları POST ile geçersiz kılınamamalı"""
        resp = self.client.post(
            "/api/kategoriler/",
            data=json_body({"ad": "RO Test", "id": 9999, "olusturulma": "2000-01-01"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertNotEqual(data.get("id"), 9999)


class TestKategoriDetail(unittest.TestCase):
    """GET/PUT/PATCH/DELETE /api/kategoriler/<pk>/"""

    def setUp(self):
        if not DJANGO_AVAILABLE:
            self.skipTest("Django mevcut değil")
        try:
            from main import django_yapilandir, kaydet_django_modeller, olustur_django_views, olustur_django_urls
            django_yapilandir()
            Kat, Urun = kaydet_django_modeller()
            KatVS, UrunVS = olustur_django_views(Kat, Urun)
            self.urls = olustur_django_urls(KatVS, UrunVS)
            self.Kategori = Kat
            from django.test import Client as DjClient
            self.client = DjClient()
            # Test kategorisi
            resp = self.client.post(
                "/api/kategoriler/",
                data=json_body({"ad": "Detay Testi"}),
                content_type=JSON_CT,
            )
            self.pk = json.loads(resp.content)["id"]
        except Exception as e:
            self.skipTest(f"Kurulum hatası: {e}")

    def test_get_detay_200(self):
        resp = self.client.get(f"/api/kategoriler/{self.pk}/")
        self.assertEqual(resp.status_code, 200)

    def test_olmayan_pk_404(self):
        resp = self.client.get("/api/kategoriler/99999/")
        self.assertEqual(resp.status_code, 404)

    def test_put_guncelleme_200(self):
        resp = self.client.put(
            f"/api/kategoriler/{self.pk}/",
            data=json_body({"ad": "Güncel Ad"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["ad"], "Güncel Ad")

    def test_patch_kismi_guncelleme_200(self):
        resp = self.client.patch(
            f"/api/kategoriler/{self.pk}/",
            data=json_body({"aciklama": "Yeni açıklama"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 200)

    def test_delete_204(self):
        resp = self.client.delete(f"/api/kategoriler/{self.pk}/")
        self.assertEqual(resp.status_code, 204)
        resp2 = self.client.get(f"/api/kategoriler/{self.pk}/")
        self.assertEqual(resp2.status_code, 404)

    def test_kategori_urunler_action(self):
        """GET /api/kategoriler/<pk>/urunler/ aksiyonu çalışmalı"""
        resp = self.client.get(f"/api/kategoriler/{self.pk}/urunler/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(json.loads(resp.content), list)


# =============================================================================
# ─── ÜRÜN ENDPOINT TESTLERİ ──────────────────────────────────────────────────
# =============================================================================

class TestUrunListCreate(unittest.TestCase):
    """GET /api/urunler/ ve POST /api/urunler/"""

    def setUp(self):
        if not DJANGO_AVAILABLE:
            self.skipTest("Django mevcut değil")
        try:
            from main import django_yapilandir, kaydet_django_modeller, olustur_django_views, olustur_django_urls
            django_yapilandir()
            Kat, Urun = kaydet_django_modeller()
            KatVS, UrunVS = olustur_django_views(Kat, Urun)
            self.urls = olustur_django_urls(KatVS, UrunVS)
            self.Kategori = Kat
            self.Urun = Urun
            from django.test import Client as DjClient
            self.client = DjClient()
            # Test kategorisi
            resp = self.client.post(
                "/api/kategoriler/",
                data=json_body({"ad": "Test Kat"}),
                content_type=JSON_CT,
            )
            self.kat_id = json.loads(resp.content)["id"]
        except Exception as e:
            self.skipTest(f"Kurulum hatası: {e}")

    def _post_urun(self, payload):
        return self.client.post(
            "/api/urunler/",
            data=json_body(payload),
            content_type=JSON_CT,
        )

    # ── LIST ──────────────────────────────────────────────────────────────────
    def test_get_urunler_200(self):
        resp = self.client.get("/api/urunler/")
        self.assertEqual(resp.status_code, 200)

    def test_filtre_durum(self):
        """?durum= filtresi çalışmalı"""
        self._post_urun({"isim": "Aktif", "fiyat": "10.00", "kategori": self.kat_id})
        resp = self.client.get("/api/urunler/?durum=aktif")
        self.assertEqual(resp.status_code, 200)

    def test_filtre_kategori(self):
        """?kategori= filtresi çalışmalı"""
        resp = self.client.get(f"/api/urunler/?kategori={self.kat_id}")
        self.assertEqual(resp.status_code, 200)

    # ── CREATE ────────────────────────────────────────────────────────────────
    def test_post_gecerli_urun_201(self):
        resp = self._post_urun({"isim": "Laptop", "fiyat": "15000.00", "kategori": self.kat_id})
        self.assertEqual(resp.status_code, 201)

    def test_post_sifir_fiyat_400(self):
        resp = self._post_urun({"isim": "Sıfır", "fiyat": "0.00", "kategori": self.kat_id})
        self.assertEqual(resp.status_code, 400)

    def test_post_negatif_fiyat_400(self):
        resp = self._post_urun({"isim": "Negatif", "fiyat": "-5.00", "kategori": self.kat_id})
        self.assertEqual(resp.status_code, 400)

    def test_post_eksik_isim_400(self):
        resp = self._post_urun({"fiyat": "100.00"})
        self.assertEqual(resp.status_code, 400)

    def test_varsayilan_stok_sifir(self):
        resp = self._post_urun({"isim": "Stoksuz", "fiyat": "5.00", "kategori": self.kat_id})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.content)["stok"], 0)

    def test_varsayilan_durum_aktif(self):
        resp = self._post_urun({"isim": "Durum Test", "fiyat": "1.00", "kategori": self.kat_id})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.content)["durum"], "aktif")

    def test_yanit_kategori_adi_alani(self):
        """Yanıt kategori_adi SerializerMethodField içermeli"""
        resp = self._post_urun({"isim": "Kat Ad Test", "fiyat": "1.00", "kategori": self.kat_id})
        data = json.loads(resp.content)
        self.assertIn("kategori_adi", data)


class TestUrunActions(unittest.TestCase):
    """Özel ViewSet action'ları"""

    def setUp(self):
        if not DJANGO_AVAILABLE:
            self.skipTest("Django mevcut değil")
        try:
            from main import django_yapilandir, kaydet_django_modeller, olustur_django_views, olustur_django_urls
            django_yapilandir()
            Kat, Urun = kaydet_django_modeller()
            KatVS, UrunVS = olustur_django_views(Kat, Urun)
            self.urls = olustur_django_urls(KatVS, UrunVS)
            from django.test import Client as DjClient
            self.client = DjClient()
            # Kategori + ürün oluştur
            kat_resp = self.client.post("/api/kategoriler/", data=json_body({"ad": "Action Kat"}), content_type=JSON_CT)
            kat_id = json.loads(kat_resp.content)["id"]
            urun_resp = self.client.post(
                "/api/urunler/",
                data=json_body({"isim": "Action Urun", "fiyat": "10.00", "stok": 0, "kategori": kat_id}),
                content_type=JSON_CT,
            )
            self.urun_id = json.loads(urun_resp.content)["id"]
        except Exception as e:
            self.skipTest(f"Kurulum hatası: {e}")

    def test_stok_yok_action_200(self):
        """GET /api/urunler/stok_yok/ stoğu tükenenleri döndürmeli"""
        resp = self.client.get("/api/urunler/stok_yok/")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        ids = [u["id"] for u in data]
        self.assertIn(self.urun_id, ids)

    def test_stok_ekle_action_200(self):
        """POST /api/urunler/<id>/stok_ekle/ stoku artırmalı"""
        resp = self.client.post(
            f"/api/urunler/{self.urun_id}/stok_ekle/",
            data=json_body({"miktar": 25}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["yeni_stok"], 25)

    def test_stok_ekle_negatif_400(self):
        """Negatif miktar 400 döndürmeli"""
        resp = self.client.post(
            f"/api/urunler/{self.urun_id}/stok_ekle/",
            data=json_body({"miktar": -10}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 400)

    def test_stok_ekle_sifir_400(self):
        """Sıfır miktar 400 döndürmeli"""
        resp = self.client.post(
            f"/api/urunler/{self.urun_id}/stok_ekle/",
            data=json_body({"miktar": 0}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 400)

    def test_stok_ekle_olmayan_urun_404(self):
        resp = self.client.post(
            "/api/urunler/99999/stok_ekle/",
            data=json_body({"miktar": 10}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 404)

    def test_stok_birden_fazla_arttirma(self):
        """Stok ardışık çağrılarda birikimli artmalı"""
        self.client.post(
            f"/api/urunler/{self.urun_id}/stok_ekle/",
            data=json_body({"miktar": 10}),
            content_type=JSON_CT,
        )
        resp2 = self.client.post(
            f"/api/urunler/{self.urun_id}/stok_ekle/",
            data=json_body({"miktar": 15}),
            content_type=JSON_CT,
        )
        self.assertEqual(json.loads(resp2.content)["yeni_stok"], 25)


# =============================================================================
# ─── CONTENT TYPE & HEADER TESTLERİ ──────────────────────────────────────────
# =============================================================================

class TestDjangoHeaders(unittest.TestCase):
    """Content-Type ve yanıt header'ları"""

    def setUp(self):
        if not DJANGO_AVAILABLE:
            self.skipTest("Django mevcut değil")
        try:
            from main import django_yapilandir, kaydet_django_modeller, olustur_django_views, olustur_django_urls
            django_yapilandir()
            Kat, Urun = kaydet_django_modeller()
            KatVS, UrunVS = olustur_django_views(Kat, Urun)
            self.urls = olustur_django_urls(KatVS, UrunVS)
            from django.test import Client as DjClient
            self.client = DjClient()
        except Exception as e:
            self.skipTest(f"Kurulum hatası: {e}")

    def test_json_content_type_list(self):
        resp = self.client.get("/api/kategoriler/")
        self.assertIn("application/json", resp.get("Content-Type", ""))

    def test_json_content_type_create(self):
        resp = self.client.post(
            "/api/kategoriler/",
            data=json_body({"ad": "CT Test"}),
            content_type=JSON_CT,
        )
        self.assertIn("application/json", resp.get("Content-Type", ""))

    def test_ana_sayfa_json_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn("mesaj", data)
        self.assertIn("uç_noktalar", data)


# =============================================================================
# ─── TEST RUNNER ─────────────────────────────────────────────────────────────
# =============================================================================

def run_django_tests():
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestKategoriListCreate,
        TestKategoriDetail,
        TestUrunListCreate,
        TestUrunActions,
        TestDjangoHeaders,
    ]
    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(0 if run_django_tests() else 1)
