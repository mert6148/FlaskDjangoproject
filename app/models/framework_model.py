"""
Framework Modeli
Desteklenen frameworkleri yönetme ve konfigürasyon
"""

from datetime import datetime
from typing import Optional, Dict, List
import json


class Framework:
    """Framework sınıfı"""
    
    def __init__(self, name: str, version: str, framework_type: str):
        self.id = None
        self.name = name
        self.version = version
        self.framework_type = framework_type  # 'frontend', 'backend', 'fullstack'
        self.status = "available"
        self.installed = False
        self.install_path = None
        self.dependencies = []
        self.description = ""
        self.official_url = ""
        self.documentation_url = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """Modeli sözlüğe dönüştür"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'type': self.framework_type,
            'status': self.status,
            'installed': self.installed,
            'install_path': self.install_path,
            'dependencies': self.dependencies,
            'description': self.description,
            'official_url': self.official_url,
            'documentation_url': self.documentation_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def to_json(self) -> str:
        """Modeli JSON'a dönüştür"""
        return json.dumps(self.to_dict())

    def add_dependency(self, dependency: str) -> None:
        """Bağımlılık ekle"""
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
            self.updated_at = datetime.now()

    def mark_installed(self, install_path: str) -> None:
        """Kurulu olarak işaretle"""
        self.installed = True
        self.install_path = install_path
        self.status = "installed"
        self.updated_at = datetime.now()

    def mark_uninstalled(self) -> None:
        """Kurulu olmayan olarak işaretle"""
        self.installed = False
        self.install_path = None
        self.status = "available"
        self.updated_at = datetime.now()


class FrameworkRegistry:
    """Framework registry'si - tüm frameworkleri yönet"""
    
    def __init__(self):
        self.frameworks: Dict[str, Framework] = {}
        self.counter = 0
        self.initialize_default_frameworks()

    def initialize_default_frameworks(self) -> None:
        """Varsayılan frameworkleri ekle"""
        default_frameworks = [
            ('Vue.js', '3.5.31', 'frontend', 
             'Progressive JavaScript framework for building user interfaces',
             'https://vuejs.org',
             'https://vuejs.org/guide/'),
            ('Oracle JET', 'latest', 'frontend',
             'Enterprise JavaScript framework for responsive web applications',
             'https://www.oracle.com/webfolder/technetwork/jet/',
             'https://docs.oracle.com/en/middleware/jet/'),
            ('Django', '4.2', 'backend',
             'High-level Python Web framework',
             'https://www.djangoproject.com/',
             'https://docs.djangoproject.com/'),
            ('Flask', '2.3', 'backend',
             'Lightweight Python web framework',
             'https://flask.palletsprojects.com/',
             'https://flask.palletsprojects.com/'),
            ('Laravel', '10.0', 'fullstack',
             'PHP web application framework',
             'https://laravel.com/',
             'https://laravel.com/docs/')
        ]

        for name, version, fw_type, desc, url, doc_url in default_frameworks:
            self.add_framework(name, version, fw_type, desc, url, doc_url)

    def add_framework(self, name: str, version: str, fw_type: str, 
                     description: str = "", url: str = "", doc_url: str = "") -> Framework:
        """Framework ekle"""
        self.counter += 1
        framework = Framework(name, version, fw_type)
        framework.id = self.counter
        framework.description = description
        framework.official_url = url
        framework.documentation_url = doc_url
        
        self.frameworks[name.lower()] = framework
        return framework

    def get_framework(self, name: str) -> Optional[Framework]:
        """Framework al"""
        return self.frameworks.get(name.lower())

    def all_frameworks(self) -> List[Framework]:
        """Tüm frameworkler"""
        return list(self.frameworks.values())

    def get_frameworks_by_type(self, fw_type: str) -> List[Framework]:
        """Türe göre frameworkler"""
        return [fw for fw in self.frameworks.values() if fw.framework_type == fw_type]

    def get_installed_frameworks(self) -> List[Framework]:
        """Kurulu frameworkler"""
        return [fw for fw in self.frameworks.values() if fw.installed]

    def get_available_frameworks(self) -> List[Framework]:
        """Kullanılabilir frameworkler"""
        return [fw for fw in self.frameworks.values() if not fw.installed]

    def install_framework(self, name: str, install_path: str) -> bool:
        """Framework kur"""
        framework = self.get_framework(name)
        if framework:
            framework.mark_installed(install_path)
            return True
        return False

    def uninstall_framework(self, name: str) -> bool:
        """Framework kaldır"""
        framework = self.get_framework(name)
        if framework:
            framework.mark_uninstalled()
            return True
        return False

    def get_installation_info(self, name: str) -> Optional[Dict]:
        """Kurulum bilgisini al"""
        framework = self.get_framework(name)
        if framework:
            return {
                'name': framework.name,
                'version': framework.version,
                'installed': framework.installed,
                'install_path': framework.install_path,
                'dependencies': framework.dependencies
            }
        return None

    def to_dict(self) -> Dict:
        """Registry'i sözlüğe dönüştür"""
        return {
            'total_frameworks': len(self.frameworks),
            'installed': len(self.get_installed_frameworks()),
            'available': len(self.get_available_frameworks()),
            'frameworks': {name: fw.to_dict() for name, fw in self.frameworks.items()}
        }

    def to_json(self) -> str:
        """Registry'i JSON'a dönüştür"""
        return json.dumps(self.to_dict())


# Kullanım Örneği
if __name__ == "__main__":
    registry = FrameworkRegistry()
    
    # Framework kur
    registry.install_framework('Vue.js', '/home/user/.npm/vue.js')
    registry.install_framework('Django', '/usr/lib/python3/dist-packages/django')
    
    # Vue.js'ye bağımlılık ekle
    vue_fw = registry.get_framework('Vue.js')
    if vue_fw:
        vue_fw.add_dependency('Node.js')
        vue_fw.add_dependency('npm')
    
    print(registry.to_json())
