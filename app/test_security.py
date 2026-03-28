#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_security.py — Flask & Django Güvenlik Katmanı Testleri
Şifre, JWT, giriş kilitleme, XSS/SQL koruması, şifreli alan testleri.
"""

import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Modül kontrolleri ─────────────────────────────────────────────────────────
try:
    from flask_security import (
        SifreYoneticisi, JWTYoneticisi,
        temizle, email_gecerli, kullanici_adi_gecerli,
        sql_enjeksiyonu_var_mi, create_flask_app,
    )
    FLASK_SEC_AVAILABLE = True
except ImportError:
    FLASK_SEC_AVAILABLE = False

try:
    from django_db_security import (
        SifreliAlanYoneticisi, DBGuvenlikKontrolcu,
        CRYPTO_AVAILABLE, DJANGO_AVAILABLE,
    )
    DJANGO_SEC_AVAILABLE = True
except ImportError:
    DJANGO_SEC_AVAILABLE = False

JSON_CT = "application/json"


# ═════════════════════════════════════════════════════════════════════════════
# ŞİFRE YÖNETİCİSİ TESTLERİ
# ═════════════════════════════════════════════════════════════════════════════

class TestSifreYoneticisi(unittest.TestCase):

    def setUp(self):
        if not FLASK_SEC_AVAILABLE:
            self.skipTest("flask_security modülü yok")

    # ── Hash & Doğrulama ──────────────────────────────────────────────────────
    def test_hashle_farkli_tuz_uretir(self):
        h1, t1 = SifreYoneticisi.hashle("ayni_sifre")
        h2, t2 = SifreYoneticisi.hashle("ayni_sifre")
        self.assertNotEqual(t1, t2, "Her çağrıda farklı tuz üretilmeli")
        self.assertNotEqual(h1, h2, "Farklı tuzlar farklı hash üretmeli")

    def test_dogrula_dogru_sifre(self):
        h, t = SifreYoneticisi.hashle("Test123!@#")
        self.assertTrue(SifreYoneticisi.dogrula("Test123!@#", h, t))

    def test_dogrula_yanlis_sifre(self):
        h, t = SifreYoneticisi.hashle("DogruSifre1!")
        self.assertFalse(SifreYoneticisi.dogrula("YanlisSifre1!", h, t))

    def test_dogrula_yanlis_tuz(self):
        h, t = SifreYoneticisi.hashle("Test123!@#")
        self.assertFalse(SifreYoneticisi.dogrula("Test123!@#", h, "yanlistuz" * 4))

    def test_hash_uzunluk_yeterli(self):
        h, t = SifreYoneticisi.hashle("Test123!@#")
        self.assertGreater(len(h), 32, "Hash en az 32 karakter olmalı")
        self.assertGreater(len(t), 16, "Tuz en az 16 karakter olmalı")

    # ── Güç Kuralları ─────────────────────────────────────────────────────────
    def test_guclu_sifre_kabul(self):
        for sifre in ["Test123!@#", "Guvenli$1Pass", "A@b3cD#eFg"]:
            ok, hatalar = SifreYoneticisi.guclu_mu(sifre)
            self.assertTrue(ok, f"Güçlü şifre reddedildi: {sifre} — {hatalar}")

    def test_kisa_sifre_red(self):
        ok, hatalar = SifreYoneticisi.guclu_mu("Ab1!")
        self.assertFalse(ok)
        self.assertTrue(any("karakter" in h for h in hatalar))

    def test_sadece_rakam_red(self):
        ok, hatalar = SifreYoneticisi.guclu_mu("12345678")
        self.assertFalse(ok)

    def test_buyuk_harf_eksik_red(self):
        ok, hatalar = SifreYoneticisi.guclu_mu("test123!@#")
        self.assertFalse(ok)
        self.assertTrue(any("büyük" in h for h in hatalar))

    def test_ozel_karakter_eksik_red(self):
        ok, hatalar = SifreYoneticisi.guclu_mu("TestSifre123")
        self.assertFalse(ok)
        self.assertTrue(any("özel" in h for h in hatalar))

    def test_bos_sifre_red(self):
        ok, hatalar = SifreYoneticisi.guclu_mu("")
        self.assertFalse(ok)
        self.assertGreater(len(hatalar), 0)


# ═════════════════════════════════════════════════════════════════════════════
# GİRİŞ DOĞRULAMA TESTLERİ
# ═════════════════════════════════════════════════════════════════════════════

class TestGirisDogrulama(unittest.TestCase):

    def setUp(self):
        if not FLASK_SEC_AVAILABLE:
            self.skipTest("flask_security modülü yok")

    # ── E-posta ───────────────────────────────────────────────────────────────
    def test_gecerli_emailler(self):
        for email in ["user@example.com", "a.b+c@domain.co.uk", "x@y.tr"]:
            self.assertTrue(email_gecerli(email), f"Geçerli e-posta reddedildi: {email}")

    def test_gecersiz_emailler(self):
        for email in ["", "abc", "@domain.com", "user@", "user @x.com", None]:
            self.assertFalse(email_gecerli(email), f"Geçersiz e-posta kabul edildi: {email}")

    # ── Kullanıcı adı ─────────────────────────────────────────────────────────
    def test_gecerli_kullanici_adlari(self):
        for kad in ["ahmet", "user_123", "Test-User", "abc"]:
            self.assertTrue(kullanici_adi_gecerli(kad), f"Geçerli KAD reddedildi: {kad}")

    def test_gecersiz_kullanici_adlari(self):
        for kad in ["", "ab", "a" * 31, "user@name", "user name", None]:
            self.assertFalse(kullanici_adi_gecerli(kad), f"Geçersiz KAD kabul edildi: {kad}")

    # ── SQL Enjeksiyonu ───────────────────────────────────────────────────────
    def test_sql_enjeksiyonu_tespiti(self):
        tehlikeli = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "1; DELETE FROM users",
        ]
        for deger in tehlikeli:
            self.assertTrue(
                sql_enjeksiyonu_var_mi(deger),
                f"SQL enjeksiyonu tespit edilmedi: {deger}",
            )

    def test_temiz_deger_gecerli(self):
        temiz_degerler = ["ahmet yilmaz", "normal metin", "12345", "test@x.com"]
        for deger in temiz_degerler:
            self.assertFalse(
                sql_enjeksiyonu_var_mi(deger),
                f"Temiz değer hatalı işaretlendi: {deger}",
            )

    # ── Temizleme ─────────────────────────────────────────────────────────────
    def test_xss_temizleme(self):
        kirli = "<script>alert('xss')</script>Merhaba"
        temiz_sonuc = temizle(kirli)
        self.assertNotIn("<script>", temiz_sonuc)
        self.assertIn("Merhaba", temiz_sonuc)

    def test_max_uzunluk_kisaltma(self):
        uzun = "a" * 1000
        self.assertLessEqual(len(temizle(uzun, max_uzunluk=100)), 100)

    def test_none_temizleme(self):
        self.assertEqual(temizle(None), "")

    def test_javascript_protokol_temizleme(self):
        kirli = "javascript:alert(1)"
        sonuc = temizle(kirli)
        self.assertNotIn("javascript:", sonuc)


# ═════════════════════════════════════════════════════════════════════════════
# FLASK API GÜVENLİK TESTLERİ
# ═════════════════════════════════════════════════════════════════════════════

class TestFlaskAPIGuvenlik(unittest.TestCase):

    def setUp(self):
        if not FLASK_SEC_AVAILABLE:
            self.skipTest("flask_security modülü yok")
        app = create_flask_app()
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        from flask_security import db
        db.create_all()

    def tearDown(self):
        if hasattr(self, "ctx"):
            self.ctx.pop()

    def _kayit(self, kad="testuser", email="test@test.com", sifre="Test123!@#"):
        return self.client.post(
            "/api/auth/kayit",
            data=json.dumps({"kullanici_adi": kad, "email": email, "sifre": sifre}),
            content_type=JSON_CT,
        )

    def _giris(self, kad="testuser", sifre="Test123!@#"):
        return self.client.post(
            "/api/auth/giris",
            data=json.dumps({"kullanici_adi": kad, "sifre": sifre}),
            content_type=JSON_CT,
        )

    # ── Kayıt ─────────────────────────────────────────────────────────────────
    def test_gecerli_kayit_201(self):
        resp = self._kayit()
        self.assertEqual(resp.status_code, 201)

    def test_duplikat_kayit_409(self):
        self._kayit()
        resp = self._kayit()
        self.assertEqual(resp.status_code, 409)

    def test_zayif_sifre_kayit_400(self):
        resp = self._kayit(sifre="zayif")
        self.assertEqual(resp.status_code, 400)

    def test_gecersiz_email_kayit_400(self):
        resp = self._kayit(email="gecersiz-email")
        self.assertEqual(resp.status_code, 400)

    def test_kisa_kullanici_adi_400(self):
        resp = self._kayit(kad="ab")
        self.assertEqual(resp.status_code, 400)

    def test_xss_kullanici_adi_400(self):
        resp = self._kayit(kad="<script>xss</script>")
        self.assertEqual(resp.status_code, 400)

    def test_sql_enjeksiyonu_kayit_400(self):
        resp = self._kayit(kad="'; DROP TABLE kullanicilar; --")
        self.assertEqual(resp.status_code, 400)

    # ── Giriş ─────────────────────────────────────────────────────────────────
    def test_gecerli_giris_200(self):
        self._kayit()
        resp = self._giris()
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("token", data)

    def test_yanlis_sifre_401(self):
        self._kayit()
        resp = self._giris(sifre="YanlisSifre1!")
        self.assertEqual(resp.status_code, 401)

    def test_olmayan_kullanici_401(self):
        resp = self._giris(kad="yokkullanici")
        self.assertEqual(resp.status_code, 401)

    def test_bos_sifre_400(self):
        resp = self.client.post(
            "/api/auth/giris",
            data=json.dumps({"kullanici_adi": "testuser", "sifre": ""}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.status_code, 400)

    # ── JWT ────────────────────────────────────────────────────────────────────
    def test_token_ile_profil_erisim(self):
        self._kayit()
        resp = self._giris()
        token = json.loads(resp.data).get("token")
        if not token:
            self.skipTest("Token üretilemedi (PyJWT eksik?)")
        profil = self.client.get(
            "/api/kullanici/profil",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(profil.status_code, 200)

    def test_token_olmadan_profil_401(self):
        resp = self.client.get("/api/kullanici/profil")
        self.assertEqual(resp.status_code, 401)

    def test_sahte_token_401(self):
        resp = self.client.get(
            "/api/kullanici/profil",
            headers={"Authorization": "Bearer sahte.token.burada"},
        )
        self.assertEqual(resp.status_code, 401)

    # ── Güvenlik Başlıkları ────────────────────────────────────────────────────
    def test_guvenlik_basliklari_mevcut(self):
        resp = self.client.get("/api/auth/giris", method="OPTIONS")
        beklenen_basliklar = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
        ]
        # GET isteği ile kontrol edelim
        resp2 = self.client.post(
            "/api/auth/giris",
            data=json.dumps({"kullanici_adi": "x", "sifre": "y"}),
            content_type=JSON_CT,
        )
        for baslik in beklenen_basliklar:
            self.assertIn(baslik, resp2.headers,
                         f"Güvenlik başlığı eksik: {baslik}")

    def test_x_frame_options_deny(self):
        resp = self.client.post(
            "/api/auth/giris",
            data=json.dumps({"kullanici_adi": "x", "sifre": "y"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")

    def test_content_type_options_nosniff(self):
        resp = self.client.post(
            "/api/auth/giris",
            data=json.dumps({"kullanici_adi": "x", "sifre": "y"}),
            content_type=JSON_CT,
        )
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")

    # ── İçerik Türü ────────────────────────────────────────────────────────────
    def test_yalnizca_json_kabul(self):
        resp = self.client.post(
            "/api/auth/giris",
            data="kullanici_adi=user&sifre=pass",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(resp.status_code, 415)

    def test_text_plain_reddedilir(self):
        resp = self.client.post(
            "/api/auth/kayit",
            data='{"kullanici_adi":"test","email":"t@t.com","sifre":"Test1!aA"}',
            content_type="text/plain",
        )
        self.assertEqual(resp.status_code, 415)

    # ── Brute-force kilitleme simülasyonu ──────────────────────────────────────
    def test_basarisiz_giris_hata_mesaji(self):
        """Başarısız girişlerde kalan deneme hakkı bilgisi verilmeli"""
        self._kayit()
        resp = self._giris(sifre="YanlisSifre1!")
        data = json.loads(resp.data)
        self.assertIn("hata", data)


# ═════════════════════════════════════════════════════════════════════════════
# DJANGO DB GÜVENLİK TESTLERİ (kütüphane bazlı, DB gerektirmez)
# ═════════════════════════════════════════════════════════════════════════════

class TestDjangoDBGuvenlik(unittest.TestCase):

    def setUp(self):
        if not DJANGO_SEC_AVAILABLE:
            self.skipTest("django_db_security modülü yok")

    # ── Şifreli Alan ──────────────────────────────────────────────────────────
    def test_sifreli_alan_cozme(self):
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography kütüphanesi yok")
        from cryptography.fernet import Fernet
        anahtar = Fernet.generate_key()
        yonetici = SifreliAlanYoneticisi(anahtar)
        ham = "gizli veri 12345"
        sifreli = yonetici.sifrele(ham)
        self.assertNotEqual(sifreli, ham)
        self.assertEqual(yonetici.coz(sifreli), ham)

    def test_sifreli_alan_farkli_cikti(self):
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography kütüphanesi yok")
        from cryptography.fernet import Fernet
        anahtar = Fernet.generate_key()
        yonetici = SifreliAlanYoneticisi(anahtar)
        s1 = yonetici.sifrele("ayni_metin")
        s2 = yonetici.sifrele("ayni_metin")
        self.assertNotEqual(s1, s2, "Fernet her seferinde farklı çıktı üretmeli")

    def test_yanlis_anahtar_hata(self):
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography kütüphanesi yok")
        from cryptography.fernet import Fernet
        y1 = SifreliAlanYoneticisi(Fernet.generate_key())
        y2 = SifreliAlanYoneticisi(Fernet.generate_key())
        sifreli = y1.sifrele("gizli")
        with self.assertRaises(ValueError):
            y2.coz(sifreli)

    def test_bozuk_veri_hata(self):
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography kütüphanesi yok")
        from cryptography.fernet import Fernet
        yonetici = SifreliAlanYoneticisi(Fernet.generate_key())
        with self.assertRaises(Exception):
            yonetici.coz("bozuk_base64_verisi!!!!")

    def test_alan_imza_dogrulama(self):
        if not CRYPTO_AVAILABLE:
            self.skipTest("cryptography kütüphanesi yok")
        from cryptography.fernet import Fernet
        yonetici = SifreliAlanYoneticisi(Fernet.generate_key())
        deger  = "kritik_veri"
        gizli  = "imza_gizli_anahtari"
        imza   = yonetici.alan_imzala(deger, gizli)
        self.assertTrue(yonetici.imza_dogrula(deger, imza, gizli))
        self.assertFalse(yonetici.imza_dogrula("degistirilmis", imza, gizli))

    # ── SQL Denetim ───────────────────────────────────────────────────────────
    def test_tehlikeli_sql_tespiti(self):
        tehlikeli_sorgular = [
            "SELECT * FROM users; DROP TABLE users --",
            "SELECT * FROM information_schema.tables",
            "EXEC xp_cmdshell('dir')",
            "SELECT * FROM users WHERE 1=1 -- ",
        ]
        for sorgu in tehlikeli_sorgular:
            temiz, uyarilar = DBGuvenlikKontrolcu.ham_sorgu_denetle(sorgu)
            self.assertFalse(temiz, f"Tehlikeli sorgu tespit edilmedi: {sorgu}")
            self.assertGreater(len(uyarilar), 0)

    def test_temiz_sql_gecerli(self):
        temiz_sorgular = [
            "SELECT id, ad FROM kullanicilar WHERE aktif = %s",
            "INSERT INTO urunler (isim, fiyat) VALUES (%s, %s)",
            "UPDATE kullanicilar SET son_giris = %s WHERE id = %s",
        ]
        for sorgu in temiz_sorgular:
            temiz, uyarilar = DBGuvenlikKontrolcu.ham_sorgu_denetle(sorgu)
            self.assertTrue(temiz, f"Temiz sorgu hatalı işaretlendi: {sorgu} — {uyarilar}")

    def test_parametre_sayisi_dogrulama(self):
        self.assertTrue(
            DBGuvenlikKontrolcu.parametre_sayisi_dogrula(
                "SELECT * FROM t WHERE id = %s AND aktif = %s", (1, True)
            )
        )
        self.assertFalse(
            DBGuvenlikKontrolcu.parametre_sayisi_dogrula(
                "SELECT * FROM t WHERE id = %s", (1, 2)
            )
        )


# ═════════════════════════════════════════════════════════════════════════════
# BÜTÜNLEŞIK GÜVENLİK TESTLERİ
# ═════════════════════════════════════════════════════════════════════════════

class TestButunlesikGuvenlik(unittest.TestCase):
    """Flask + Django güvenlik katmanlarının birlikte çalışma kontrolü."""

    def test_sifre_hash_tutarliligi(self):
        if not FLASK_SEC_AVAILABLE:
            self.skipTest("flask_security yok")
        sifre = "Guvenlı_Sifre123!"
        h1, t1 = SifreYoneticisi.hashle(sifre)
        h2, t2 = SifreYoneticisi.hashle(sifre)
        # Farklı tuzlar farklı hash üretmeli
        self.assertNotEqual(h1, h2)
        # Ama her ikisi de doğrulanabilir olmalı
        self.assertTrue(SifreYoneticisi.dogrula(sifre, h1, t1))
        self.assertTrue(SifreYoneticisi.dogrula(sifre, h2, t2))

    def test_guvenlik_basliklari_listesi_eksiksiz(self):
        if not FLASK_SEC_AVAILABLE:
            self.skipTest("flask_security yok")
        app = create_flask_app()
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        with app.test_client() as client:
            with app.app_context():
                from flask_security import db
                db.create_all()
                resp = client.post(
                    "/api/auth/giris",
                    data=json.dumps({"kullanici_adi": "x", "sifre": "y"}),
                    content_type=JSON_CT,
                )
                zorunlu = {
                    "X-Content-Type-Options", "X-Frame-Options",
                    "X-XSS-Protection", "Content-Security-Policy",
                }
                eksik = zorunlu - set(resp.headers.keys())
                self.assertEqual(len(eksik), 0, f"Eksik güvenlik başlıkları: {eksik}")


# ═════════════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═════════════════════════════════════════════════════════════════════════════

def run_security_tests():
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        TestSifreYoneticisi,
        TestGirisDogrulama,
        TestFlaskAPIGuvenlik,
        TestDjangoDBGuvenlik,
        TestButunlesikGuvenlik,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(0 if run_security_tests() else 1)
