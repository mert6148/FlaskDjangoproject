# System Protection for javascript

Bu klasör JavaScript kaynaklarını içerir.

## Koruma Önerileri

- JS kodu, özellikle tarayıcıya gönderilen scriptler, hassas bilgiyi içeremez.
- SDK kurulum ve frontend betikleri güvenli kaynaklardan sağlanmalıdır.
- Değişiklikler sürüm kontrolü ve kod incelemesi ile takip edilmelidir.

## Uygulama

- `frontend_demo.js` ve `install_sdk.js` gibi dosyalar sadece genel frontend/SDK işlevi içermelidir.
- Gizli API anahtarları veya kullanıcı verisi bu dosyalarda tutulmamalıdır.
