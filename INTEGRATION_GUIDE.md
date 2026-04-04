# Uygulama Entegrasyon Sistemi Dokümantasyonu

## Genel Bakış

Bu sistem, **PHP (Laravel)**, **JavaScript (Vue.js, Node.js)** ve **Python (Django, Flask)** dillerini bir araya getirerek, modern bir tam yığın (full-stack) uygulama geliştirme ortamı sağlar.

## Mimari

```
┌─────────────────────────────┐
│   Frontend (Vue.js/HTML)    │
│     (Browser/Client)        │
└──────────────┬──────────────┘
               │ HTTP REST API
┌──────────────▼──────────────┐
│   JavaScript Bridge Layer   │
│  (system-bridge.js, ...)    │
└──────────────┬──────────────┘
               │ HTTP/REST
┌──────────────▼──────────────┐
│   PHP (Laravel) Backend     │
│    API Controller Layer     │
│       (app.php)             │
└──────────────┬──────────────┘
               │ Shell/Process
┌──────────────▼──────────────┐
│   Python Model Layer        │
│  (user_model, system_model, │
│  framework_model,           │
│  device_model)              │
└─────────────────────────────┘
```

## Komponent Açıklaması

### 1. PHP Uygulaması (`app/app.php`)

**Sorumlulukları:**
- Uygulama yapılandırması ve başlatması
- Servis yönetimi (Database, Cache, Filesystem)
- Python modellerine erişim
- API endpoint'lerinin tanımlanması
- JavaScript bridge'e destek

**Ana Sınıflar:**
- `App` - Ana uygulama sınıfı
- `Config` - Yapılandırma yönetimi
- `ServiceManager` - Servis yönetimi

### 2. Python Modelleri (`app/models/`)

#### `user_model.py`
- Kullanıcı yönetimi
- Authentication ve authorization
- Rol tabanlı erişim kontrolü

```python
class User:
    - to_dict() / to_json()
    - set_roles(), add_permission()
    - is_admin(), has_permission()

class UserRepository:
    - create(), find(), find_by_username()
    - all(), update(), delete()
    - get_active_users()
```

#### `system_model.py`
- Sistem konfigürasyonu
- Sistem durumu takibi
- Servis yönetimi

```python
class SystemConfig:
    - Yapılandırma yönetimi

class SystemStatus:
    - Durum takibi
    - CPU, Memory, Disk kullanımı

class ServiceManager:
    - Servis kayıt ve yönetimi
```

#### `framework_model.py`
- Desteklenen framework'lerin yönetimi
- Kurulum takibi
- Bağımlılık yönetimi

```python
class Framework:
    - Framework bilgisi
    - Kurulum durumu

class FrameworkRegistry:
    - Tüm framework'leri yönet
    - Kurulu/Kullanılabilir framework'ler
```

#### `device_model.py`
- Cihaz kaydı ve yönetimi
- Ağ bilgileri
- Donanım bilgileri

```python
class Device:
    - Cihaz bilgisi
    - Ağ ve donanım özellikleri

class DeviceRegistry:
    - Tüm cihazları yönet
    - Bağlantı durumunu takip
```

### 3. JavaScript Bridge Katmanı (`js/`)

#### `system-bridge.js`
- PHP uygulamasıyla iletişim
- Sistem bilgisini alma/güncelleme
- Python kodunu çalıştırma
- Event yönetimi

```javascript
class SystemBridge:
    - initialize()
    - fetchSystemInfo()
    - connectToApplication()
    - updateConfig()
    - executeCommand()
    - executePython()
    - startHealthCheck()
```

#### `model-sync.js`
- Python modellerini JavaScript'e senkronize et
- Veri tutarlılığını sağla
- Model güncellemelerin takibi

```javascript
class ModelSync:
    - syncAll()
    - syncUserModels()
    - syncSystemModels()
    - syncFrameworkModels()
    - syncDeviceModels()
    - updateModel(), deleteModel()
```

#### `api-client.js`
- RESTful API istemcisi
- Tüm API endpoint'lerine erişim
- Retry mekanizması
- Batch işlemler

```javascript
class ApiClient:
    - request()
    - models.*
    - system.*
    - frameworks.*
    - devices.*
    - users.*
    - python.*
    - files.*
```

#### `framework-manager.js`
- Vue.js ve Oracle JET kurulumu/kaldırılması
- Framework durumu yönetimi
- Bağımlılık takibi

```javascript
class FrameworkManager:
    - installFramework()
    - uninstallFramework()
    - setupVueJs()
    - setupOracleJET()
    - getStatistics()
```

#### `app.js`
- Ana uygulama başlatıcısı
- Tüm komponentleri bir araya getirir
- Yaşam döngüsü yönetimi

```javascript
class Application:
    - initialize()
    - setupEventListeners()
    - executePython()
    - installFramework()
    - checkSystemHealth()
    - shutdown()
```

## Veri Akışı

### İleri Yönlü (Frontend → Backend)
```
Vue.js → JavaScript Bridge → PHP App → Python Models → Database
```

**Örnek: Kullanıcı oluştur**
```javascript
// Frontend
const newUser = { username: 'ali', email: 'ali@example.com' };
await apiClient.users.create(newUser);

// PHP (ApiController)
POST /api/users → UserController@create

// Python
UserRepository().create() → Save to DB
```

### Geri Yönlü (Backend → Frontend)
```
Python Model → PHP App → JavaScript Bridge → Vue.js → UI
```

