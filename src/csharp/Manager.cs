using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using System.Diagnostics;
using System.Reflection;
using System.Linq;
using System.Threading;

namespace manager.src
{
    #region Attributes

    /// <summary>
    /// Manager bileşeni için attribute
    /// </summary>
    [System.AttributeUsage(System.AttributeTargets.Class, Inherited = false, AllowMultiple = false)]
    public sealed class ManagerAttribute : System.Attribute
    {
        public string Name { get; }
        public string Description { get; set; }
        public int Priority { get; set; } = 100;
        public bool IsSingleton { get; set; } = true;

        public ManagerAttribute(string name)
        {
            Name = name ?? throw new ArgumentNullException(nameof(name));
        }
    }

    /// <summary>
    /// Servis bağımlılığı için attribute
    /// </summary>
    [System.AttributeUsage(System.AttributeTargets.Property | System.AttributeTargets.Field, Inherited = false, AllowMultiple = false)]
    public sealed class InjectAttribute : System.Attribute
    {
        public string ServiceName { get; set; }
        public bool IsRequired { get; set; } = true;

        public InjectAttribute() { }

        public InjectAttribute(string serviceName)
        {
            ServiceName = serviceName;
        }
    }

    /// <summary>
    /// Konfigürasyon özelliği için attribute
    /// </summary>
    [System.AttributeUsage(System.AttributeTargets.Property, Inherited = false, AllowMultiple = false)]
    public sealed class ConfigAttribute : System.Attribute
    {
        public string Key { get; }
        public object DefaultValue { get; set; }

        public ConfigAttribute(string key)
        {
            Key = key ?? throw new ArgumentNullException(nameof(key));
        }
    }

    #endregion

    #region Interfaces

    /// <summary>
    /// Manager bileşeni arayüzü
    /// </summary>
    public interface IManager
    {
        string Name { get; }
        bool IsInitialized { get; }
        Task InitializeAsync();
        Task ShutdownAsync();
        Task<bool> HealthCheckAsync();
    }

    /// <summary>
    /// Servis arayüzü
    /// </summary>
    public interface IService
    {
        string ServiceName { get; }
        ServiceStatus Status { get; }
        Task StartAsync();
        Task StopAsync();
        Task RestartAsync();
    }

    /// <summary>
    /// Plugin arayüzü
    /// </summary>
    public interface IPlugin
    {
        string PluginName { get; }
        string Version { get; }
        Task LoadAsync();
        Task UnloadAsync();
        IEnumerable<string> GetDependencies();
    }

    /// <summary>
    /// Konfigürasyon sağlayıcı arayüzü
    /// </summary>
    public interface IConfigurationProvider
    {
        Task<T> GetValueAsync<T>(string key, T defaultValue = default);
        Task SetValueAsync<T>(string key, T value);
        Task<bool> ContainsKeyAsync(string key);
        Task<IEnumerable<string>> GetKeysAsync(string prefix = null);
    }

    #endregion

    #region Enums

    /// <summary>
    /// Servis durumu
    /// </summary>
    public enum ServiceStatus
    {
        Stopped,
        Starting,
        Running,
        Stopping,
        Failed
    }

    /// <summary>
    /// Uygulama durumu
    /// </summary>
    public enum ApplicationStatus
    {
        NotStarted,
        Starting,
        Running,
        Stopping,
        Stopped,
        Error
    }

    /// <summary>
    /// Log seviyesi
    /// </summary>
    public enum LogLevel
    {
        Debug,
        Info,
        Warning,
        Error,
        Critical
    }

    #endregion

    #region Core Classes

    /// <summary>
    /// Ana uygulama yöneticisi
    /// </summary>
    [Manager("ApplicationManager", Description = "Ana uygulama yönetim sistemi")]
    public class ApplicationManager : IManager
    {
        private readonly Dictionary<string, IManager> _managers = new();
        private readonly Dictionary<string, IService> _services = new();
        private readonly Dictionary<string, IPlugin> _plugins = new();
        private readonly List<ILogger> _loggers = new();
        private ApplicationStatus _status = ApplicationStatus.NotStarted;
        private readonly CancellationTokenSource _cts = new();

        public string Name => "ApplicationManager";
        public bool IsInitialized => _status == ApplicationStatus.Running;
        public ApplicationStatus Status => _status;

