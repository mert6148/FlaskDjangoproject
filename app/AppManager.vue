<template>
  <div class="app-manager">
    <!-- Header -->
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title">
          <i class="fas fa-cogs"></i>
          Uygulama Yönetim Sistemi
        </h1>
        <div class="header-actions">
          <div class="system-status" :class="systemStatusClass">
            <i :class="systemStatusIcon"></i>
            {{ systemStatusText }}
          </div>
          <button @click="refreshData" class="btn-refr esh" :disabled="loading">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            Yenile
          </button>
        </div>
      </div>
    </header>

    <!-- Navigation -->
    <nav class="app-navigation">
      <div class="nav-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['nav-tab', { active: activeTab === tab.id }]"
        >
          <i :class="tab.icon"></i>
          {{ tab.name }}
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="app-content">
      <!-- Dashboard Tab -->
      <div v-if="activeTab === 'dashboard'" class="tab-content">
        <div class="dashboard-grid">
          <!-- System Overview -->
          <div class="dashboard-card system-overview">
            <h3><i class="fas fa-server"></i> Sistem Genel Bakış</h3>
            <div class="metrics-grid">
              <div class="metric">
                <span class="metric-value">{{ systemInfo.cpu_usage }}%</span>
                <span class="metric-label">CPU Kullanımı</span>
              </div>
              <div class="metric">
                <span class="metric-value">{{ systemInfo.memory_usage }}%</span>
                <span class="metric-label">Bellek Kullanımı</span>
              </div>
              <div class="metric">
                <span class="metric-value">{{ systemInfo.disk_usage }}%</span>
                <span class="metric-label">Disk Kullanımı</span>
              </div>
              <div class="metric">
                <span class="metric-value">{{ systemInfo.services_running }}</span>
                <span class="metric-label">Çalışan Servisler</span>
              </div>
            </div>
          </div>

          <!-- Recent Activities -->
          <div class="dashboard-card recent-activities">
            <h3><i class="fas fa-history"></i> Son Aktiviteler</h3>
            <div class="activity-list">
              <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
                <div class="activity-icon" :class="activity.type">
                  <i :class="activity.icon"></i>
                </div>
                <div class="activity-content">
                  <div class="activity-title">{{ activity.title }}</div>
                  <div class="activity-time">{{ activity.time }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="dashboard-card quick-actions">
            <h3><i class="fas fa-bolt"></i> Hızlı İşlemler</h3>
            <div class="action-buttons">
              <button @click="startAllServices" class="action-btn primary">
                <i class="fas fa-play"></i>
                Tüm Servisleri Başlat
              </button>
              <button @click="stopAllServices" class="action-btn danger">
                <i class="fas fa-stop"></i>
                Tüm Servisleri Durdur
              </button>
              <button @click="checkHealth" class="action-btn success">
                <i class="fas fa-heartbeat"></i>
                Sistem Sağlığını Kontrol Et
              </button>
              <button @click="clearLogs" class="action-btn warning">
                <i class="fas fa-trash"></i>
                Logları Temizle
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Frameworks Tab -->
      <div v-if="activeTab === 'frameworks'" class="tab-content">
        <div class="frameworks-section">
          <div class="section-header">
            <h3><i class="fas fa-code"></i> Framework Yönetimi</h3>
            <button @click="refreshFrameworks" class="btn-secondary">
              <i class="fas fa-sync-alt"></i>
              Yenile
            </button>
          </div>

          <div class="frameworks-grid">
            <div v-for="framework in frameworks" :key="framework.name" class="framework-card">
              <div class="framework-header">
                <h4>{{ framework.name }}</h4>
                <span class="framework-version">{{ framework.version }}</span>
              </div>
              <div class="framework-status" :class="framework.installed ? 'installed' : 'available'">
                <i :class="framework.installed ? 'fas fa-check-circle' : 'fas fa-circle'"></i>
                {{ framework.installed ? 'Kurulu' : 'Kullanılabilir' }}
              </div>
              <p class="framework-description">{{ framework.description }}</p>
              <div class="framework-actions">
                <button
                  v-if="!framework.installed"
                  @click="installFramework(framework.name)"
                  class="btn-primary"
                  :disabled="framework.installing"
                >
                  <i class="fas fa-download"></i>
                  {{ framework.installing ? 'Kuruluyor...' : 'Kur' }}
                </button>
                <button
                  v-else
                  @click="uninstallFramework(framework.name)"
                  class="btn-danger"
                  :disabled="framework.uninstalling"
                >
                  <i class="fas fa-trash"></i>
                  {{ framework.uninstalling ? 'Kaldırılıyor...' : 'Kaldır' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Users Tab -->
      <div v-if="activeTab === 'users'" class="tab-content">
        <div class="users-section">
          <div class="section-header">
            <h3><i class="fas fa-users"></i> Kullanıcı Yönetimi</h3>
            <button @click="showUserModal = true" class="btn-primary">
              <i class="fas fa-plus"></i>
              Yeni Kullanıcı
            </button>
          </div>

          <div class="users-table">
            <table>
              <thead>
                <tr>
                  <th>Kullanıcı Adı</th>
                  <th>Email</th>
                  <th>Roller</th>
                  <th>Durum</th>
                  <th>Son Giriş</th>
                  <th>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id">
                  <td>{{ user.username }}</td>
                  <td>{{ user.email }}</td>
                  <td>
                    <span v-for="role in user.roles" :key="role" class="role-badge">
                      {{ role }}
                    </span>
                  </td>
                  <td>
                    <span class="status-badge" :class="user.isActive ? 'active' : 'inactive'">
                      {{ user.isActive ? 'Aktif' : 'Pasif' }}
                    </span>
                  </td>
                  <td>{{ user.lastLogin || 'Hiç giriş yapmadı' }}</td>
                  <td class="actions">
                    <button @click="editUser(user)" class="btn-icon">
                      <i class="fas fa-edit"></i>
                    </button>
                    <button @click="deleteUser(user.id)" class="btn-icon danger">
                      <i class="fas fa-trash"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Devices Tab -->
      <div v-if="activeTab === 'devices'" class="tab-content">
        <div class="devices-section">
          <div class="section-header">
            <h3><i class="fas fa-desktop"></i> Cihaz Yönetimi</h3>
            <button @click="refreshDevices" class="btn-secondary">
              <i class="fas fa-sync-alt"></i>
              Yenile
            </button>
          </div>

          <div class="devices-grid">
            <div v-for="device in devices" :key="device.id" class="device-card">
              <div class="device-header">
                <h4>{{ device.name }}</h4>
                <span class="device-type">{{ device.device_type }}</span>
              </div>
              <div class="device-info">
                <div class="info-item">
                  <i class="fas fa-microchip"></i>
                  {{ device.processor }}
                </div>
                <div class="info-item">
                  <i class="fas fa-memory"></i>
                  {{ device.memory }} MB
                </div>
                <div class="info-item">
                  <i class="fas fa-hdd"></i>
                  {{ device.storage }} GB
                </div>
                <div class="info-item">
                  <i class="fas fa-network-wired"></i>
                  {{ device.ip_address }}
                </div>
              </div>
              <div class="device-status" :class="device.connected ? 'connected' : 'disconnected'">
                <i :class="device.connected ? 'fas fa-circle' : 'far fa-circle'"></i>
                {{ device.connected ? 'Bağlı' : 'Bağlantısız' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Services Tab -->
      <div v-if="activeTab === 'services'" class="tab-content">
        <div class="services-section">
          <div class="section-header">
            <h3><i class="fas fa-cogs"></i> Servis Yönetimi</h3>
            <button @click="refreshServices" class="btn-secondary">
              <i class="fas fa-sync-alt"></i>
              Yenile
            </button>
          </div>

          <div class="services-list">
            <div v-for="service in services" :key="service.name" class="service-item">
              <div class="service-info">
                <h4>{{ service.name }}</h4>
                <p>{{ service.description }}</p>
                <div class="service-details">
                  <span class="service-port" v-if="service.port">Port: {{ service.port }}</span>
                  <span class="service-type">{{ service.type }}</span>
                </div>
              </div>
              <div class="service-status" :class="service.status">
                <i :class="service.status === 'running' ? 'fas fa-play-circle' : 'fas fa-stop-circle'"></i>
                {{ service.status === 'running' ? 'Çalışıyor' : 'Durduruldu' }}
              </div>
              <div class="service-actions">
                <button
                  v-if="service.status !== 'running'"
                  @click="startService(service.name)"
                  class="btn-success"
                >
                  <i class="fas fa-play"></i>
                  Başlat
                </button>
                <button
                  v-else
                  @click="stopService(service.name)"
                  class="btn-danger"
                >
                  <i class="fas fa-stop"></i>
                  Durdur
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Logs Tab -->
      <div v-if="activeTab === 'logs'" class="tab-content">
        <div class="logs-section">
          <div class="section-header">
            <h3><i class="fas fa-file-alt"></i> Sistem Logları</h3>
            <div class="log-actions">
              <select v-model="logLevel" class="log-filter">
                <option value="all">Tüm Loglar</option>
                <option value="error">Hata</option>
                <option value="warning">Uyarı</option>
                <option value="info">Bilgi</option>
                <option value="debug">Debug</option>
              </select>
              <button @click="clearLogs" class="btn-danger">
                <i class="fas fa-trash"></i>
                Temizle
              </button>
            </div>
          </div>

          <div class="logs-container">
            <div v-for="log in filteredLogs" :key="log.id" class="log-entry" :class="log.level">
              <div class="log-time">{{ log.timestamp }}</div>
              <div class="log-level" :class="log.level">
                <i :class="getLogIcon(log.level)"></i>
                {{ log.level.toUpperCase() }}
              </div>
              <div class="log-message">{{ log.message }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Settings Tab -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <div class="settings-section">
          <h3><i class="fas fa-cog"></i> Sistem Ayarları</h3>

          <div class="settings-grid">
            <div class="setting-group">
              <h4>Genel Ayarlar</h4>
              <div class="setting-item">
                <label>Uygulama Adı</label>
                <input v-model="settings.app_name" type="text" class="setting-input">
              </div>
              <div class="setting-item">
                <label>Ortam</label>
                <select v-model="settings.environment" class="setting-input">
                  <option value="development">Geliştirme</option>
                  <option value="staging">Test</option>
                  <option value="production">Üretim</option>
                </select>
              </div>
              <div class="setting-item">
                <label>Debug Modu</label>
                <input v-model="settings.debug" type="checkbox" class="setting-checkbox">
              </div>
            </div>

            <div class="setting-group">
              <h4>Veritabanı Ayarları</h4>
              <div class="setting-item">
                <label>Host</label>
                <input v-model="settings.database.host" type="text" class="setting-input">
              </div>
              <div class="setting-item">
                <label>Veritabanı Adı</label>
                <input v-model="settings.database.database" type="text" class="setting-input">
              </div>
              <div class="setting-item">
                <label>Kullanıcı Adı</label>
                <input v-model="settings.database.username" type="text" class="setting-input">
              </div>
              <div class="setting-item">
                <label>Şifre</label>
                <input v-model="settings.database.password" type="password" class="setting-input">
              </div>
            </div>

            <div class="setting-group">
              <h4>Cache Ayarları</h4>
              <div class="setting-item">
                <label>Cache Sürücüsü</label>
                <select v-model="settings.cache.driver" class="setting-input">
                  <option value="redis">Redis</option>
                  <option value="memcached">Memcached</option>
                  <option value="file">Dosya</option>
                </select>
              </div>
              <div class="setting-item">
                <label>TTL (saniye)</label>
                <input v-model.number="settings.cache.ttl" type="number" class="setting-input">
              </div>
            </div>
          </div>

          <div class="settings-actions">
            <button @click="saveSettings" class="btn-primary">
              <i class="fas fa-save"></i>
              Kaydet
            </button>
            <button @click="resetSettings" class="btn-secondary">
              <i class="fas fa-undo"></i>
              Sıfırla
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- User Modal -->
    <div v-if="showUserModal" class="modal-overlay" @click="closeUserModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingUser ? 'Kullanıcı Düzenle' : 'Yeni Kullanıcı' }}</h3>
          <button @click="closeUserModal" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="saveUser" class="user-form">
            <div class="form-group">
              <label>Kullanıcı Adı</label>
              <input v-model="userForm.username" type="text" required>
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="userForm.email" type="email" required>
            </div>
            <div class="form-group">
              <label>Şifre</label>
              <input v-model="userForm.password" type="password" :required="!editingUser">
            </div>
            <div class="form-group">
              <label>Roller</label>
              <div class="role-checkboxes">
                <label v-for="role in availableRoles" :key="role">
                  <input v-model="userForm.roles" :value="role" type="checkbox">
                  {{ role }}
                </label>
              </div>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn-primary">
                {{ editingUser ? 'Güncelle' : 'Oluştur' }}
              </button>
              <button type="button" @click="closeUserModal" class="btn-secondary">
                İptal
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
        <p>Yükleniyor...</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'

export default {
  name: 'AppManager',
  setup() {
    // Reactive data
    const activeTab = ref('dashboard')
    const loading = ref(false)
    const showUserModal = ref(false)
    const editingUser = ref(null)
    const logLevel = ref('all')

    // System data
    const systemInfo = ref({
      cpu_usage: 0,
      memory_usage: 0,
      disk_usage: 0,
      services_running: 0
    })

    // Data collections
    const frameworks = ref([])
    const users = ref([])
    const devices = ref([])
    const services = ref([])
    const logs = ref([])
    const recentActivities = ref([])

    // Settings
    const settings = ref({
      app_name: 'Flask-Django-SDK',
      environment: 'development',
      debug: true,
      database: {
        host: 'localhost',
        database: 'flask_django_sdk',
        username: 'root',
        password: ''
      },
      cache: {
        driver: 'redis',
        ttl: 3600
      }
    })

    // User form
    const userForm = ref({
      username: '',
      email: '',
      password: '',
      roles: []
    })

    // Available roles
    const availableRoles = ref(['admin', 'developer', 'user', 'manager'])

    // Navigation tabs
    const tabs = ref([
      { id: 'dashboard', name: 'Dashboard', icon: 'fas fa-tachometer-alt' },
      { id: 'frameworks', name: 'Frameworkler', icon: 'fas fa-code' },
      { id: 'users', name: 'Kullanıcılar', icon: 'fas fa-users' },
      { id: 'devices', name: 'Cihazlar', icon: 'fas fa-desktop' },
      { id: 'services', name: 'Servisler', icon: 'fas fa-cogs' },
      { id: 'logs', name: 'Loglar', icon: 'fas fa-file-alt' },
      { id: 'settings', name: 'Ayarlar', icon: 'fas fa-cog' }
    ])

    // Computed properties
    const systemStatusClass = computed(() => {
      const status = systemInfo.value.cpu_usage > 80 || systemInfo.value.memory_usage > 80 ? 'warning' : 'healthy'
      return status
    })

    const systemStatusText = computed(() => {
      if (systemInfo.value.cpu_usage > 80 || systemInfo.value.memory_usage > 80) {
        return 'Yüksek Yük'
      }
      return 'Sağlıklı'
    })

    const systemStatusIcon = computed(() => {
      if (systemInfo.value.cpu_usage > 80 || systemInfo.value.memory_usage > 80) {
        return 'fas fa-exclamation-triangle'
      }
      return 'fas fa-check-circle'
    })

    const filteredLogs = computed(() => {
      if (logLevel.value === 'all') {
        return logs.value
      }
      return logs.value.filter(log => log.level === logLevel.value)
    })

    // Methods
    const refreshData = async () => {
      loading.value = true
      try {
        await Promise.all([
          loadSystemInfo(),
          loadFrameworks(),
          loadUsers(),
          loadDevices(),
          loadServices(),
          loadLogs(),
          loadRecentActivities()
        ])
      } catch (error) {
        console.error('Veri yenileme hatası:', error)
      } finally {
        loading.value = false
      }
    }

    const loadSystemInfo = async () => {
      try {
        const response = await fetch('/api/system/status')
        const data = await response.json()
        systemInfo.value = {
          cpu_usage: data.cpu_usage || 0,
          memory_usage: data.memory_usage || 0,
          disk_usage: data.disk_usage || 0,
          services_running: data.services_running || 0
        }
      } catch (error) {
        console.error('Sistem bilgisi yükleme hatası:', error)
      }
    }

    const loadFrameworks = async () => {
      try {
        const response = await fetch('/api/frameworks')
        const data = await response.json()
        frameworks.value = data.frameworks || []
      } catch (error) {
        console.error('Framework yükleme hatası:', error)
      }
    }

    const loadUsers = async () => {
      try {
        const response = await fetch('/api/users')
        const data = await response.json()
        users.value = data.users || []
      } catch (error) {
        console.error('Kullanıcı yükleme hatası:', error)
      }
    }

    const loadDevices = async () => {
      try {
        const response = await fetch('/api/devices')
        const data = await response.json()
        devices.value = data.devices || []
      } catch (error) {
        console.error('Cihaz yükleme hatası:', error)
      }
    }

    const loadServices = async () => {
      try {
        const response = await fetch('/api/system/services')
        const data = await response.json()
        services.value = data.services || []
      } catch (error) {
        console.error('Servis yükleme hatası:', error)
      }
    }

    const loadLogs = async () => {
      try {
        const response = await fetch('/api/system/logs')
        const data = await response.json()
        logs.value = data.logs || []
      } catch (error) {
        console.error('Log yükleme hatası:', error)
      }
    }

    const loadRecentActivities = async () => {
      // Mock data for recent activities
      recentActivities.value = [
        {
          id: 1,
          title: 'Vue.js frameworkü kuruldu',
          time: '2 dakika önce',
          type: 'success',
          icon: 'fas fa-code'
        },
        {
          id: 2,
          title: 'Yeni kullanıcı eklendi: mertd',
          time: '5 dakika önce',
          type: 'info',
          icon: 'fas fa-user-plus'
        },
        {
          id: 3,
          title: 'Sistem güncellemesi tamamlandı',
          time: '10 dakika önce',
          type: 'success',
          icon: 'fas fa-sync-alt'
        }
      ]
    }

    const installFramework = async (frameworkName) => {
      const framework = frameworks.value.find(f => f.name === frameworkName)
      if (framework) {
        framework.installing = true
        try {
          await fetch('/api/frameworks/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: frameworkName, path: `./${frameworkName.toLowerCase()}` })
          })
          await loadFrameworks()
        } catch (error) {
          console.error('Framework kurulum hatası:', error)
        } finally {
          framework.installing = false
        }
      }
    }

    const uninstallFramework = async (frameworkName) => {
      const framework = frameworks.value.find(f => f.name === frameworkName)
      if (framework) {
        framework.uninstalling = true
        try {
          await fetch('/api/frameworks/uninstall', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: frameworkName })
          })
          await loadFrameworks()
        } catch (error) {
          console.error('Framework kaldırma hatası:', error)
        } finally {
          framework.uninstalling = false
        }
      }
    }

    const startAllServices = async () => {
      try {
        await fetch('/api/system/services/start-all', { method: 'POST' })
        await loadServices()
        await loadSystemInfo()
      } catch (error) {
        console.error('Servis başlatma hatası:', error)
      }
    }

    const stopAllServices = async () => {
      try {
        await fetch('/api/system/services/stop-all', { method: 'POST' })
        await loadServices()
        await loadSystemInfo()
      } catch (error) {
        console.error('Servis durdurma hatası:', error)
      }
    }

    const checkHealth = async () => {
      try {
        const response = await fetch('/api/system/health')
        const data = await response.json()
        console.log('Sistem sağlığı:', data)
      } catch (error) {
        console.error('Sağlık kontrolü hatası:', error)
      }
    }

    const clearLogs = async () => {
      try {
        await fetch('/api/system/logs/clear', { method: 'POST' })
        logs.value = []
      } catch (error) {
        console.error('Log temizleme hatası:', error)
      }
    }

    const editUser = (user) => {
      editingUser.value = user
      userForm.value = {
        username: user.username,
        email: user.email,
        password: '',
        roles: [...user.roles]
      }
      showUserModal.value = true
    }

    const saveUser = async () => {
      try {
        const method = editingUser.value ? 'PUT' : 'POST'
        const url = editingUser.value ? `/api/users/${editingUser.value.id}` : '/api/users'

        await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userForm.value)
        })

        await loadUsers()
        closeUserModal()
      } catch (error) {
        console.error('Kullanıcı kaydetme hatası:', error)
      }
    }

    const deleteUser = async (userId) => {
      if (confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) {
        try {
          await fetch(`/api/users/${userId}`, { method: 'DELETE' })
          await loadUsers()
        } catch (error) {
          console.error('Kullanıcı silme hatası:', error)
        }
      }
    }

    const closeUserModal = () => {
      showUserModal.value = false
      editingUser.value = null
      userForm.value = {
        username: '',
        email: '',
        password: '',
        roles: []
      }
    }

    const startService = async (serviceName) => {
      try {
        await fetch('/api/system/services/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ service: serviceName })
        })
        await loadServices()
      } catch (error) {
        console.error('Servis başlatma hatası:', error)
      }
    }

    const stopService = async (serviceName) => {
      try {
        await fetch('/api/system/services/stop', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ service: serviceName })
        })
        await loadServices()
      } catch (error) {
        console.error('Servis durdurma hatası:', error)
      }
    }

    const refreshFrameworks = () => loadFrameworks()
    const refreshDevices = () => loadDevices()
    const refreshServices = () => loadServices()

    const saveSettings = async () => {
      try {
        await fetch('/api/system/config', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(settings.value)
        })
        console.log('Ayarlar kaydedildi')
      } catch (error) {
        console.error('Ayar kaydetme hatası:', error)
      }
    }

    const resetSettings = () => {
      if (confirm('Ayarları sıfırlamak istediğinizden emin misiniz?')) {
        settings.value = {
          app_name: 'Flask-Django-SDK',
          environment: 'development',
          debug: true,
          database: {
            host: 'localhost',
            database: 'flask_django_sdk',
            username: 'root',
            password: ''
          },
          cache: {
            driver: 'redis',
            ttl: 3600
          }
        }
      }
    }

    const getLogIcon = (level) => {
      const icons = {
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle',
        debug: 'fas fa-bug'
      }
      return icons[level] || 'fas fa-question-circle'
    }

    // Initialize
    onMounted(async () => {
      await refreshData()

      // Auto refresh every 30 seconds
      setInterval(refreshData, 30000)
    })

    return {
      // Data
      activeTab,
      loading,
      showUserModal,
      editingUser,
      logLevel,
      systemInfo,
      frameworks,
      users,
      devices,
      services,
      logs,
      recentActivities,
      settings,
      userForm,
      availableRoles,
      tabs,

      // Computed
      systemStatusClass,
      systemStatusText,
      systemStatusIcon,
      filteredLogs,

      // Methods
      refreshData,
      loadSystemInfo,
      loadFrameworks,
      loadUsers,
      loadDevices,
      loadServices,
      loadLogs,
      loadRecentActivities,
      installFramework,
      uninstallFramework,
      startAllServices,
      stopAllServices,
      checkHealth,
      clearLogs,
      editUser,
      saveUser,
      deleteUser,
      closeUserModal,
      startService,
      stopService,
      refreshFrameworks,
      refreshDevices,
      refreshServices,
      saveSettings,
      resetSettings,
      getLogIcon
    }
  }
}
</script>

