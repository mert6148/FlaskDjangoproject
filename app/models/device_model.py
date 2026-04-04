"""
Cihaz Modeli
Sistem cihazları ve donanım bilgilerini yönetme
"""

from datetime import datetime
from typing import Optional, Dict, List
import json
import uuid
import platform


class Device:
    """Cihaz sınıfı"""
    
    def __init__(self, device_type: str, name: str):
        self.id = str(uuid.uuid4())
        self.device_type = device_type  # 'computer', 'mobile', 'server', 'iot'
        self.name = name
        self.status = "active"
        self.os = platform.system()
        self.os_version = platform.version()
        self.processor = platform.processor()
        self.hostname = platform.node()
        self.ip_address = None
        self.mac_address = None
        self.memory = None
        self.storage = None
        self.cpu_cores = None
        self.last_seen = datetime.now()
        self.connected = True
        self.tags = []
        self.metadata = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """Modeli sözlüğe dönüştür"""
        return {
            'id': self.id,
            'device_type': self.device_type,
            'name': self.name,
            'status': self.status,
            'os': self.os,
            'os_version': self.os_version,
            'processor': self.processor,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'memory': self.memory,
            'storage': self.storage,
            'cpu_cores': self.cpu_cores,
            'last_seen': self.last_seen.isoformat(),
            'connected': self.connected,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def to_json(self) -> str:
        """Modeli JSON'a dönüştür"""
        return json.dumps(self.to_dict())

    def set_network_info(self, ip: str, mac: str) -> None:
        """Ağ bilgisini ayarla"""
        self.ip_address = ip
        self.mac_address = mac
        self.updated_at = datetime.now()

    def set_hardware_info(self, memory: int, storage: int, cpu_cores: int) -> None:
        """Donanım bilgisini ayarla"""
        self.memory = memory
        self.storage = storage
        self.cpu_cores = cpu_cores
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Etiket ekle"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Etiket çıkar"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def update_last_seen(self) -> None:
        """Son görülme zamanını güncelle"""
        self.last_seen = datetime.now()

    def mark_connected(self) -> None:
        """Bağlı olarak işaretle"""
        self.connected = True
        self.status = "active"
        self.update_last_seen()

    def mark_disconnected(self) -> None:
        """Bağlantısı kesilmiş olarak işaretle"""
        self.connected = False
        self.status = "inactive"


class DeviceRegistry:
    """Cihaz registry'si - tüm cihazları yönet"""
    
    def __init__(self):
        self.devices: Dict[str, Device] = {}

    def register_device(self, device_type: str, name: str) -> Device:
        """Cihaz kaydet"""
        device = Device(device_type, name)
        self.devices[device.id] = device
        return device

    def get_device(self, device_id: str) -> Optional[Device]:
        """Cihaz al"""
        return self.devices.get(device_id)

    def find_devices_by_type(self, device_type: str) -> List[Device]:
        """Türe göre cihazları bul"""
        return [dev for dev in self.devices.values() if dev.device_type == device_type]

    def find_devices_by_tag(self, tag: str) -> List[Device]:
        """Etikete göre cihazları bul"""
        return [dev for dev in self.devices.values() if tag in dev.tags]

    def get_connected_devices(self) -> List[Device]:
        """Bağlı cihazları al"""
        return [dev for dev in self.devices.values() if dev.connected]

    def get_disconnected_devices(self) -> List[Device]:
        """Bağlantısı kesilmiş cihazları al"""
        return [dev for dev in self.devices.values() if not dev.connected]

    def get_active_devices(self) -> List[Device]:
        """Aktif cihazları al"""
        return [dev for dev in self.devices.values() if dev.status == "active"]

    def update_device_status(self, device_id: str, connected: bool) -> bool:
        """Cihaz durumunu güncelle"""
        device = self.get_device(device_id)
        if device:
            if connected:
                device.mark_connected()
            else:
                device.mark_disconnected()
            return True
        return False

    def get_device_count(self) -> int:
        """Toplam cihaz sayısı"""
        return len(self.devices)

    def get_connected_count(self) -> int:
        """Bağlı cihaz sayısı"""
        return len(self.get_connected_devices())

    def get_device_summary(self) -> Dict:
        """Cihaz özeti"""
        devices_by_type = {}
        for device_type in ['computer', 'mobile', 'server', 'iot']:
            devices = self.find_devices_by_type(device_type)
            if devices:
                devices_by_type[device_type] = len(devices)

        return {
            'total_devices': self.get_device_count(),
            'connected': self.get_connected_count(),
            'disconnected': self.get_device_count() - self.get_connected_count(),
            'by_type': devices_by_type
        }

    def to_dict(self) -> Dict:
        """Registry'i sözlüğe dönüştür"""
        return {
            'summary': self.get_device_summary(),
            'devices': {device_id: device.to_dict() for device_id, device in self.devices.items()}
        }

    def to_json(self) -> str:
        """Registry'i JSON'a dönüştür"""
        return json.dumps(self.to_dict())


# Kullanım Örneği
if __name__ == "__main__":
    registry = DeviceRegistry()
    
    # Cihaz kaydet
    computer = registry.register_device('computer', 'Development Machine')
    computer.set_network_info('192.168.1.100', '00:11:22:33:44:55')
    computer.set_hardware_info(16384, 512000, 8)
    computer.add_tag('development')
    computer.mark_connected()
    
    server = registry.register_device('server', 'API Server')
    server.set_network_info('192.168.1.200', '00:11:22:33:44:66')
    server.set_hardware_info(32768, 1024000, 16)
    server.add_tag('production')
    server.mark_connected()
    
    mobile = registry.register_device('mobile', 'Test Device')
    mobile.add_tag('testing')
    mobile.mark_connected()
    
    print(registry.to_json())