        /// <summary>
        /// Uygulamayı başlat
        /// </summary>
        public async Task InitializeAsync()
        {
            if (_status != ApplicationStatus.NotStarted)
                throw new InvalidOperationException("Uygulama zaten başlatılmış");

            _status = ApplicationStatus.Starting;

            try
            {
                await LogAsync(LogLevel.Info, "Uygulama başlatılıyor...");

                // Manager'ları keşfet ve kaydet
                await DiscoverAndRegisterManagersAsync();

                // Manager'ları başlat (öncelik sırasına göre)
                await InitializeManagersAsync();

                // Servisleri başlat
                await StartServicesAsync();

                // Plugin'leri yükle
                await LoadPluginsAsync();

                _status = ApplicationStatus.Running;
                await LogAsync(LogLevel.Info, "Uygulama başarıyla başlatıldı");
            }
            catch (Exception ex)
            {
                _status = ApplicationStatus.Error;
                await LogAsync(LogLevel.Critical, $"Uygulama başlatma hatası: {ex.Message}", ex);
                throw;
            }
        }

        /// <summary>
        /// Uygulamayı kapat
        /// </summary>
        public async Task ShutdownAsync()
        {
            if (_status != ApplicationStatus.Running)
                return;

            _status = ApplicationStatus.Stopping;

            try
            {
                await LogAsync(LogLevel.Info, "Uygulama kapatılıyor...");

                // Plugin'leri kaldır
                await UnloadPluginsAsync();

                // Servisleri durdur
                await StopServicesAsync();

                // Manager'ları kapat
                await ShutdownManagersAsync();

                _cts.Cancel();
                _status = ApplicationStatus.Stopped;

                await LogAsync(LogLevel.Info, "Uygulama başarıyla kapatıldı");
            }
            catch (Exception ex)
            {
                await LogAsync(LogLevel.Error, $"Uygulama kapatma hatası: {ex.Message}", ex);
                throw;
            }
        }

        /// <summary>
        /// Sağlık kontrolü
        /// </summary>
        public async Task<Dictionary<string, bool>> HealthCheckAsync()
        {
            var results = new Dictionary<string, bool>();

            // Manager'ların sağlık kontrolü
            foreach (var manager in _managers.Values)
            {
                try
                {
                    await manager.HealthCheckAsync();
                    results[manager.Name] = true;
                }
                catch
                {
                    results[manager.Name] = false;
                }
            }

            // Servislerin sağlık kontrolü
            foreach (var service in _services.Values)
            {
                results[service.ServiceName] = service.Status == ServiceStatus.Running;
            }

            var allHealthy = results.Values.All(x => x);
            if (!allHealthy)
            {
                await LogAsync(LogLevel.Warning, "Sağlık kontrolü başarısız bileşenler var");
            }

            return results;
        }

        /// <summary>
        /// Manager kaydet
        /// </summary>
        public void RegisterManager(IManager manager)
        {
            _managers[manager.Name] = manager;
        }

        /// <summary>
        /// Manager al
        /// </summary>
        public T GetManager<T>() where T : IManager
        {
            var manager = _managers.Values.FirstOrDefault(m => m is T);
            return manager != null ? (T)manager : throw new KeyNotFoundException($"Manager {typeof(T).Name} bulunamadı");
        }

        /// <summary>
        /// Servis kaydet
        /// </summary>
        public void RegisterService(IService service)
        {
            _services[service.ServiceName] = service;
        }

        /// <summary>
        /// Servis al
        /// </summary>
        public T GetService<T>() where T : IService
        {
            var service = _services.Values.FirstOrDefault(s => s is T);
            return service != null ? (T)service : throw new KeyNotFoundException($"Servis {typeof(T).Name} bulunamadı");
        }

        /// <summary>
        /// Plugin kaydet
        /// </summary>
        public void RegisterPlugin(IPlugin plugin)
        {
            _plugins[plugin.PluginName] = plugin;
        }

        /// <summary>
        /// Logger ekle
        /// </summary>
        public void AddLogger(ILogger logger)
        {
            _loggers.Add(logger);
        }

        /// <summary>
        /// Log yaz
        /// </summary>
        public async Task LogAsync(LogLevel level, string message, Exception exception = null)
        {
            foreach (var logger in _loggers)
            {
                await logger.LogAsync(level, message, exception);
            }
        }

        #region Private Methods

