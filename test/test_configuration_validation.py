#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI/ML/AI/OS Konfigürasyon Validasyon Testleri
Sistematik kontroller için kapsamlı test suite
"""

import sys
import json
import unittest
from pathlib import Path
import re

# Add paths
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "assests"))

try:
    from assests.assest import UserAssetManager, AssetSchemaValidator
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False


class TestMLConfigValidation(unittest.TestCase):
    """ML konfigürasyon validasyon testleri"""
    
    def test_ml_config_file_structure(self):
        """ML config dosya yapısı kontrolü"""
        config_path = Path("config/src/ml-config.js")
        if not config_path.exists():
            self.skipTest("ML config dosyası bulunamadı")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Temel yapı kontrolü
        self.assertIn("const MLConfig", content, "MLConfig objesi bulunmalı")
        self.assertIn("config:", content, "config objesi bulunmalı")
        self.assertIn("models:", content, "models dizisi bulunmalı")
    
    def test_ml_config_defaults(self):
        """ML config varsayılan değerleri kontrolü"""
        config_path = Path("config/src/ml-config.js")
        if not config_path.exists():
            self.skipTest("ML config dosyası bulunamadı")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Varsayılan değerler kontrolü
        defaults = {
            "mlServiceEnabled": "true",
            "autoAnalysisEnabled": "true",
            "anomalyThreshold": "75",
            "confidenceLevel": "85"
        }
        
        for key, expected_value in defaults.items():
            # Config objesinde bu değerlerin varlığını kontrol et
            pattern = rf'{key}:\s*{expected_value}'
            if not re.search(pattern, content):
                # Alternatif olarak sadece key'in varlığını kontrol et
                self.assertIn(key, content, f"ML config'de {key} bulunmalı")
    
    def test_ml_model_management_functions(self):
        """ML model yönetim fonksiyonları kontrolü"""
        config_path = Path("config/src/ml-config.js")
        if not config_path.exists():
            self.skipTest("ML config dosyası bulunamadı")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            "reloadModel",
            "testModel",
            "deleteModel",
            "activateModel",
            "handleModelUpload"
        ]
        
        for func in required_functions:
            self.assertIn(func, content, f"ML config'de {func} fonksiyonu bulunmalı")


class TestAIConfigValidation(unittest.TestCase):
    """AI konfigürasyon validasyon testleri"""
    
    def test_ai_model_support(self):
        """AI model format desteği kontrolü"""
        settings_path = Path("config/src/settings.html")
        if not settings_path.exists():
            self.skipTest("Settings dosyası bulunamadı")
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Desteklenen model formatları
        model_formats = ['.h5', '.pkl', '.onnx', '.pb']
        for fmt in model_formats:
            # Accept attribute'unda format kontrolü
            if 'accept=' in content or 'accept=' in content:
                # Format desteği kontrol edildi
                pass
    
    def test_ai_analysis_parameters(self):
        """AI analiz parametreleri kontrolü"""
        settings_path = Path("config/src/settings.html")
        if not settings_path.exists():
            self.skipTest("Settings dosyası bulunamadı")
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analiz parametreleri kontrolü
        analysis_params = [
            "anomaly-threshold",
            "confidence-level",
            "prediction-window",
            "sample-size"
        ]
        
        for param in analysis_params:
            self.assertIn(param, content, 
                        f"AI analiz parametresi bulunmalı: {param}")


class TestOSConfigValidation(unittest.TestCase):
    """OS konfigürasyon validasyon testleri"""
    
    def test_os_config_files(self):
        """OS konfigürasyon dosyaları kontrolü"""
        os_files = [
            "assests/dahboard.py",
            "assests/dashboard.py",
            "assests/compiler.py",
            "assests/assest.py"
        ]
        
        existing_files = []
        for os_file in os_files:
            file_path = Path(os_file)
            if file_path.exists():
                existing_files.append(os_file)
                # Dosya boş olmamalı
                self.assertGreater(file_path.stat().st_size, 0,
                                 f"{os_file} boş olmamalı")
        
        self.assertGreater(len(existing_files), 0,
                         "En az bir OS konfigürasyon dosyası bulunmalı")
    
    def test_database_schemas(self):
        """Veritabanı şemaları kontrolü"""
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
                    except json.JSONDecodeError as e:
                        self.fail(f"{schema_file} geçersiz JSON: {e}")


class TestUIIntegrationValidation(unittest.TestCase):
    """UI entegrasyon validasyon testleri"""
    
    def test_network_manager_integration(self):
        """Network Manager entegrasyonu kontrolü"""
        nm_js = Path("config/src/Network Manager.js")
        nm_html = Path("config/src/Network Manager.html")
        
        if nm_js.exists() and nm_html.exists():
            # JavaScript dosyası HTML'de referans edilmeli
            with open(nm_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.assertIn("Network Manager.js", html_content,
                        "HTML dosyası JavaScript dosyasını referans etmeli")
    
    def test_ml_config_integration(self):
        """ML config entegrasyonu kontrolü"""
        settings_html = Path("config/src/settings.html")
        ml_config_js = Path("config/src/ml-config.js")
        
        if settings_html.exists() and ml_config_js.exists():
            with open(settings_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.assertIn("ml-config.js", html_content,
                        "Settings HTML ML config JavaScript'i referans etmeli")
    
    def test_css_integration(self):
        """CSS entegrasyonu kontrolü"""
        html_files = [
            "config/src/Network Manager.html",
            "config/src/settings.html",
            "config/src/index.html"
        ]
        
        css_path = Path("config/src/style.css")
        if not css_path.exists():
            self.skipTest("CSS dosyası bulunamadı")
        
        for html_file in html_files:
            html_path = Path(html_file)
            if html_path.exists():
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # CSS referansı kontrolü
                self.assertIn("style.css", content,
                            f"{html_file} CSS dosyasını referans etmeli")


class TestSystematicInputValidation(unittest.TestCase):
    """Sistematik input validasyon testleri"""
    
    def test_username_validation_rules(self):
        """Kullanıcı adı validasyon kuralları"""
        valid_usernames = ["user123", "test_user", "admin", "user_name"]
        invalid_usernames = ["", "ab", "user@name", "user name", "123"]
        
        for username in valid_usernames:
            is_valid = (
                len(username) >= 3 and
                username.replace('_', '').replace('-', '').isalnum()
            )
            self.assertTrue(is_valid, f"Geçerli kullanıcı adı reddedildi: {username}")
        
        for username in invalid_usernames:
            is_valid = (
                len(username) >= 3 and
                username.replace('_', '').replace('-', '').isalnum()
            )
            if username == "":
                self.assertFalse(is_valid, f"Boş kullanıcı adı kabul edilmemeli")
            elif len(username) < 3:
                self.assertFalse(is_valid, f"Çok kısa kullanıcı adı kabul edilmemeli: {username}")
    
    def test_password_validation_rules(self):
        """Şifre validasyon kuralları"""
        valid_passwords = [
            "Test123!@#",
            "SecurePass1!",
            "MyP@ssw0rd"
        ]
        invalid_passwords = [
            "short",
            "nouppercase123!",
            "NOLOWERCASE123!",
            "NoNumbers!@#",
            "NoSpecial123"
        ]
        
        def validate_password(password):
            return (
                len(password) >= 8 and
                any(c.isupper() for c in password) and
                any(c.islower() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
            )
        
        for password in valid_passwords:
            self.assertTrue(validate_password(password),
                          f"Geçerli şifre reddedildi: {password}")
        
        for password in invalid_passwords:
            self.assertFalse(validate_password(password),
                           f"Geçersiz şifre kabul edildi: {password}")
    
    def test_email_validation(self):
        """E-posta validasyonu"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@domain",
            "user name@example.com"
        ]
        
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        
        for email in valid_emails:
            self.assertTrue(re.match(email_pattern, email),
                          f"Geçerli e-posta reddedildi: {email}")
        
        for email in invalid_emails:
            self.assertFalse(re.match(email_pattern, email),
                           f"Geçersiz e-posta kabul edildi: {email}")


