"""
Kullanıcı Modeli
Sistem kullanıcılarının yönetimi ve kimlik doğrulama
"""

from datetime import datetime
from typing import Optional, Dict, List
import json


class User:
    """Kullanıcı sınıfı"""
    
    def __init__(self, id: int, username: str, email: str, password: str):
        self.id = id
        self.username = username
        self.email = email
        self.password = password  # Hash işlemi gerekli
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.is_active = True
        self.roles = []
        self.permissions = []

    def to_dict(self) -> Dict:
        """Modeli sözlüğe dönüştür"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'roles': self.roles,
            'permissions': self.permissions
        }

    def to_json(self) -> str:
        """Modeli JSON'a dönüştür"""
        return json.dumps(self.to_dict())

    def set_roles(self, roles: List[str]) -> None:
        """Kullanıcı rollerini ayarla"""
        self.roles = roles
        self.updated_at = datetime.now()

    def add_permission(self, permission: str) -> None:
        """İzin ekle"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now()

    def remove_permission(self, permission: str) -> None:
        """İzin çıkar"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now()

    def has_permission(self, permission: str) -> bool:
        """İzin var mı kontrol et"""
        return permission in self.permissions

    def is_admin(self) -> bool:
        """Admin mi kontrol et"""
        return 'admin' in self.roles

    def activate(self) -> None:
        """Kullanıcıyı etkinleştir"""
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Kullanıcıyı devre dışı bırak"""
        self.is_active = False
        self.updated_at = datetime.now()


class UserRepository:
    """Kullanıcı veri deposu"""
    
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.counter = 0

    def create(self, username: str, email: str, password: str) -> User:
        """Yeni kullanıcı oluştur"""
        self.counter += 1
        user = User(self.counter, username, email, password)
        self.users[user.id] = user
        return user

    def find(self, user_id: int) -> Optional[User]:
        """Kullanıcı bul"""
        return self.users.get(user_id)

    def find_by_username(self, username: str) -> Optional[User]:
        """Kullanıcı adıyla bul"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def find_by_email(self, email: str) -> Optional[User]:
        """Email'le bul"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def all(self) -> List[User]:
        """Tüm kullanıcılar"""
        return list(self.users.values())

    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Kullanıcı güncelle"""
        user = self.find(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.now()
        return user

    def delete(self, user_id: int) -> bool:
        """Kullanıcı sil"""
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False

    def get_active_users(self) -> List[User]:
        """Aktif kullanıcıları al"""
        return [user for user in self.users.values() if user.is_active]

    def count(self) -> int:
        """Toplam kullanıcı sayısı"""
        return len(self.users)

    def to_json(self) -> str:
        """Tüm kullanıcıları JSON'a dönüştür"""
        users_dict = {
            'total': self.count(),
            'users': [user.to_dict() for user in self.users.values()]
        }
        return json.dumps(users_dict)


# Kullanım Örneği
if __name__ == "__main__":
    repo = UserRepository()
    
    # Kullanıcı oluştur
    user1 = repo.create("mertd", "mert@example.com", "hashed_password")
    user1.set_roles(["admin", "developer"])
    user1.add_permission("create_projects")
    
    user2 = repo.create("ali", "ali@example.com", "hashed_password")
    user2.set_roles(["user"])
    
    print(repo.to_json())
