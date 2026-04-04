/**
 * Uygulama Başlangıcı - Sistem Entegrasyonu
 * PHP, JavaScript ve Python modellerini bir araya getir
 */

class Application {
    constructor() {
        this.systemBridge = null;
        this.modelSync = null;
        this.apiClient = null;
        this.frameworkManager = null;
        this.isReady = false;
        this.logger = this.createLogger();
    }

    /**
     * Uygulama başlangıcı
     */
    async initialize() {
        try {
            this.logger.info('Uygulama başlatılıyor...');

            // 1. API Client'ı başlat
            this.apiClient = new ApiClient();
            this.logger.info('API Client başladı');

            // 2. System Bridge'i başlat
            this.systemBridge = new SystemBridge();
            await this.systemBridge.initialize();
            this.logger.info('System Bridge başladı');

            // 3. Model Senkronizasyonunu başlat
            this.modelSync = new ModelSync(this.systemBridge);
            await this.modelSync.start();
            this.logger.info('Model Senkronizasyonu başladı');

            // 4. Framework Manager'ı başlat
            this.frameworkManager = new FrameworkManager(this.apiClient, this.modelSync);
            await this.frameworkManager.initialize();
            this.logger.info('Framework Manager başladı');

            // 5. Event listener'ları ayarla
            this.setupEventListeners();

            // 6. Sağlık kontrolünü başlat
            this.systemBridge.startHealthCheck(30000);

            this.isReady = true;
            this.logger.info('Uygulama tamamen başlatıldı');
            this.onApplicationReady();

            return {
                success: true,
                timestamp: new Date(),
                components: {
                    systemBridge: this.systemBridge.isReady(),
                    modelSync: this.modelSync.getSyncStatus(),
                    frameworks: this.frameworkManager.getStatistics()
                }
            };
        } catch (error) {
            this.logger.error('Uygulama başlatılırken hata oluştu:', error);
            throw error;
        }
    }

    /**
     * Event listener'ları ayarla
     */
    setupEventListeners() {
        // System Bridge Events
        this.systemBridge.on('system:ready', () => {
            this.logger.info('Sistem hazır');
        });

        this.systemBridge.on('system:health-check', (data) => {
            if (data.status.overall !== 'healthy') {
                this.logger.warn('Sistem sağlığı uyarısı:', data.status);
            }
        });

        this.systemBridge.on('system:connection-lost', () => {
            this.logger.error('Sistem bağlantısı kesildi');
        });

        // Model Sync Events
        this.modelSync.on('sync:complete', (results) => {
            this.logger.info('Modeller senkronize edildi:', results);
        });

        this.modelSync.on('sync:error', (error) => {
            this.logger.error('Model senkronizasyon hatası:', error);
        });

        // Framework Manager Events
        this.frameworkManager.on('frameworks:loaded', (stats) => {
            this.logger.info('Framework\'ler yüklendi:', stats);
        });

        this.frameworkManager.on('framework:installed', (data) => {
            this.logger.info(`Framework kuruldu: ${data.name}`);
        });

        this.frameworkManager.on('framework:error', (error) => {
            this.logger.error('Framework hatası:', error);
        });
    }

    /**
     * Uygulama hazır oldu callback
     */
    onApplicationReady() {
        // Vue.js veya diğer framework'ler bunu dinleyebilir
        if (window.appReadyCallbacks) {
            window.appReadyCallbacks.forEach(callback => callback());
        }

        // Custom event gönder
        window.dispatchEvent(new CustomEvent('applicationReady', {
            detail: this.getApplicationState()
        }));
    }

    /**
     * Uygulama durumunu al
     */
    getApplicationState() {
        return {
            ready: this.isReady,
            timestamp: new Date(),
            system: this.systemBridge.getSystemInfo(),
            models: this.modelSync.getSyncStatus(),
            frameworks: this.frameworkManager.getStatistics()
        };
    }

    /**
     * Logger oluştur
     */
    createLogger() {
        return {
            info: (message, data) => console.log(`[INFO] ${message}`, data),
            warn: (message, data) => console.warn(`[WARN] ${message}`, data),
            error: (message, data) => console.error(`[ERROR] ${message}`, data),
            debug: (message, data) => console.debug(`[DEBUG] ${message}`, data)
        };
    }

    /**
     * Python kodu çalıştır
     */
    async executePython(code, context = {}) {
        return this.systemBridge.executePython(code, context);
    }

    /**
     * Framework kur
     */
    async installFramework(name, path) {
        return this.frameworkManager.installFramework(name, path);
    }

    /**
     * Framework kaldır
     */
    async uninstallFramework(name) {
        return this.frameworkManager.uninstallFramework(name);
    }

    /**
     * Sistem durumunu kontrol et
     */
    async checkSystemHealth() {
        const response = await this.apiClient.system.health();
        return response;
    }

    /**
     * Veritabanı bağlantısını test et
     */
    async testDatabaseConnection() {
        try {
            const response = await this.apiClient.system.info();
            return { success: true, message: 'Veritabanı bağlantısı başarılı' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Tüm servisleri başlat
     */
    async startAllServices() {
        try {
            const services = await this.apiClient.system.services();
            
            for (const service of services) {
                await this.apiClient.system.startService(service.name);
                this.logger.info(`${service.name} servisi başlatıldı`);
            }
            
            return { success: true, servicesStarted: services.length };
        } catch (error) {
            this.logger.error('Servisler başlatılamadı:', error);
            throw error;
        }
    }

    /**
     * Tüm servisleri durdur
     */
    async stopAllServices() {
        try {
            const services = await this.apiClient.system.services();
            
            for (const service of services) {
                await this.apiClient.system.stopService(service.name);
                this.logger.info(`${service.name} servisi durduruldu`);
            }
            
            return { success: true, servicesStopped: services.length };
        } catch (error) {
            this.logger.error('Servisler durdurulamadı:', error);
            throw error;
        }
    }

    /**
     * Uygulamayı kapatma
     */
    async shutdown() {
        try {
            this.logger.info('Uygulama kapatılıyor...');
            
            // Servisleri durdur
            await this.stopAllServices();
            
            // Bağlantıları kapat
            this.systemBridge.emit('system:shutdown');
            
            this.isReady = false;
            this.logger.info('Uygulama kapatıldı');
            
            return { success: true, shutdownTime: new Date() };
        } catch (error) {
            this.logger.error('Kapatma sırasında hata:', error);
            throw error;
        }
    }
}

// Global application instance
const app = new Application();

// Otomatik başlatma
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        app.initialize().catch(error => {
            console.error('Uygulama başlatılamadı:', error);
        });
    });
} else {
    app.initialize().catch(error => {
        console.error('Uygulama başlatılamadı:', error);
    });
}

// Vue.js entegrasyonu için
if (window.Vue) {
    window.appReadyCallbacks = window.appReadyCallbacks || [];
    window.appReadyCallbacks.push(() => {
        console.log('[Vue.js] Uygulamaya hazır');
    });
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Application;
}
