/**
 * Framework Yöneticisi - Vue.js, Oracle JET ve diğer frameworkleri yönet
 */

class FrameworkManager {
    constructor(apiClient, modelSync) {
        this.apiClient = apiClient;
        this.modelSync = modelSync;
        this.frameworks = new Map();
        this.installedFrameworks = new Set();
        this.listeners = new Map();
    }

    /**
     * Framework yöneticisini başlat
     */
    async initialize() {
        try {
            console.log('[FrameworkManager] Başlatılıyor...');
            
            // Mevcut frameworkleri yükle
            await this.loadFrameworks();
            
            // Kurulu frameworkleri kontrol et
            await this.checkInstalledFrameworks();
            
            console.log('[FrameworkManager] Hazır');
            this.emit('manager:ready');
        } catch (error) {
            console.error('[FrameworkManager] Başlatma hatası:', error);
            this.emit('manager:error', error);
        }
    }

    /**
     * Framework'leri yükle
     */
    async loadFrameworks() {
        try {
            const data = await this.apiClient.frameworks.list();
            
            data.frameworks.forEach(fw => {
                this.frameworks.set(fw.name, fw);
                if (fw.installed) {
                    this.installedFrameworks.add(fw.name);
                }
            });
            
            this.emit('frameworks:loaded', {
                total: this.frameworks.size,
                installed: this.installedFrameworks.size
            });
        } catch (error) {
            console.error('[FrameworkManager] Framework yüklemesi başarısız:', error);
            this.emit('frameworks:error', error);
        }
    }

    /**
     * Kurulu frameworkleri kontrol et
     */
    async checkInstalledFrameworks() {
        try {
            const status = await this.apiClient.frameworks.status();
            
            status.installed.forEach(name => {
                this.installedFrameworks.add(name);
            });
            
            this.emit('frameworks:status-checked', status);
        } catch (error) {
            console.error('[FrameworkManager] Durum kontrolü başarısız:', error);
        }
    }

    /**
     * Framework kur
     */
    async installFramework(frameworkName, installPath) {
        try {
            console.log(`[FrameworkManager] ${frameworkName} kuruluyor...`);
            this.emit('framework:installing', { name: frameworkName });
            
            const result = await this.apiClient.frameworks.install(frameworkName, installPath);
            
            if (result.success) {
                this.installedFrameworks.add(frameworkName);
                const fw = this.frameworks.get(frameworkName);
                if (fw) {
                    fw.installed = true;
                    fw.install_path = installPath;
                }
                
                this.emit('framework:installed', {
                    name: frameworkName,
                    path: installPath,
                    version: fw?.version
                });
            }
            
            return result;
        } catch (error) {
            console.error(`[FrameworkManager] ${frameworkName} kurulumu başarısız:`, error);
            this.emit('framework:install-error', { name: frameworkName, error });
            throw error;
        }
    }

    /**
     * Framework kaldır
     */
    async uninstallFramework(frameworkName) {
        try {
            console.log(`[FrameworkManager] ${frameworkName} kaldırılıyor...`);
            this.emit('framework:uninstalling', { name: frameworkName });
            
            const result = await this.apiClient.frameworks.uninstall(frameworkName);
            
            if (result.success) {
                this.installedFrameworks.delete(frameworkName);
                const fw = this.frameworks.get(frameworkName);
                if (fw) {
                    fw.installed = false;
                    fw.install_path = null;
                }
                
                this.emit('framework:uninstalled', { name: frameworkName });
            }
            
            return result;
        } catch (error) {
            console.error(`[FrameworkManager] ${frameworkName} kaldırılması başarısız:`, error);
            this.emit('framework:uninstall-error', { name: frameworkName, error });
            throw error;
        }
    }

    /**
     * Vue.js kurulumunu başlat
     */
    async setupVueJs(projectPath = './vue-project') {
        try {
            console.log('[FrameworkManager] Vue.js ayarlanıyor...');
            
            const commands = [
                'npm install -g @vue/cli',
                `vue create ${projectPath}`,
                `cd ${projectPath} && npm install`,
                `cd ${projectPath} && npm install @oracle/oraclejet`
            ];
            
            for (const command of commands) {
                await this.executeCommand(command);
                console.log(`[FrameworkManager] Komut yürütüldü: ${command}`);
            }
            
            await this.installFramework('Vue.js', projectPath);
            this.emit('vuejs:setup-complete', { projectPath });
            
            return { success: true, projectPath };
        } catch (error) {
            console.error('[FrameworkManager] Vue.js kurulumu başarısız:', error);
            this.emit('vuejs:setup-error', error);
            throw error;
        }
    }

    /**
     * Oracle JET kurulumunu başlat
     */
    async setupOracleJET(projectPath = './oracle-jet-project') {
        try {
            console.log('[FrameworkManager] Oracle JET ayarlanıyor...');
            
            const commands = [
                'npm install -g @oracle/oraclejet-cli',
                `ojet create ${projectPath}`,
                `cd ${projectPath} && npm install`
            ];
            
            for (const command of commands) {
                await this.executeCommand(command);
                console.log(`[FrameworkManager] Komut yürütüldü: ${command}`);
            }
            
            await this.installFramework('Oracle JET', projectPath);
            this.emit('oraclejet:setup-complete', { projectPath });
            
            return { success: true, projectPath };
        } catch (error) {
            console.error('[FrameworkManager] Oracle JET kurulumu başarısız:', error);
            this.emit('oraclejet:setup-error', error);
            throw error;
        }
    }

    /**
     * Framework'ü al
     */
    getFramework(name) {
        return this.frameworks.get(name);
    }

    /**
     * Tüm frameworkleri al
     */
    getAllFrameworks() {
        return Array.from(this.frameworks.values());
    }

    /**
     * Kurulu frameworkleri al
     */
    getInstalledFrameworks() {
        return Array.from(this.installedFrameworks);
    }

    /**
     * Kullanılabilir frameworkleri al
     */
    getAvailableFrameworks() {
        const available = [];
        this.frameworks.forEach((fw, name) => {
            if (!this.installedFrameworks.has(name)) {
                available.push(fw);
            }
        });
        return available;
    }

    /**
     * Framework kurulu mu kontrol et
     */
    isFrameworkInstalled(name) {
        return this.installedFrameworks.has(name);
    }

    /**
     * Framework bağımlılıklarını al
     */
    getFrameworkDependencies(name) {
        const fw = this.frameworks.get(name);
        return fw ? fw.dependencies : [];
    }

    /**
     * İstatistik al
     */
    getStatistics() {
        return {
            total: this.frameworks.size,
            installed: this.installedFrameworks.size,
            available: this.frameworks.size - this.installedFrameworks.size,
            frameworks: Array.from(this.frameworks.values()).map(fw => ({
                name: fw.name,
                version: fw.version,
                installed: this.installedFrameworks.has(fw.name)
            }))
        };
    }

    /**
     * Komut çalıştır (mock)
     */
    async executeCommand(command) {
        try {
            // Gerçek uygulamada Python veya Node.js üzerinden çalıştırılacak
            const result = await this.apiClient.python.execute(
                `import subprocess; subprocess.run(['${command}'], shell=True)`
            );
            return result;
        } catch (error) {
            console.error('[FrameworkManager] Komut çalıştırma hatası:', error);
            throw error;
        }
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
                    console.error(`[FrameworkManager] Event '${eventName}' işleme hatası:`, error);
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
    module.exports = FrameworkManager;
}
