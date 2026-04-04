# C# Dökümantasyonu

`src/csharp/` klasörü C# projesi ve ilgili API bileşenleri için ayrılmıştır.

## İçerik

- `Controller.cs` - C# web API denetleyicisi
- `Manager.cs` - yönetim ve servis yaşam döngüsü sınıfları
- `Program.cs` - C# uygulama giriş noktası
- `ManagerSystem.csproj` - .NET proje dosyası
- `webapi/` - ASP.NET Core Web API bileşenleri
- `Bank/` - C# banka uygulaması örneği

## Başlatma

```bash
cd src/csharp
dotnet build
dotnet run
```

## Yapılandırma

Proje `ManagerSystem.csproj` içinde .NET 8.0 hedeflenmiştir. `Controller.cs` ve `webapi/` bileşenleri ASP.NET Core uyumluluğu gerektirir.

## Notlar

- `src/csharp/` klasörü `src/src/` altında oluşturulan .NET kaynaklarını temiz ve dil bazlı bir yapıya taşıdı.
- Artık C# kaynakları tek bir klasörde toplanmıştır.
