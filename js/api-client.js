/**
 * API Client - RESTful API ile iletişim
 * Tüm API endpoint'lerini yönet
 */

class ApiClient {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        this.timeout = 30000;
        this.retryAttempts = 3;
        this.retryDelay = 1000;
    }

    /**
     * İstek yap
     */
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const fetchOptions = {
            method: method,
            headers: this.headers,
            ...options
        };

        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            fetchOptions.body = JSON.stringify(data);
        }

        try {
            const response = await this.fetchWithTimeout(url, fetchOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            if (this.retryAttempts > 0) {
                console.warn(`[ApiClient] Tekrar deneniyor (${this.retryAttempts}) - ${endpoint}`);
                this.retryAttempts--;
                
                await this.delay(this.retryDelay);
                return this.request(method, endpoint, data, options);
            }
            
            throw error;
        }
    }

    /**
     * Timeout ile fetch yap
     */
    fetchWithTimeout(url, options) {
        return Promise.race([
            fetch(url, options),
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Request timeout')), this.timeout)
            )
        ]);
    }

    /**
     * Gecikmeli promise
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Model işlemleri
     */
    models = {
        list: async (type) => this.request('GET', `/models?type=${type}`),
        get: async (id) => this.request('GET', `/models/${id}`),
        create: async (data) => this.request('POST', '/models', data),
        update: async (id, data) => this.request('PUT', `/models/${id}`, data),
        delete: async (id) => this.request('DELETE', `/models/${id}`)
    }

    /**
     * Sistem işlemleri
     */
    system = {
        info: async () => this.request('GET', '/system/info'),
        status: async () => this.request('GET', '/system/status'),
        health: async () => this.request('GET', '/system/health'),
        config: async () => this.request('GET', '/system/config'),
        updateConfig: async (config) => this.request('PUT', '/system/config', config),
        command: async (command, args) => this.request('POST', '/system/command', { command, args }),
        services: async () => this.request('GET', '/system/services'),
        startService: async (service) => this.request('POST', '/system/services/start', { service }),
        stopService: async (service) => this.request('POST', '/system/services/stop', { service })
    }

    /**
     * Framework işlemleri
     */
    frameworks = {
        list: async () => this.request('GET', '/frameworks'),
        get: async (name) => this.request('GET', `/frameworks/${name}`),
        install: async (name, path) => this.request('POST', '/frameworks/install', { name, path }),
        uninstall: async (name) => this.request('POST', '/frameworks/uninstall', { name }),
        status: async () => this.request('GET', '/frameworks/status')
    }

    /**
     * Cihaz işlemleri
     */
    devices = {
        list: async () => this.request('GET', '/devices'),
        get: async (id) => this.request('GET', `/devices/${id}`),
        connected: async () => this.request('GET', '/devices/connected'),
        register: async (data) => this.request('POST', '/devices', data),
        update: async (id, data) => this.request('PUT', `/devices/${id}`, data),
        updateStatus: async (id, connected) => this.request('PATCH', `/devices/${id}/status`, { connected })
    }

    /**
     * Kullanıcı işlemleri
     */
    users = {
        list: async () => this.request('GET', '/users'),
        get: async (id) => this.request('GET', `/users/${id}`),
        create: async (data) => this.request('POST', '/users', data),
        update: async (id, data) => this.request('PUT', `/users/${id}`, data),
        delete: async (id) => this.request('DELETE', `/users/${id}`),
        active: async () => this.request('GET', '/users/active')
    }

    /**
     * Python kodu çalıştırma
     */
    python = {
        execute: async (code, context = {}) => 
            this.request('POST', '/execute/python', { code, context }),
        executeModel: async (modelName, method, args = {}) =>
            this.request('POST', '/execute/model', { model: modelName, method, args })
    }

    /**
     * File işlemleri
     */
    files = {
        list: async (path) => this.request('GET', `/files?path=${encodeURIComponent(path)}`),
        upload: async (file, path) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('path', path);
            
            return fetch(`${this.baseUrl}/files/upload`, {
                method: 'POST',
                body: formData
            }).then(r => r.json());
        },
        download: async (path) => {
            window.location.href = `${this.baseUrl}/files/download?path=${encodeURIComponent(path)}`;
        }
    }

    /**
     * Hata işleme
     */
    handleError(error) {
        console.error('[ApiClient] Hata:', error);
        
        if (error.message === 'Request timeout') {
            return {
                success: false,
                error: 'İstek zaman aşımına uğradı',
                code: 'TIMEOUT'
            };
        }
        
        return {
            success: false,
            error: error.message,
            code: 'REQUEST_FAILED'
        };
    }

    /**
     * Batch istek yap
     */
    async batch(requests) {
        try {
            const results = await Promise.all(
                requests.map(req => this.request(req.method, req.endpoint, req.data))
            );
            return { success: true, results };
        } catch (error) {
            return this.handleError(error);
        }
    }
}

// Global instance
const apiClient = new ApiClient();

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
}
