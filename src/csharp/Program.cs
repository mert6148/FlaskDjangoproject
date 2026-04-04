using System;
using System.Threading.Tasks;
using manager.src;

namespace ManagerDemo
{
    /// <summary>
    /// Manager sistemi demo uygulaması
    /// </summary>
    class Program
    {
        static async Task Main(string[] args)
        {
            Console.WriteLine("=== C# Uygulama Yönetim Sistemi Demo ===\n");

            try
            {
                // Uygulama yöneticisini oluştur
                var appManager = new ApplicationManager();

                // Logger'ları ekle
                appManager.AddLogger(new ConsoleLogger());
                appManager.AddLogger(new FileLogger());

                // Servisleri kaydet
                appManager.RegisterService(new DatabaseService());
                appManager.RegisterService(new CacheService());

                Console.WriteLine("1. Uygulama başlatılıyor...");
                await appManager.InitializeAsync();

                // Manager'ları al
                var configManager = appManager.GetManager<ConfigurationManager>();
                var serviceManager = appManager.GetManager<ServiceManager>();

                Console.WriteLine("\n2. Konfigürasyon testi...");
                // Konfigürasyon örneği
                await configManager.SetValueAsync("app.title", "Manager Demo App");
                await configManager.SetValueAsync("database.host", "localhost");
                await configManager.SetValueAsync("cache.size", 1024);

                var title = await configManager.GetValueAsync<string>("app.title");
                var host = await configManager.GetValueAsync<string>("database.host");
                var cacheSize = await configManager.GetValueAsync<int>("cache.size");

                Console.WriteLine($"   Başlık: {title}");
                Console.WriteLine($"   DB Host: {host}");
                Console.WriteLine($"   Cache Boyutu: {cacheSize}");

                Console.WriteLine("\n3. Servis testi...");
                // Servis kontrolü
                var dbService = serviceManager.GetService("DatabaseService");
                var cacheService = serviceManager.GetService("CacheService");

                Console.WriteLine($"   DB Servis Durumu: {dbService.Status}");
                Console.WriteLine($"   Cache Servis Durumu: {cacheService.Status}");

                // Cache kullanımı örneği
                Console.WriteLine("\n4. Cache testi...");
                var typedCacheService = (CacheService)cacheService;
                await typedCacheService.SetAsync("demo_key", "Merhaba Dünya!", 60);
                var cachedValue = await typedCacheService.GetAsync<string>("demo_key");
                var exists = await typedCacheService.ExistsAsync("demo_key");

                Console.WriteLine($"   Cache Değeri: {cachedValue}");
                Console.WriteLine($"   Anahtar Var mı: {exists}");

                Console.WriteLine("\n5. Sağlık kontrolü...");
                // Sağlık kontrolü
                var healthResults = await appManager.HealthCheckAsync();
                foreach (var result in healthResults)
                {
                    Console.WriteLine($"   {result.Key}: {(result.Value ? "✓" : "✗")}");
                }

                Console.WriteLine("\n6. Sistem bilgileri...");
                // Sistem durumu
                var systemStatus = appManager.Status;
                Console.WriteLine($"   Uygulama Durumu: {systemStatus}");

                // Tüm servisleri listele
                var allServices = serviceManager.GetAllServices();
                Console.WriteLine($"   Toplam Servis: {allServices.Count()}");

                foreach (var service in allServices)
                {
                    Console.WriteLine($"   - {service.ServiceName}: {service.Status}");
                }

                // Tüm konfigürasyon anahtarlarını listele
                var configKeys = await configManager.GetKeysAsync();
                Console.WriteLine($"   Konfigürasyon Anahtarları: {configKeys.Count()}");

                Console.WriteLine("\n7. Uygulama kapatılıyor...");
                await appManager.ShutdownAsync();

                Console.WriteLine("\n=== Demo Başarıyla Tamamlandı ===");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n❌ Hata: {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
            }

            Console.WriteLine("\nÇıkmak için bir tuşa basın...");
            Console.ReadKey();
        }
    }
}