        private async Task DiscoverAndRegisterManagersAsync()
        {
            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            var managerTypes = new List<Type>();

            foreach (var assembly in assemblies)
            {
                try
                {
                    var types = assembly.GetTypes()
                        .Where(t => typeof(IManager).IsAssignableFrom(t) &&
                                   t.IsClass && !t.IsAbstract &&
                                   t.GetCustomAttribute<ManagerAttribute>() != null);

                    managerTypes.AddRange(types);
                }
                catch (Exception ex)
                {
                    await LogAsync(LogLevel.Warning, $"Assembly tarama hatası {assembly.FullName}: {ex.Message}");
                }
            }

            // Öncelik sırasına göre sırala
            var orderedTypes = managerTypes
                .Select(t => (Type: t, Attribute: t.GetCustomAttribute<ManagerAttribute>()))
                .OrderBy(x => x.Attribute.Priority)
                .Select(x => x.Type);

            foreach (var type in orderedTypes)
            {
                try
                {
                    var manager = (IManager)Activator.CreateInstance(type);
                    RegisterManager(manager);
                    await LogAsync(LogLevel.Debug, $"Manager keşfedildi: {manager.Name}");
                }
                catch (Exception ex)
                {
                    await LogAsync(LogLevel.Error, $"Manager oluşturma hatası {type.Name}: {ex.Message}");
                }
            }
        }

        private async Task InitializeManagersAsync()
        {
            foreach (var manager in _managers.Values.OrderBy(m => m.GetType().GetCustomAttribute<ManagerAttribute>()?.Priority ?? 100))
            {
                try
                {
                    await manager.InitializeAsync();
                    await LogAsync(LogLevel.Info, $"Manager başlatıldı: {manager.Name}");
                }
                catch (Exception ex)
                {
                    await LogAsync(LogLevel.Error, $"Manager başlatma hatası {manager.Name}: {ex.Message}");
                    throw;
                }
            }
        }

        private async Task ShutdownManagersAsync()
        {
            foreach (var manager in _managers.Values.Reverse())
            {
                try
                {
                    await manager.ShutdownAsync();
                    await LogAsync(LogLevel.Info, $"Manager kapatıldı: {manager.Name}");
                }
                catch (Exception ex)
                {
                    await LogAsync(LogLevel.Error, $"Manager kapatma hatası {manager.Name}: {ex.Message}");
                }
            }
        }

        private async Task StartServicesAsync()
        {
            foreach (var service in _services.Values)
            {
                try
                {
                    await service.StartAsync();
                    await LogAsync(LogLevel.Info, $"Servis başlatıldı: {service.ServiceName}");
                }
                catch (Exception ex)
                {
                    await LogAsync(LogLevel.Error, $"Servis başlatma hatası {service.ServiceName}: {ex.Message}");
                }
            }
        }

        private async Task StopServicesAsync()
        {
            foreach (var service in _services.Values.Reverse())
            {
                try
                {
                    await service.StopAsync();
                    await LogAsync(LogLevel.Info, $"Servis durduruldu: {service.ServiceName}");
                }
                catch (Exception ex)
                {
                    await LogAsync(LogLevel.Error, $"Servis durdurma hatası {service.ServiceName}: {ex.Message}");
                }
            }
        }

        private async Task LoadPluginsAsync()
        {
            foreach (var plugin in _plugins.Values)
            {
                try
                {
                    await plugin.LoadAsync();
                    await LogAsync(LogLevel.Info, $"Plugin yüklendi: {plugin.PluginName}");
                }
                catch (Exception ex)
                {
                    await LogAsync(LogLevel.Error, $"Plugin yükleme hatası {plugin.PluginName}: {ex.Message}");
                }
            }
        }

        private async Task UnloadPluginsAsync()
        {
            foreach (var plugin in _plugins.Values.Reverse())
            {
                try
                {
                    await plugin.UnloadAsync();
                    await LogAsync(LogLevel.Info, $"Plugin kaldırıldı: {plugin.PluginName}");
                }
                catch (Exception ex)
                {
                    await LogAsync(LogLevel.Error, $"Plugin kaldırma hatası {plugin.PluginName}: {ex.Message}");
                }
            }
        }

        #endregion
    }

    /// <summary>
    /// Servis yöneticisi
    /// </summary>
    [Manager("ServiceManager", Description = "Servis yönetim sistemi", Priority = 50)]
    public class ServiceManager : IManager
    {
        private readonly Dictionary<string, IService> _services = new();
        private readonly ApplicationManager _appManager;

        [Inject]
        public ILogger Logger { get; set; }

        public string Name => "ServiceManager";
        public bool IsInitialized { get; private set; }

        public ServiceManager(ApplicationManager appManager)
        {
            _appManager = appManager;
        }

        public async Task InitializeAsync()
        {
            await Logger?.LogAsync(LogLevel.Info, "Servis yöneticisi başlatılıyor...");
            IsInitialized = true;
        }

