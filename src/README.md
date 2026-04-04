# src Klasörü Genel Dökümantasyonu

Bu klasör, `Flask-Django` projesindeki Python, C#, JavaScript, C/C++ ve HTML bileşenlerinin toplandığı ana çalışma alanıdır.
Aşağıdaki yapı, her dilin kendi alt klasöründe düzenlenmesini sağlar.

## Klasör Yapısı

- `python/` - Python uygulama kodları ve araçları
- `csharp/` - C# uygulama ve API bileşenleri
- `java/` - Java örnekleri ve uygulama dosyaları
- `javascript/` - JavaScript ön yüz kodları ve yardımcı scriptler
- `html/` - HTML şablonları ve statik sayfalar
- `cpp/` - C/C++ konfigürasyon rehberi ve örnekler
- `docs/` - Ortam dosyaları ve dil bazlı dokümantasyon
- `config.py`, `settings.py`, `__init__.py` - src kökünde Python yapılandırma paketi
- `CONFIG_README.md` - yapılandırma hakkında özel kılavuz

## Nasıl Kullanılır

1. `src/README.md` klasörün genel yapısını açıklar.
2. `src/docs/` altındaki dosyalar her dil için rehber sağlar.
3. `config.py` ve `settings.py`, Python tabanlı proje yapılandırması için ana dosyalardır.

## Önemli Notlar

- `src/python/` klasörü Python uygulamalarının ana kaynaklarını tutar, ancak `config.py` ve `settings.py` kök seviyede kalmalıdır.
- C# kodları `src/csharp/` altına taşındı; burada .NET projesi ve Web API bileşenleri bulunur.
- Java kodları artık `src/java/` altında yer alır.
- JS ve HTML varlıkları kendi dil klasörlerinde düzenlendi.
- `src/cpp/` klasörü C/C++ için yapılandırma rehberi içerir; gerekli durumlarda kaynak dosyalar eklenebilir.
