/**
 * Sistem Bridge - PHP ve Python ile iletişim
 * Sistem yapılandırması ve durumunu yönetme
 */

class SystemBridge {
    constructor() {
        this.apiBaseUrl = '/api';
        this.pythonEndpoint = '/execute/python';
        this.isConnected = false;
        this.systemConfig = {};
        this.systemStatus = {};
        this.listeners = new Map();
    }

    /**
     * Sistem başlangıcını başlat
     */
    async initialize() {
        try {
            console.log('[SystemBridge] Başlatılıyor...');
            
            // Sistem bilgisini al
            await this.fetchSystemInfo();
            
            // PHP uygulamasıyla bağlantı kur
            await this.connectToApplication();
            
            // Event listener'ları ayarla
            this.setupEventListeners();
            
            this.isConnected = true;
            this.emit('system:ready');
            console.log('[SystemBridge] Hazır');
        } catch (error) {
            console.error('[SystemBridge] Başlatma hatası:', error);
        }
    }

    /**
     * Sistem bilgisini getir
     */
    async fetchSystemInfo() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/system/info`);
            const data = await response.json();
            
            this.systemConfig = data.config || {};
            this.systemStatus = data.status || {};
            
            this.emit('system:info-updated', {
                config: this.systemConfig,
                status: this.systemStatus
            });
            
            return data;
        } catch (error) {
            console.error('[SystemBridge] Sistem bilgisi alınamadı:', error);
            throw error;
        }
    }

    /**
     * Uygulamayla bağlantı kur
     */
    async connectToApplication() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/system/status`);
            const data = await response.json();
            
            console.log('[SystemBridge] Uygulama durumu:', data);
            this.emit('system:connected', data);
            
            return data;
        } catch (error) {
            console.error('[SystemBridge] Bağlantı hatası:', error);
            throw error;
        }
    }

    /**
     * Sistem konfigürasyonunu güncelle
     */
    async updateConfig(config) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/system/config`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            this.systemConfig = { ...this.systemConfig, ...config };
            
            this.emit('system:config-updated', data);
            return data;
        } catch (error) {
            console.error('[SystemBridge] Konfigürasyon güncelleme hatası:', error);
            throw error;
        }
    }

    /**
     * Sistem komutunu çalıştır
     */
    async executeCommand(command, args = {}) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/system/command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command: command,
                    arguments: args
                })
            });
            
            const data = await response.json();
            this.emit('system:command-executed', data);
            
            return data;
        } catch (error) {
            console.error('[SystemBridge] Komut çalıştırma hatası:', error);
            throw error;
        }
    }

    /**
     * Servisleri al
     */
    async getServices() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/system/services`);
            return await response.json();
        } catch (error) {
            console.error('[SystemBridge] Servisler alınamadı:', error);
            throw error;
        }
    }

    /**
     * Servisi başlat
     */
    async startService(serviceName) {
        return this.executeCommand('start_service', { service: serviceName });
    }

    /**
     * Servisi durdur
     */
    async stopService(serviceName) {
        return this.executeCommand('stop_service', { service: serviceName });
    }

    /**
     * Python kodu çalıştır
     */
    async executePython(code, context = {}) {
        try {
            const response = await fetch(this.pythonEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: code,
                    context: context
                })
            });
            
            const data = await response.json();
            this.emit('python:executed', data);
            
            return data;
        } catch (error) {
            console.error('[SystemBridge] Python kodu çalıştırma hatası:', error);
            throw error;
        }
    }

    /**
     * Sistem durumunu periyodik olarak kontrol et
     */
    startHealthCheck(interval = 30000) {
        setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBaseUrl}/system/health`);
                const data = await response.json();
                
                this.systemStatus = data.status;
                this.emit('system:health-check', data);
                
                if (data.status.overall !== 'healthy') {
                    console.warn('[SystemBridge] Sistem sağlığı uyarısı:', data);
                }
            } catch (error) {
                console.error('[SystemBridge] Sağlık kontrolü hatası:', error);
                this.emit('system:connection-lost');
            }
        }, interval);
    }

    /**
     * Event listener'ları ayarla
     */
    setupEventListeners() {
        // Vue.js veya diğer framework'ler bunu dinleyebilir
        window.addEventListener('beforeunload', () => {
            this.emit('system:shutdown');
        });
    }

    /**
     * Event dinlemek
     */
    on(eventName, callback) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }
        this.listeners.get(eventName).push(callback);
    }

    /**
     * Event gönder
     */
    emit(eventName, data = null) {
        if (this.listeners.has(eventName)) {
            this.listeners.get(eventName).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[SystemBridge] Event '${eventName}' işleme hatası:`, error);
                }
            });
        }
    }

    /**
     * Event dinlemesini kaldır
     */
    off(eventName, callback) {
        if (this.listeners.has(eventName)) {
            const callbacks = this.listeners.get(eventName);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * Bağlantı durumunu al
     */
    isReady() {
        return this.isConnected;
    }

    /**
     * Sistem bilgisini al
     */
    getSystemInfo() {
        return {
            config: this.systemConfig,
            status: this.systemStatus
        };
    }
}

// Global instance
const systemBridge = new SystemBridge();

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SystemBridge;
}