        public async Task ShutdownAsync()
        {
            foreach (var service in _services.Values.Where(s => s.Status == ServiceStatus.Running))
            {
                await service.StopAsync();
            }
            IsInitialized = false;
        }

        public async Task<bool> HealthCheckAsync()
        {
            var failedServices = _services.Values.Where(s => s.Status == ServiceStatus.Failed).ToList();
            return !failedServices.Any();
        }

        public void RegisterService(IService service)
        {
            _services[service.ServiceName] = service;
        }

        public async Task StartServiceAsync(string serviceName)
        {
            if (_services.TryGetValue(serviceName, out var service))
            {
                await service.StartAsync();
            }
            else
            {
                throw new KeyNotFoundException($"Servis bulunamadı: {serviceName}");
            }
        }

        public async Task StopServiceAsync(string serviceName)
        {
            if (_services.TryGetValue(serviceName, out var service))
            {
                await service.StopAsync();
            }
            else
            {
                throw new KeyNotFoundException($"Servis bulunamadı: {serviceName}");
            }
        }

        public IEnumerable<IService> GetAllServices()
        {
            return _services.Values;
        }

        public IService GetService(string serviceName)
        {
            return _services.TryGetValue(serviceName, out var service) ? service : null;
        }
    }

    /// <summary>
    /// Konfigürasyon yöneticisi
    /// </summary>
    [Manager("ConfigurationManager", Description = "Konfigürasyon yönetim sistemi", Priority = 10)]
    public class ConfigurationManager : IManager, IConfigurationProvider
    {
        private readonly Dictionary<string, object> _configurations = new();
        private readonly string _configFilePath;
        private readonly ApplicationManager _appManager;

        [Inject]
        public ILogger Logger { get; set; }

        public string Name => "ConfigurationManager";
        public bool IsInitialized { get; private set; }

        public ConfigurationManager(ApplicationManager appManager)
        {
            _appManager = appManager;
            _configFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.json");
        }

        public async Task InitializeAsync()
        {
            await Logger?.LogAsync(LogLevel.Info, "Konfigürasyon yöneticisi başlatılıyor...");

            // Varsayılan konfigürasyonları yükle
            await LoadDefaultConfigurationsAsync();

            // Dosyadan konfigürasyonları yükle
            if (File.Exists(_configFilePath))
            {
                await LoadFromFileAsync();
            }

            IsInitialized = true;
        }

        public async Task ShutdownAsync()
        {
            await SaveToFileAsync();
            IsInitialized = false;
        }

        public async Task<bool> HealthCheckAsync()
        {
            // Konfigürasyon dosyasının erişilebilirliğini kontrol et
            try
            {
                using (var stream = File.Open(_configFilePath, FileMode.OpenOrCreate, FileAccess.ReadWrite))
                {
                    // Dosya erişilebilir
                }
                return true;
            }
            catch
            {
                return false;
            }
        }

        public async Task<T> GetValueAsync<T>(string key, T defaultValue = default)
        {
            if (_configurations.TryGetValue(key, out var value))
            {
                return (T)Convert.ChangeType(value, typeof(T));
            }
            return defaultValue;
        }

        public async Task SetValueAsync<T>(string key, T value)
        {
            _configurations[key] = value;
            await Logger?.LogAsync(LogLevel.Debug, $"Konfigürasyon güncellendi: {key} = {value}");
        }

        public async Task<bool> ContainsKeyAsync(string key)
        {
            return _configurations.ContainsKey(key);
        }

        public async Task<IEnumerable<string>> GetKeysAsync(string prefix = null)
        {
            var keys = _configurations.Keys;
            if (!string.IsNullOrEmpty(prefix))
            {
                keys = keys.Where(k => k.StartsWith(prefix)).ToList();
            }
            return keys;
        }

        private async Task LoadDefaultConfigurationsAsync()
        {
            await SetValueAsync("app.name", "Flask-Django-SDK");
            await SetValueAsync("app.version", "1.0.0");
            await SetValueAsync("app.environment", "development");
            await SetValueAsync("app.debug", true);
            await SetValueAsync("logging.level", "Info");
            await SetValueAsync("services.timeout", 30000);
            await SetValueAsync("cache.enabled", true);
            await SetValueAsync("cache.ttl", 3600);
        }