<style scoped>
/* Modern CSS Variables */
:root {
  --primary-color: #007bff;
  --success-color: #28a745;
  --danger-color: #dc3545;
  --warning-color: #ffc107;
  --info-color: #17a2b8;
  --dark-color: #343a40;
  --light-color: #f8f9fa;
  --border-color: #dee2e6;
  --shadow: 0 2px 4px rgba(0,0,0,0.1);
  --border-radius: 8px;
  --transition: all 0.3s ease;
}

/* Main Container */
.app-manager {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Header */
.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-title {
  margin: 0;
  color: var(--dark-color);
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.system-status {
  padding: 0.5rem 1rem;
  border-radius: var(--border-radius);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.system-status.healthy {
  background: var(--success-color);
  color: white;
}

.system-status.warning {
  background: var(--warning-color);
  color: var(--dark-color);
}

.btn-refresh {
  padding: 0.5rem 1rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: var(--transition);
}

.btn-refresh:hover:not(:disabled) {
  background: #0056b3;
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Navigation */
.app-navigation {
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid var(--border-color);
}

.nav-tabs {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  padding: 0 2rem;
}

.nav-tab {
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--dark-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: var(--transition);
  font-weight: 500;
}

.nav-tab:hover {
  background: rgba(0, 123, 255, 0.1);
}

.nav-tab.active {
  border-bottom-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(0, 123, 255, 0.05);
}

/* Main Content */
.app-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.tab-content {
  background: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
  padding: 2rem;
}

/* Dashboard */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.dashboard-card {
  background: var(--light-color);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  border: 1px solid var(--border-color);
}

.dashboard-card h3 {
  margin: 0 0 1rem 0;
  color: var(--dark-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.metric {
  text-align: center;
  padding: 1rem;
  background: white;
  border-radius: var(--border-radius);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.metric-value {
  display: block;
  font-size: 2rem;
  font-weight: bold;
  color: var(--primary-color);
}

.metric-label {
  font-size: 0.9rem;
  color: var(--dark-color);
  margin-top: 0.5rem;
}

.activity-list {
  max-height: 300px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.activity-icon.success { background: var(--success-color); }
.activity-icon.info { background: var(--info-color); }
.activity-icon.warning { background: var(--warning-color); }

.activity-content {
  flex: 1;
}

.activity-title {
  font-weight: 500;
  color: var(--dark-color);
}

.activity-time {
  font-size: 0.8rem;
  color: #6c757d;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.action-btn {
  padding: 1rem;
  border: none;
  border-radius: var(--border-radius);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 500;
  transition: var(--transition);
}

.action-btn.primary { background: var(--primary-color); }
.action-btn.danger { background: var(--danger-color); }
.action-btn.success { background: var(--success-color); }
.action-btn.warning { background: var(--warning-color); }

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

/* Frameworks */
.frameworks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.framework-card {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  transition: var(--transition);
}

.framework-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.framework-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.framework-header h4 {
  margin: 0;
  color: var(--dark-color);
}

.framework-version {
  background: var(--info-color);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.framework-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

.framework-status.installed {
  color: var(--success-color);
}

.framework-status.available {
  color: var(--warning-color);
}

.framework-description {
  color: #6c757d;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.framework-actions {
  display: flex;
  gap: 0.5rem;
}

/* Users */
.users-table {
  margin-top: 1.5rem;
  overflow-x: auto;
}

.users-table table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.users-table th {
  background: var(--light-color);
  font-weight: 600;
  color: var(--dark-color);
}

.role-badge {
  display: inline-block;
  background: var(--info-color);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  margin: 0.1rem;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge.active {
  background: var(--success-color);
  color: white;
}

.status-badge.inactive {
  background: var(--danger-color);
  color: white;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  padding: 0.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: var(--info-color);
  color: white;
  transition: var(--transition);
}

.btn-icon:hover {
  background: #138496;
}

.btn-icon.danger {
  background: var(--danger-color);
}

.btn-icon.danger:hover {
  background: #c82333;
}

/* Devices */
.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.device-card {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  transition: var(--transition);
}

.device-card:hover {
  box-shadow: var(--shadow);
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.device-header h4 {
  margin: 0;
  color: var(--dark-color);
}

.device-type {
  background: var(--primary-color);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  text-transform: capitalize;
}

.device-info {
  margin-bottom: 1rem;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: #6c757d;
  font-size: 0.9rem;
}

.device-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.device-status.connected {
  color: var(--success-color);
}

.device-status.disconnected {
  color: var(--danger-color);
}

/* Services */
.services-list {
  margin-top: 1.5rem;
}

.service-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  margin-bottom: 1rem;
  transition: var(--transition);
}

.service-item:hover {
  box-shadow: var(--shadow);
}

.service-info {
  flex: 1;
}

.service-info h4 {
  margin: 0 0 0.5rem 0;
  color: var(--dark-color);
}

.service-info p {
  margin: 0 0 0.5rem 0;
  color: #6c757d;
}

.service-details {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #6c757d;
}

.service-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  margin: 0 2rem;
}

.service-status.running {
  color: var(--success-color);
}

.service-status.stopped {
  color: var(--danger-color);
}

/* Logs */
.logs-container {
  margin-top: 1.5rem;
  max-height: 500px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: var(--border-radius);
  padding: 1rem;
}

.log-entry {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem;
  border-bottom: 1px solid #333;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.log-entry.error { background: rgba(220, 53, 69, 0.1); }
.log-entry.warning { background: rgba(255, 193, 7, 0.1); }
.log-entry.info { background: rgba(23, 162, 184, 0.1); }
.log-entry.debug { background: rgba(108, 117, 125, 0.1); }

.log-time {
  color: #888;
  min-width: 120px;
}

.log-level {
  min-width: 80px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: bold;
}

.log-level.error { color: var(--danger-color); }
.log-level.warning { color: var(--warning-color); }
.log-level.info { color: var(--info-color); }
.log-level.debug { color: #6c757d; }

.log-message {
  flex: 1;
  color: #f8f8f2;
}

/* Settings */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  margin-top: 1.5rem;
}

.setting-group {
  background: var(--light-color);
  padding: 1.5rem;
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
}

.setting-group h4 {
  margin: 0 0 1rem 0;
  color: var(--dark-color);
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-item label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--dark-color);
}

.setting-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 1rem;
  transition: var(--transition);
}

.setting-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.setting-checkbox {
  width: auto;
  margin-right: 0.5rem;
}

.settings-actions {
  margin-top: 2rem;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: var(--border-radius);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: var(--dark-color);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
}

.modal-body {
  padding: 1.5rem;
}

.user-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--dark-color);
}

.form-group input {
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 1rem;
}

.role-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.role-checkboxes label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

/* Loading */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.loading-spinner {
  background: white;
  padding: 2rem;
  border-radius: var(--border-radius);
  text-align: center;
}

.loading-spinner i {
  font-size: 2rem;
  color: var(--primary-color);
  margin-bottom: 1rem;
}

/* Buttons */
.btn-primary {
  padding: 0.75rem 1.5rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-weight: 500;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-weight: 500;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-success {
  padding: 0.5rem 1rem;
  background: var(--success-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-weight: 500;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-success:hover {
  background: #218838;
}

.btn-danger {
  padding: 0.5rem 1rem;
  background: var(--danger-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-weight: 500;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-danger:hover {
  background: #c82333;
}

/* Section Headers */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h3 {
  margin: 0;
  color: var(--dark-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.log-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.log-filter {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: white;
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }

  .nav-tabs {
    flex-wrap: wrap;
  }

  .nav-tab {
    flex: 1;
    min-width: 120px;
    justify-content: center;
  }

  .app-content {
    padding: 1rem;
  }

  .dashboard-grid,
  .frameworks-grid,
  .devices-grid,
  .settings-grid {
    grid-template-columns: 1fr;
  }

  .service-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .service-status {
    margin: 0;
  }

  .log-entry {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .form-actions {
    flex-direction: column;
  }

  .settings-actions {
    flex-direction: column;
  }
}
</style>