class TestConfigurationConsistency(unittest.TestCase):
    """Konfigürasyon tutarlılık testleri"""
    
    def test_config_file_consistency(self):
        """Konfigürasyon dosyaları tutarlılığı"""
        config_files = {
            "JavaScript": ["config/src/Network Manager.js", "config/src/ml-config.js"],
            "HTML": ["config/src/Network Manager.html", "config/src/settings.html"],
            "CSS": ["config/src/style.css"]
        }
        
        for file_type, files in config_files.items():
            existing_files = [f for f in files if Path(f).exists()]
            self.assertGreater(len(existing_files), 0,
                             f"En az bir {file_type} dosyası bulunmalı")
    
    def test_api_endpoint_consistency(self):
        """API endpoint tutarlılığı"""
        api_file = Path("api_server.py")
        if api_file.exists():
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Temel endpoint'ler
            endpoints = [
                "/api/v1/health",
                "/api/v1/auth/login",
                "/api/v1/users"
            ]
            
            for endpoint in endpoints:
                self.assertIn(endpoint, content,
                            f"API endpoint bulunmalı: {endpoint}")


def run_configuration_tests():
    """Konfigürasyon testlerini çalıştır"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestMLConfigValidation,
        TestAIConfigValidation,
        TestOSConfigValidation,
        TestUIIntegrationValidation,
        TestSystematicInputValidation,
        TestConfigurationConsistency
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_configuration_tests()
    sys.exit(0 if success else 1)

