/**
 * Model Senkronizasyonu - Python ve JavaScript Modelleri Senkronize Et
 * Veri tutarlılığını sağla
 */

class ModelSync {
    constructor(systemBridge) {
        this.systemBridge = systemBridge;
        this.models = new Map();
        this.syncInterval = 60000; // 1 dakika
        this.lastSyncTime = null;
        this.syncStatus = 'idle';
        this.listeners = new Map();
    }

    /**
     * Senkronizasyonu başlat
     */
    async start() {
        try {
            console.log('[ModelSync] Başlatılıyor...');
            
            // İlk senkronizasyonu yapmak
            await this.syncAll();
            
            // Periyodik senkronizasyon
            setInterval(() => this.syncAll(), this.syncInterval);
            
            console.log('[ModelSync] Hazır');
        } catch (error) {
            console.error('[ModelSync] Başlatma hatası:', error);
        }
    }

    /**
     * Tüm modelleri senkronize et
     */
    async syncAll() {
        try {
            this.syncStatus = 'syncing';
            this.emit('sync:start');
            
            const results = {
                userModels: await this.syncUserModels(),
                systemModels: await this.syncSystemModels(),
                frameworkModels: await this.syncFrameworkModels(),
                deviceModels: await this.syncDeviceModels()
            };
            
            this.lastSyncTime = new Date();
            this.syncStatus = 'synced';
            this.emit('sync:complete', results);
            
            console.log('[ModelSync] Senkronizasyon tamamlandı', results);
            return results;
        } catch (error) {
            this.syncStatus = 'error';
            console.error('[ModelSync] Senkronizasyon hatası:', error);
            this.emit('sync:error', error);
            throw error;
        }
    }

    /**
     * Kullanıcı modellerini senkronize et
     */
    async syncUserModels() {
        try {
            const response = await fetch('/api/models?type=user');
            const data = await response.json();
            
            // JavaScript modeline dönüştür
            const jsModels = data.users.map(user => this.pythonUserToJS(user));
            
            this.models.set('users', jsModels);
            this.emit('sync:users', jsModels);
            
            return {
                count: jsModels.length,
                status: 'synced'
            };
        } catch (error) {
            console.error('[ModelSync] Kullanıcı senkronizasyon hatası:', error);
            return { status: 'error', error: error.message };
        }
    }

    /**
     * Sistem modellerini senkronize et
     */
    async syncSystemModels() {
        try {
            const response = await fetch('/api/models?type=system');
            const data = await response.json();
            
            this.models.set('system', data);
            this.emit('sync:system', data);
            
            return {
                status: 'synced',
                data: data
            };
        } catch (error) {
            console.error('[ModelSync] Sistem senkronizasyon hatası:', error);
            return { status: 'error', error: error.message };
        }
    }

    /**
     * Framework modellerini senkronize et
     */
    async syncFrameworkModels() {
        try {
            const response = await fetch('/api/frameworks');
            const data = await response.json();
            
            this.models.set('frameworks', data.frameworks);
            this.emit('sync:frameworks', data.frameworks);
            
            return {
                count: data.frameworks.length,
                installed: data.installed,
                available: data.available,
                status: 'synced'
            };
        } catch (error) {
            console.error('[ModelSync] Framework senkronizasyon hatası:', error);
            return { status: 'error', error: error.message };
        }
    }

    /**
     * Cihaz modellerini senkronize et
     */
    async syncDeviceModels() {
        try {
            const response = await fetch('/api/devices');
            const data = await response.json();
            
            this.models.set('devices', data.devices);
            this.emit('sync:devices', data.devices);
            
            return {
                count: data.devices.length,
                connected: data.connected,
                status: 'synced'
            };
        } catch (error) {
            console.error('[ModelSync] Cihaz senkronizasyon hatası:', error);
            return { status: 'error', error: error.message };
        }
    }

    /**
     * Python kullanıcı modelini JavaScript'e dönüştür
     */
    pythonUserToJS(pythonUser) {
        return {
            id: pythonUser.id,
            username: pythonUser.username,
            email: pythonUser.email,
            isActive: pythonUser.is_active,
            roles: pythonUser.roles,
            permissions: pythonUser.permissions,
            createdAt: new Date(pythonUser.created_at),
            updatedAt: new Date(pythonUser.updated_at)
        };
    }

    /**
     * JavaScript kullanıcı modelini Python'a dönüştür
     */
    jsUserToPython(jsUser) {
        return {
            username: jsUser.username,
            email: jsUser.email,
            is_active: jsUser.isActive,
            roles: jsUser.roles,
            permissions: jsUser.permissions
        };
    }

    /**
     * Model al
     */
    getModel(modelType) {
        return this.models.get(modelType);
    }

    /**
     * Modeli güncelle
     */
    async updateModel(modelType, modelId, data) {
        try {
            const response = await fetch(`/api/models/${modelId}?type=${modelType}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const updatedData = await response.json();
            this.emit('model:updated', { type: modelType, id: modelId, data: updatedData });
            
            return updatedData;
        } catch (error) {
            console.error('[ModelSync] Model güncelleme hatası:', error);
            throw error;
        }
    }

    /**
     * Modeli sil
     */
    async deleteModel(modelType, modelId) {
        try {
            const response = await fetch(`/api/models/${modelId}?type=${modelType}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            this.emit('model:deleted', { type: modelType, id: modelId });
            
            return result;
        } catch (error) {
            console.error('[ModelSync] Model silme hatası:', error);
            throw error;
        }
    }

    /**
     * Senkronizasyon durumunu al
     */
    getSyncStatus() {
        return {
            status: this.syncStatus,
            lastSyncTime: this.lastSyncTime,
            models: Array.from(this.models.keys())
        };
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
                    console.error(`[ModelSync] Event '${eventName}' işleme hatası:`, error);
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
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModelSync;
}
