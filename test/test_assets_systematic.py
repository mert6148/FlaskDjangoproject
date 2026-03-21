#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assests Modülü Sistematik Kontroller
UI/ML/AI/OS konfigürasyonlarında kullanıcı girişleri için kapsamlı testler
"""

import sys
import json
import unittest
from pathlib import Path
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
        validate_user_assets_batch,
        ASSET_CATEGORY_PROFILE,
        ASSET_CATEGORY_PREFERENCES,
        ASSET_CATEGORY_SECURITY,
        ASSET_CATEGORY_SYSTEM,
        ASSET_CATEGORY_CUSTOM,
        VALID_ASSET_CATEGORIES
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")
    MODULES_AVAILABLE = False


class TestAssetsSystematicValidation(unittest.TestCase):
    """Assests modülü sistematik validasyon testleri"""
    
    def setUp(self):
        """Test öncesi hazırlık"""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
        
        # Test veritabanı
        self.test_db = ":memory:"
        login_system.DB_FILE = self.test_db
        login_system.init_db()
        
        # Test kullanıcısı oluştur
        self.test_username = "testuser_assets"
        self.test_password = "Test123!@#"
        login_system.create_user(self.test_username, self.test_password, "Test User")
        
        # User ID al
        conn = login_system.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (self.test_username,))
        user = c.fetchone()
        conn.close()
        
        if user:
            self.user_id = user[0]
            self.asset_manager = UserAssetManager(self.test_db)
            self.validator = AssetSchemaValidator()
        else:
            self.skipTest("Test kullanıcısı oluşturulamadı")
    
    def test_profile_assets_validation(self):
        """Profil asset'leri validasyonu"""
        profile_assets = {
            "first_name": "Ahmet",
            "last_name": "Yılmaz",
            "email": "ahmet@example.com",
            "phone": "+90-555-123-4567"
        }
        
        all_valid, errors = validate_user_assets_batch(
            self.asset_manager,
            {ASSET_CATEGORY_PROFILE: profile_assets}
        )
        
        self.assertTrue(all_valid, f"Profil asset'leri geçersiz: {errors}")
    
    def test_preferences_assets_validation(self):
        """Tercih asset'leri validasyonu"""
        preference_assets = {
            "theme": "dark",
            "language": "tr_TR",
            "timezone": "Europe/Istanbul"
        }
        
        all_valid, errors = validate_user_assets_batch(
            self.asset_manager,
            {ASSET_CATEGORY_PREFERENCES: preference_assets}
        )
        
        self.assertTrue(all_valid, f"Tercih asset'leri geçersiz: {errors}")
    
    def test_security_assets_validation(self):
        """Güvenlik asset'leri validasyonu"""
        security_assets = {
            "two_factor_enabled": "true",
            "login_attempts": "3",
            "account_locked": "false"
        }
        
        all_valid, errors = validate_user_assets_batch(
            self.asset_manager,
            {ASSET_CATEGORY_SECURITY: security_assets}
        )
        
        self.assertTrue(all_valid, f"Güvenlik asset'leri geçersiz: {errors}")
    
    def test_system_assets_validation(self):
        """Sistem asset'leri validasyonu"""
        system_assets = {
            "ip_address": "192.168.1.100",
            "login_count": "42",
            "last_login": "2024-01-15T10:30:00"
        }
        
        all_valid, errors = validate_user_assets_batch(
            self.asset_manager,
            {ASSET_CATEGORY_SYSTEM: system_assets}
        )
        
        self.assertTrue(all_valid, f"Sistem asset'leri geçersiz: {errors}")
    
    def test_invalid_email_rejection(self):
        """Geçersiz e-posta reddi"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@domain"
        ]
        
        for email in invalid_emails:
            is_valid, _ = validate_schema_with_conditions(
                self.asset_manager,
                ASSET_CATEGORY_PROFILE,
                "email",
                email
            )
            self.assertFalse(is_valid, f"Geçersiz e-posta kabul edildi: {email}")
    
    def test_invalid_login_attempts_rejection(self):
        """Geçersiz login_attempts reddi"""
        # Max değer 10, 15 geçersiz olmalı
        is_valid, _ = validate_schema_with_conditions(
            self.asset_manager,
            ASSET_CATEGORY_SECURITY,
            "login_attempts",
            "15"
        )
        self.assertFalse(is_valid, "Max değeri aşan login_attempts kabul edilmemeli")
    
    def test_asset_crud_operations(self):
        """Asset CRUD işlemleri testi"""
        # Create
        result = self.asset_manager.set_asset(
            self.user_id,
            "test_asset",
            "test_value",
            "string",
            ASSET_CATEGORY_CUSTOM
        )
        self.assertTrue(result, "Asset oluşturulamadı")
        
        # Read
        asset = self.asset_manager.get_asset(self.user_id, "test_asset")
        self.assertIsNotNone(asset, "Asset okunamadı")
        self.assertEqual(asset.asset_value, "test_value", "Asset değeri yanlış")
        
        # Update
        result = self.asset_manager.set_asset(
            self.user_id,
            "test_asset",
            "updated_value",
            "string",
            ASSET_CATEGORY_CUSTOM
        )
        self.assertTrue(result, "Asset güncellenemedi")
        
        asset = self.asset_manager.get_asset(self.user_id, "test_asset")
        self.assertEqual(asset.asset_value, "updated_value", "Asset güncellenemedi")
        
        # Delete
        result = self.asset_manager.delete_asset(self.user_id, "test_asset")
        self.assertTrue(result, "Asset silinemedi")
        
        asset = self.asset_manager.get_asset(self.user_id, "test_asset")
        self.assertIsNone(asset, "Asset silinmedi")
    
    def test_batch_asset_operations(self):
        """Toplu asset işlemleri testi"""
        batch_assets = {
            ASSET_CATEGORY_PROFILE: {
                "first_name": "Batch",
                "email": "batch@example.com"
            },
            ASSET_CATEGORY_PREFERENCES: {
                "theme": "light"
            }
        }
        
        # Validasyon
        all_valid, errors = validate_user_assets_batch(
            self.asset_manager,
            batch_assets
        )
        self.assertTrue(all_valid, f"Toplu validasyon başarısız: {errors}")
        
        # Kaydetme
        from assests.assest import process_validated_assets
        success, failed = process_validated_assets(
            self.asset_manager,
            self.user_id,
            batch_assets
        )
        self.assertTrue(success, f"Toplu kayıt başarısız: {failed}")
        
        # Geri alma
        all_assets = self.asset_manager.get_all_assets(self.user_id)
        self.assertGreater(len(all_assets), 0, "Asset'ler geri alınamadı")


class TestAssetsIntegration(unittest.TestCase):
    """Assests modülü entegrasyon testleri"""
    
    def test_assets_with_login_system(self):
        """Login sistemi ile asset entegrasyonu"""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
        
        # Test veritabanı
        test_db = ":memory:"
        login_system.DB_FILE = test_db
        login_system.init_db()
        
        # Kullanıcı oluştur
        username = "integration_test"
        password = "Test123!@#"
        login_system.create_user(username, password, "Integration Test")
        
        # User ID al
        conn = login_system.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            self.skipTest("Kullanıcı oluşturulamadı")
        
        user_id = user[0]
        asset_manager = UserAssetManager(test_db)
        
        # Asset ekle
        result = asset_manager.set_asset(
            user_id,
            "integration_test_asset",
            "test_value",
            "string",
            ASSET_CATEGORY_CUSTOM
        )
        self.assertTrue(result, "Asset eklenemedi")
        
        # Asset oku
        asset = asset_manager.get_asset(user_id, "integration_test_asset")
        self.assertIsNotNone(asset, "Asset okunamadı")
    
    def test_assets_schema_consistency(self):
        """Asset şema tutarlılığı"""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
        
        validator = AssetSchemaValidator()
        
        # Tüm kategoriler için şema kontrolü
        for category in VALID_ASSET_CATEGORIES:
            schema = validator.schema.get(category, {})
            self.assertIsInstance(schema, dict,
                                f"{category} kategorisi için şema dict olmalı")


class TestAssetsFileStructure(unittest.TestCase):
    """Assests dosya yapısı testleri"""
    
    def test_asset_module_files(self):
        """Asset modül dosyaları kontrolü"""
        required_files = [
            "assests/assest.py",
            "assests/assets.json"
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            if path.exists():
                self.assertTrue(path.is_file(), f"{file_path} dosya olmalı")
                self.assertGreater(path.stat().st_size, 0,
                                 f"{file_path} boş olmamalı")
    
    def test_schema_files(self):
        """Şema dosyaları kontrolü"""
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


def run_assets_tests():
    """Assests testlerini çalıştır"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestAssetsSystematicValidation,
        TestAssetsIntegration,
        TestAssetsFileStructure
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_assets_tests()
    sys.exit(0 if success else 1)