**Örnek: Kullanıcıları listele**
```javascript
// Frontend
const users = await apiClient.users.list();

// PHP (ApiController)
GET /api/users → UserController@list

// Python
UserRepository().all() → JSON Response
```

### Senkronizasyon
```
Python Model ←→ ModelSync ↔ Vue.js Components
```

## Başlatma Sırası

1. **app.js** dosyası yüklenir
2. **ApiClient** başlatılır
3. **SystemBridge** başlatılır
4. **ModelSync** başlatılır ve ilk senkronizasyonu yapar
5. **FrameworkManager** başlatılır
6. Event listener'lar ayarlanır
7. Sağlık kontrolü başlatılır
8. `applicationReady` event'i gönderilir

## Örnek Kullanım

### Vue.js Komponenti
```javascript
<script setup>
import { ref, onMounted } from 'vue'

const users = ref([])
const frameworks = ref([])

onMounted(async () => {
    // Sistem hazır olmasını bekle
    window.addEventListener('applicationReady', async () => {
        users.value = await app.apiClient.users.list()
        frameworks.value = app.frameworkManager.getStatistics()
    })
})

const installFramework = async (name) => {
    await app.installFramework(name, './install-path')
}
</script>
```

### Python Kodu Çalıştırma
```javascript
// JavaScript'ten Python kodu çalıştır
const result = await app.executePython(`
    from app.models.user_model import UserRepository
    repo = UserRepository()
    repo.create('yeni_user', 'email@example.com', 'password')
`)
```

### Framework Kurulumu
```javascript
// Vue.js kur
await app.installFramework('Vue.js', '/home/user/projects/vue-app')

// Oracle JET kur
await app.frameworkManager.setupOracleJET('./oracle-project')
```

## Event'ler

### System Events
- `system:ready` - Sistem hazır
- `system:connected` - PHP uygulamasına bağlandı
- `system:config-updated` - Konfigürasyon güncellendi
- `system:health-check` - Sağlık kontrolü yapıldı
- `system:connection-lost` - Bağlantı kesildi

### Model Events
- `sync:start` - Senkronizasyona başladı
- `sync:complete` - Senkronizasyon tamamlandı
- `sync:error` - Senkronizasyon hatası
- `model:updated` - Model güncellendi
- `model:deleted` - Model silindi

### Framework Events
- `frameworks:loaded` - Framework'ler yüklendi
- `framework:installing` - Framework kuruluyor
- `framework:installed` - Framework kuruldu
- `framework:uninstalling` - Framework kaldırılıyor
- `framework:uninstalled` - Framework kaldırıldı

## API Endpoint'leri

### Modeller
- `GET /api/models` - Tüm modelleri listele
- `GET /api/models/{id}` - Model al
- `POST /api/models` - Model oluştur
- `PUT /api/models/{id}` - Model güncelle
- `DELETE /api/models/{id}` - Model sil

### Sistem
- `GET /api/system/info` - Sistem bilgisi
- `GET /api/system/status` - Sistem durumu
- `GET /api/system/health` - Sistem sağlığı
- `PUT /api/system/config` - Yapılandırma güncelle
- `POST /api/system/command` - Komut çalıştır
- `GET /api/system/services` - Servisleri listele
- `POST /api/system/services/start` - Servisi başlat
- `POST /api/system/services/stop` - Servisi durdur

### Framework'ler
- `GET /api/frameworks` - Framework'leri listele
- `GET /api/frameworks/{name}` - Framework al
- `POST /api/frameworks/install` - Framework kur
- `POST /api/frameworks/uninstall` - Framework kaldır
- `GET /api/frameworks/status` - Framework durumu

### Cihazlar
- `GET /api/devices` - Cihazları listele
- `GET /api/devices/connected` - Bağlı cihazları listele
- `POST /api/devices` - Cihaz kaydet
- `PUT /api/devices/{id}` - Cihaz güncelle
- `PATCH /api/devices/{id}/status` - Durumu güncelle

### Kullanıcılar
- `GET /api/users` - Kullanıcıları listele
- `POST /api/users` - Kullanıcı oluştur
- `PUT /api/users/{id}` - Kullanıcı güncelle
- `DELETE /api/users/{id}` - Kullanıcı sil
- `GET /api/users/active` - Aktif kullanıcıları listele

### Python
- `POST /execute/python` - Python kodu çalıştır
- `POST /execute/model` - Python modeli çalıştır

## Hata Yönetimi

İstekler başarısız olursa, sistem otomatik olarak tekrar dener (3 kez).

```javascript
// ApiClient retry mekanizması
{
    retryAttempts: 3,
    retryDelay: 1000,
    timeout: 30000
}
```

## Güvenlik

- CORS (Cross-Origin Resource Sharing) yapılandırması
- CSRF token'ları
- Rate limiting
- Input validation
- SQL injection koruması

## Bağımlılıklar

- PHP 8+
- Laravel 10+
- Node.js 14+
- Python 3.8+
- Vue.js 3+
- Oracle JET (opsiyonel)

## Başlar ve Kapatır

```javascript
// Başlatma
await app.initialize()

// Kapatma
await app.shutdown()
```

## Sonuç

Bu sistem, Python modellerinin gücünü PHP uygulamasının esnekliği ve JavaScript'in interaktivitesi ile birleştirerek, güçlü ve ölçeklenebilir web uygulamaları geliştirmeye olanak tanır.