        private async Task LoadFromFileAsync()
        {
            try
            {
                var json = await File.ReadAllTextAsync(_configFilePath);
                var configs = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(json);

                if (configs != null)
                {
                    foreach (var kvp in configs)
                    {
                        _configurations[kvp.Key] = kvp.Value;
                    }
                }
            }
            catch (Exception ex)
            {
                await Logger?.LogAsync(LogLevel.Warning, $"Konfigürasyon dosyası yükleme hatası: {ex.Message}");
            }
        }

        private async Task SaveToFileAsync()
        {
            try
            {
                var json = System.Text.Json.JsonSerializer.Serialize(_configurations, new System.Text.Json.JsonSerializerOptions
                {
                    WriteIndented = true
                });
                await File.WriteAllTextAsync(_configFilePath, json);
            }
            catch (Exception ex)
            {
                await Logger?.LogAsync(LogLevel.Error, $"Konfigürasyon dosyası kaydetme hatası: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Logger arayüzü
    /// </summary>
    public interface ILogger
    {
        Task LogAsync(LogLevel level, string message, Exception exception = null);
    }

    /// <summary>
    /// Konsol logger
    /// </summary>
    public class ConsoleLogger : ILogger
    {
        public async Task LogAsync(LogLevel level, string message, Exception exception = null)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            var levelStr = level.ToString().ToUpper();
            var fullMessage = $"[{timestamp}] [{levelStr}] {message}";

            if (exception != null)
            {
                fullMessage += $"\nException: {exception.Message}\nStackTrace: {exception.StackTrace}";
            }

            Console.WriteLine(fullMessage);
            await Task.CompletedTask;
        }
    }

    /// <summary>
    /// Dosya logger
    /// </summary>
    public class FileLogger : ILogger
    {
        private readonly string _logFilePath;
        private readonly object _lock = new();

        public FileLogger(string logFilePath = null)
        {
            _logFilePath = logFilePath ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs", "app.log");

            // Logs klasörünü oluştur
            var logDir = Path.GetDirectoryName(_logFilePath);
            if (!Directory.Exists(logDir))
            {
                Directory.CreateDirectory(logDir);
            }
        }

        public async Task LogAsync(LogLevel level, string message, Exception exception = null)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            var levelStr = level.ToString().ToUpper();
            var fullMessage = $"[{timestamp}] [{levelStr}] {message}";

            if (exception != null)
            {
                fullMessage += $"\nException: {exception.Message}\nStackTrace: {exception.StackTrace}";
            }

            fullMessage += Environment.NewLine;

            lock (_lock)
            {
                File.AppendAllText(_logFilePath, fullMessage);
            }

            await Task.CompletedTask;
        }
    }

    #endregion

    #region Example Services

    /// <summary>
    /// Örnek servis - Veritabanı servisi
    /// </summary>
    public class DatabaseService : IService
    {
        public string ServiceName => "DatabaseService";
        public ServiceStatus Status { get; private set; } = ServiceStatus.Stopped;

        [Inject]
        public ILogger Logger { get; set; }

        [Config("database.connection_string")]
        public string ConnectionString { get; set; }

        public async Task StartAsync()
        {
            Status = ServiceStatus.Starting;
            await Logger?.LogAsync(LogLevel.Info, "Veritabanı servisi başlatılıyor...");

            try
            {
                // Veritabanı bağlantısı simülasyonu
                await Task.Delay(1000);

                Status = ServiceStatus.Running;
                await Logger?.LogAsync(LogLevel.Info, "Veritabanı servisi başlatıldı");
            }
            catch (Exception ex)
            {
                Status = ServiceStatus.Failed;
                await Logger?.LogAsync(LogLevel.Error, $"Veritabanı servisi başlatma hatası: {ex.Message}");
                throw;
            }
        }

        public async Task StopAsync()
        {
            Status = ServiceStatus.Stopping;
            await Logger?.LogAsync(LogLevel.Info, "Veritabanı servisi durduruluyor...");

            try
            {
                // Veritabanı bağlantısı kapatma simülasyonu
                await Task.Delay(500);

                Status = ServiceStatus.Stopped;
                await Logger?.LogAsync(LogLevel.Info, "Veritabanı servisi durduruldu");
            }
            catch (Exception ex)
            {
                await Logger?.LogAsync(LogLevel.Error, $"Veritabanı servisi durdurma hatası: {ex.Message}");
                throw;
            }
        }

        public async Task RestartAsync()
        {
            await StopAsync();
            await StartAsync();
        }
    }

    /// <summary>
    /// Örnek servis - Cache servisi
    /// </summary>
    public class CacheService : IService
    {
        public string ServiceName => "CacheService";
        public ServiceStatus Status { get; private set; } = ServiceStatus.Stopped;

        [Inject]
        public ILogger Logger { get; set; }

        [Config("cache.ttl")]
        public int DefaultTtl { get; set; } = 3600;

        private readonly Dictionary<string, (object Value, DateTime ExpiresAt)> _cache = new();

        public async Task StartAsync()
        {
            Status = ServiceStatus.Starting;
            await Logger?.LogAsync(LogLevel.Info, "Cache servisi başlatılıyor...");

            try
            {
                // Cache başlatma simülasyonu
                await Task.Delay(500);

                Status = ServiceStatus.Running;
                await Logger?.LogAsync(LogLevel.Info, "Cache servisi başlatıldı");
            }
            catch (Exception ex)
            {
                Status = ServiceStatus.Failed;
                await Logger?.LogAsync(LogLevel.Error, $"Cache servisi başlatma hatası: {ex.Message}");
                throw;
            }
        }

        public async Task StopAsync()
        {
            Status = ServiceStatus.Stopping;
            await Logger?.LogAsync(LogLevel.Info, "Cache servisi durduruluyor...");

            try
            {
                _cache.Clear();

                Status = ServiceStatus.Stopped;
                await Logger?.LogAsync(LogLevel.Info, "Cache servisi durduruldu");
            }
            catch (Exception ex)
            {
                await Logger?.LogAsync(LogLevel.Error, $"Cache servisi durdurma hatası: {ex.Message}");
                throw;
            }
        }

        public async Task RestartAsync()
        {
            await StopAsync();
            await StartAsync();
        }

        public async Task SetAsync<T>(string key, T value, int ttl = 0)
        {
            if (Status != ServiceStatus.Running)
                throw new InvalidOperationException("Cache servisi çalışmıyor");

            var expiresAt = DateTime.Now.AddSeconds(ttl > 0 ? ttl : DefaultTtl);
            _cache[key] = (value, expiresAt);

            await Logger?.LogAsync(LogLevel.Debug, $"Cache'e eklendi: {key}");
        }

        public async Task<T> GetAsync<T>(string key)
        {
            if (Status != ServiceStatus.Running)
                throw new InvalidOperationException("Cache servisi çalışmıyor");

            if (_cache.TryGetValue(key, out var item))
            {
                if (DateTime.Now < item.ExpiresAt)
                {
                    return (T)item.Value;
                }
                else
                {
                    _cache.Remove(key);
                }
            }

            return default;
        }

        public async Task<bool> ExistsAsync(string key)
        {
            if (Status != ServiceStatus.Running)
                return false;

            return _cache.ContainsKey(key) && DateTime.Now < _cache[key].ExpiresAt;
        }

        public async Task RemoveAsync(string key)
        {
            _cache.Remove(key);
            await Logger?.LogAsync(LogLevel.Debug, $"Cache'den çıkarıldı: {key}");
        }
    }

    #endregion

    #region Usage Example

    /// <summary>
    /// Kullanım örneği
    /// </summary>
    public static class ManagerExample
    {
        public static async Task RunExampleAsync()
        {
            // Uygulama yöneticisini oluştur
            var appManager = new ApplicationManager();

            // Logger'ları ekle
            appManager.AddLogger(new ConsoleLogger());
            appManager.AddLogger(new FileLogger());

            // Servisleri kaydet
            appManager.RegisterService(new DatabaseService());
            appManager.RegisterService(new CacheService());

            try
            {
                // Uygulamayı başlat
                await appManager.InitializeAsync();

                // Manager'ları al
                var configManager = appManager.GetManager<ConfigurationManager>();
                var serviceManager = appManager.GetManager<ServiceManager>();

                // Konfigürasyon örneği
                await configManager.SetValueAsync("database.connection_string", "Server=localhost;Database=test");
                var connectionString = await configManager.GetValueAsync<string>("database.connection_string");

                // Servis kontrolü
                var dbService = serviceManager.GetService("DatabaseService");
                var cacheService = serviceManager.GetService("CacheService");

                // Cache kullanımı örneği
                var typedCacheService = (CacheService)cacheService;
                await typedCacheService.SetAsync("test_key", "test_value", 300);
                var cachedValue = await typedCacheService.GetAsync<string>("test_key");

                // Sağlık kontrolü
                await appManager.HealthCheckAsync();

                // Uygulamayı kapat
                await appManager.ShutdownAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Hata: {ex.Message}");
            }
        }
    }

    #endregion
}