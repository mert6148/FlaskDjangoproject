"""
Sistem Modeli
Sistem konfigürasyonu ve durumu yönetimi
"""

from datetime import datetime
from typing import Optional, Dict, List
import json
import platform
import psutil


class SystemConfig:
    """Sistem yapılandırması"""
    
    def __init__(self):
        self.app_name = "Flask-Django-SDK"
        self.version = "1.0.0"
        self.environment = "development"
        self.debug = True
        self.timezone = "UTC"
        self.locale = "tr"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.services = {}
        self.features = []

    def to_dict(self) -> Dict:
        """Yapılandırmayı sözlüğe dönüştür"""
        return {
            'app_name': self.app_name,
            'version': self.version,
            'environment': self.environment,
            'debug': self.debug,
            'timezone': self.timezone,
            'locale': self.locale,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'services': self.services,
            'features': self.features
        }

    def to_json(self) -> str:
        """Yapılandırmayı JSON'a dönüştür"""
        return json.dumps(self.to_dict())


class SystemStatus:
    """Sistem durumu"""
    
    def __init__(self):
        self.status = "running"
        self.uptime = 0
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.disk_usage = 0.0
        self.services_running = 0
        self.services_total = 0
        self.last_check = datetime.now()
        self.errors = []
        self.warnings = []

    def get_system_info(self) -> Dict:
        """Sistem bilgisini al"""
        try:
            return {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'processor': platform.processor(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def to_dict(self) -> Dict:
        """Durumu sözlüğe dönüştür"""
        return {
            'status': self.status,
            'uptime': self.uptime,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'services_running': self.services_running,
            'services_total': self.services_total,
            'last_check': self.last_check.isoformat(),
            'errors': self.errors,
            'warnings': self.warnings,
            'system_info': self.get_system_info()
        }

    def to_json(self) -> str:
        """Durumu JSON'a dönüştür"""
        return json.dumps(self.to_dict())

    def add_error(self, error: str) -> None:
        """Hata ekle"""
        self.errors.append({
            'timestamp': datetime.now().isoformat(),
            'message': error
        })

    def add_warning(self, warning: str) -> None:
        """Uyarı ekle"""
        self.warnings.append({
            'timestamp': datetime.now().isoformat(),
            'message': warning
        })

    def clear_errors(self) -> None:
        """Hataları temizle"""
        self.errors.clear()

    def clear_warnings(self) -> None:
        """Uyarıları temizle"""
        self.warnings.clear()


class ServiceManager:
    """Servis yöneticisi"""
    
    def __init__(self):
        self.services: Dict = {}

    def register_service(self, name: str, service_config: Dict) -> None:
        """Servis kaydetme"""
        self.services[name] = {
            **service_config,
            'registered_at': datetime.now().isoformat(),
            'status': 'registered'
        }

    def start_service(self, name: str) -> bool:
        """Servisi başlat"""
        if name in self.services:
            self.services[name]['status'] = 'running'
            self.services[name]['started_at'] = datetime.now().isoformat()
            return True
        return False

    def stop_service(self, name: str) -> bool:
        """Servisi durdur"""
        if name in self.services:
            self.services[name]['status'] = 'stopped'
            self.services[name]['stopped_at'] = datetime.now().isoformat()
            return True
        return False

    def get_service(self, name: str) -> Optional[Dict]:
        """Servisi al"""
        return self.services.get(name)

    def get_all_services(self) -> Dict:
        """Tüm servisleri al"""
        return self.services

    def get_running_services(self) -> List[str]:
        """Çalışan servisleri al"""
        return [name for name, svc in self.services.items() if svc.get('status') == 'running']

    def to_dict(self) -> Dict:
        """Servisleri sözlüğe dönüştür"""
        return self.services

    def to_json(self) -> str:
        """Servisleri JSON'a dönüştür"""
        return json.dumps(self.to_dict())


# Kullanım Örneği
if __name__ == "__main__":
    # Konfigürasyon
    config = SystemConfig()
    config.services = {'database': True, 'cache': True, 'api': True}
    config.features = ['user_management', 'framework_support', 'python_integration']
    
    # Durum
    status = SystemStatus()
    status.status = "healthy"
    status.services_running = 5
    status.services_total = 5
    
    # Servis Yöneticisi
    service_manager = ServiceManager()
    service_manager.register_service('database', {'type': 'mysql', 'host': 'localhost'})
    service_manager.register_service('api', {'type': 'rest', 'port': 8000})
    
    service_manager.start_service('database')
    service_manager.start_service('api')
    
    print("=== Sistem Konfigürasyonu ===")
    print(config.to_json())
    print("\n=== Sistem Durumu ===")
    print(status.to_json())
    print("\n=== Servisler ===")
    print(service_manager.to_json())
