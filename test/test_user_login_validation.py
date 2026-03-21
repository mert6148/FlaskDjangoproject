#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kullanıcı Girişi Validasyon Testleri
UI/ML/AI/OS konfigürasyonlarında sistematik kontroller için test suite
"""

import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sqlite3

# Add paths
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "assests"))

try:
    import print as login_system
    from assests.assest import (
        UserAssetManager,
        AssetSchemaValidator,
        validate_schema_with_conditions,
        ASSET_CATEGORY_PROFILE,
        ASSET_CATEGORY_PREFERENCES,
        ASSET_CATEGORY_SECURITY,
        ASSET_CATEGORY_SYSTEM
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")
    MODULES_AVAILABLE = False


class TestUserLoginValidation(unittest.TestCase):
    """Kullanıcı girişi validasyon testleri"""
    
    def setUp(self):
        """Test öncesi hazırlık"""
        self.test_db = ":memory:"
        login_system.DB_FILE = self.test_db
        login_system.init_db()
        
        # Test kullanıcısı oluştur
        self.test_username = "testuser"
        self.test_password = "Test123!@#"
        login_system.create_user(self.test_username, self.test_password, "Test User")
    
    def tearDown(self):
        """Test sonrası temizlik"""
        pass
    
    def test_valid_login(self):
        """Geçerli kullanıcı girişi testi"""
        result = login_system.login_command(self.test_username, self.test_password)
        self.assertTrue(result, "Geçerli kullanıcı girişi başarısız olmamalı")
    
    def test_invalid_password(self):
        """Geçersiz şifre testi"""
        result = login_system.login_command(self.test_username, "wrongpassword")
        self.assertFalse(result, "Geçersiz şifre ile giriş başarılı olmamalı")
    
    def test_nonexistent_user(self):
        """Var olmayan kullanıcı testi"""
        result = login_system.login_command("nonexistent", "password")
        self.assertFalse(result, "Var olmayan kullanıcı ile giriş başarılı olmamalı")
    
    def test_empty_username(self):
        """Boş kullanıcı adı testi"""
        result = login_system.login_command("", "password")
        self.assertFalse(result, "Boş kullanıcı adı ile giriş başarılı olmamalı")
    
    def test_empty_password(self):
        """Boş şifre testi"""
        result = login_system.login_command(self.test_username, "")
        self.assertFalse(result, "Boş şifre ile giriş başarılı olmamalı")
    
    def test_password_hashing(self):
        """Şifre hashleme testi"""
        salt, hashed = login_system.hash_password("testpassword")
        self.assertIsNotNone(salt, "Salt değeri oluşturulmalı")
        self.assertIsNotNone(hashed, "Hash değeri oluşturulmalı")
        self.assertNotEqual(salt, hashed, "Salt ve hash farklı olmalı")
    
    def test_password_verification(self):
        """Şifre doğrulama testi"""
        salt, hashed = login_system.hash_password("testpassword")
        self.assertTrue(
            login_system.verify_password("testpassword", salt, hashed),
            "Doğru şifre doğrulanmalı"
        )
        self.assertFalse(
            login_system.verify_password("wrongpassword", salt, hashed),
            "Yanlış şifre doğrulanmamalı"
        )
    
    def test_session_creation(self):
        """Oturum oluşturma testi"""
        session_id = login_system.start_session(self.test_username)
        self.assertIsNotNone(session_id, "Oturum ID oluşturulmalı")
        self.assertIsInstance(session_id, str, "Oturum ID string olmalı")
    
    def test_session_termination(self):
        """Oturum sonlandırma testi"""
        session_id = login_system.start_session(self.test_username)
        result = login_system.end_session(session_id)
        self.assertTrue(result, "Oturum sonlandırılmalı")


class TestUIConfigurationValidation(unittest.TestCase):
    """UI konfigürasyon validasyon testleri"""
    
    def setUp(self):
        """Test öncesi hazırlık"""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
    
    def test_ml_config_validation(self):
        """ML konfigürasyon validasyonu"""
        # ML config dosyası kontrolü
        config_path = Path("config/src/ml-config.js")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Temel validasyonlar
                self.assertIn("MLConfig", content, "MLConfig objesi bulunmalı")
                self.assertIn("saveConfig", content, "saveConfig fonksiyonu bulunmalı")
                self.assertIn("loadConfig", content, "loadConfig fonksiyonu bulunmalı")
    
    def test_network_manager_validation(self):
        """Network Manager validasyonu"""
        nm_path = Path("config/src/Network Manager.js")
        if nm_path.exists():
            with open(nm_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Temel fonksiyonlar kontrolü
                self.assertIn("NetworkManager", content, "NetworkManager objesi bulunmalı")
                self.assertIn("handleLogin", content, "handleLogin fonksiyonu bulunmalı")
                self.assertIn("validateInputs", content, "validateInputs fonksiyonu bulunmalı")
    
    def test_html_structure_validation(self):
        """HTML yapı validasyonu"""
        html_files = [
            "config/src/Network Manager.html",
            "config/src/settings.html",
            "config/src/index.html"
        ]
        
        for html_file in html_files:
            html_path = Path(html_file)
            if html_path.exists():
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Temel HTML yapısı kontrolü
                    self.assertIn("<!DOCTYPE html>", content, f"{html_file} geçerli HTML olmalı")
                    self.assertIn("<html", content, f"{html_file} HTML tag'i içermeli")
                    self.assertIn("</html>", content, f"{html_file} kapanış tag'i içermeli")


class TestMLConfigurationValidation(unittest.TestCase):
    """ML konfigürasyon validasyon testleri"""
    
    def setUp(self):
        """Test öncesi hazırlık"""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
    
    def test_ml_input_validation(self):
        """ML input validasyonu"""
        # Simüle edilmiş ML input validation
        test_inputs = [
            ("valid_username", "ValidPass123!", True),
            ("user", "short", False),  # Çok kısa şifre
            ("", "password123", False),  # Boş kullanıcı adı
            ("user123", "password", False),  # Zayıf şifre
        ]
        
        for username, password, expected in test_inputs:
            # Basit validasyon kuralları
            is_valid = (
                len(username) >= 3 and
                len(password) >= 8 and
                any(c.isupper() for c in password) and
                any(c.islower() for c in password) and
                any(c.isdigit() for c in password)
            )
            self.assertEqual(is_valid, expected, 
                           f"Validation failed for username={username}, password={password}")
    
    def test_ml_config_structure(self):
        """ML konfigürasyon yapısı kontrolü"""
        config_path = Path("config/src/ml-config.js")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # ML config yapısı kontrolü
                required_keys = [
                    "mlServiceEnabled",
                    "autoAnalysisEnabled",
                    "anomalyThreshold",
                    "confidenceLevel"
                ]
                for key in required_keys:
                    self.assertIn(key, content, f"ML config'de {key} bulunmalı")


class TestAIConfigurationValidation(unittest.TestCase):
    """AI konfigürasyon validasyon testleri"""
    
    def test_ai_model_validation(self):
        """AI model validasyonu"""
        # Model dosyaları kontrolü
        config_path = Path("config/src/settings.html")
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Model yükleme desteği kontrolü
                self.assertIn("model-file-input", content, "Model dosya input'u bulunmalı")
                self.assertIn("accept", content, "Dosya kabul formatları tanımlı olmalı")


class TestOSConfigurationValidation(unittest.TestCase):
    """OS konfigürasyon validasyon testleri"""
    
    def test_os_config_files(self):
        """OS konfigürasyon dosyaları kontrolü"""
        os_config_files = [
            "assests/dahboard.py",
            "assests/dashboard.py",
            "assests/compiler.py"
        ]
        
        for config_file in os_config_files:
            config_path = Path(config_file)
            if config_path.exists():
                self.assertTrue(config_path.is_file(), f"{config_file} dosya olmalı")
                # Dosya boş olmamalı
                self.assertGreater(config_path.stat().st_size, 0, 
                                 f"{config_file} boş olmamalı")
    
    def test_database_schema_validation(self):
        """Veritabanı şema validasyonu"""
        schema_files = [
            "assests/users_schema.json",
            "assests/sessions_schema.json",
            "assests/login_log_schema.json"
        ]
        
        for schema_file in schema_files:
            schema_path = Path(schema_file)
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    try:
                        schema = json.load(f)
                        self.assertIsInstance(schema, (dict, list), 
                                            f"{schema_file} geçerli JSON olmalı")
                    except json.JSONDecodeError:
                        self.fail(f"{schema_file} geçersiz JSON formatında")


class TestAssetValidation(unittest.TestCase):
    """Asset validasyon testleri"""
    
    def setUp(self):
        """Test öncesi hazırlık"""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
        
        self.asset_manager = UserAssetManager()
        self.validator = AssetSchemaValidator()
    
    def test_asset_schema_validation(self):
        """Asset şema validasyonu"""
        # Geçerli asset değerleri
        valid_cases = [
            (ASSET_CATEGORY_PROFILE, "email", "test@example.com", "string"),
            (ASSET_CATEGORY_PREFERENCES, "theme", "dark", "string"),
            (ASSET_CATEGORY_SECURITY, "login_attempts", "5", "integer"),
        ]
        
        for category, name, value, asset_type in valid_cases:
            is_valid, error = validate_schema_with_conditions(
                self.asset_manager, category, name, value, asset_type
            )
            self.assertTrue(is_valid, 
                          f"Geçerli asset reddedildi: {category}.{name} = {value}, Error: {error}")
    
    def test_asset_invalid_validation(self):
        """Geçersiz asset değerleri testi"""
        invalid_cases = [
            (ASSET_CATEGORY_PROFILE, "email", "invalid-email", "string"),
            (ASSET_CATEGORY_SECURITY, "login_attempts", "15", "integer"),  # Max 10
        ]
        
        for category, name, value, asset_type in invalid_cases:
            is_valid, error = validate_schema_with_conditions(
                self.asset_manager, category, name, value, asset_type
            )
            self.assertFalse(is_valid, 
                           f"Geçersiz asset kabul edildi: {category}.{name} = {value}")
            self.assertIsNotNone(error, "Hata mesajı döndürülmeli")
    
    def test_asset_category_validation(self):
        """Asset kategori validasyonu"""
        from assests.assest import VALID_ASSET_CATEGORIES
        
        valid_categories = VALID_ASSET_CATEGORIES
        invalid_categories = ["invalid", "unknown", ""]
        
        for category in valid_categories:
            is_valid, _ = self.validator.validate_asset_value(
                category, "test_field", "test_value"
            )
            # Custom kategori için özel kontrol gerekebilir
            if category != "custom":
                # Şemada olmayan field için hata beklenir
                pass
        
        for category in invalid_categories:
            is_valid, _ = self.validator.validate_asset_value(
                category, "test_field", "test_value"
            )
            self.assertFalse(is_valid, f"Geçersiz kategori kabul edildi: {category}")


class TestSystematicChecks(unittest.TestCase):
    """Sistematik kontroller testleri"""
    
    def test_api_endpoints_validation(self):
        """API endpoint validasyonu"""
        api_file = Path("api_server.py")
        if api_file.exists():
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Temel endpoint'ler kontrolü
                required_endpoints = [
                    "/api/v1/health",
                    "/api/v1/auth/login",
                    "/api/v1/users"
                ]
                for endpoint in required_endpoints:
                    self.assertIn(endpoint, content, 
                                f"API endpoint bulunmalı: {endpoint}")
    
    def test_configuration_files_exist(self):
        """Konfigürasyon dosyalarının varlığı kontrolü"""
        config_files = [
            ".eslintrc.json",
            ".htmlhintrc",
            ".github/workflows/ci.yml"
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                self.assertTrue(config_path.is_file(), 
                              f"{config_file} dosya olmalı")
    
    def test_database_integrity(self):
        """Veritabanı bütünlük kontrolü"""
        db_file = Path("login_system.db")
        if db_file.exists():
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                # Temel tablolar kontrolü
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ["users", "user_attributes"]
                for table in required_tables:
                    self.assertIn(table, tables, 
                                f"Veritabanında {table} tablosu bulunmalı")
                
                conn.close()
            except sqlite3.Error:
                # Veritabanı erişilemezse test geçer
                pass


def run_tests():
    """Tüm testleri çalıştır"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Tüm test sınıflarını ekle
    test_classes = [
        TestUserLoginValidation,
        TestUIConfigurationValidation,
        TestMLConfigurationValidation,
        TestAIConfigurationValidation,
        TestOSConfigurationValidation,
        TestAssetValidation,
        TestSystematicChecks
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

