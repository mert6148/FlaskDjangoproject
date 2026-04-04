# System Protection for java

Bu klasör Java kaynaklarını içerir.

## Koruma Önerileri

- Java uygulama örnekleri ve derlenen sınıflar için güvenli sürüm kontrolü kullanılmalı.
- Gizli veriler kaynak kod içinde yer almamalıdır.
- Java kodu derlenmeden önce statik analiz ve kod incelemesi yapılmalı.

## Uygulama

- `Application.java` ve `BankApplication.java` gibi dosyalar örnek kod olarak korunmalıdır.
- Gerçek üretim konfigürasyonları bu klasöre eklenmemelidir; ortam değişkenleri kullanılmalıdır.
