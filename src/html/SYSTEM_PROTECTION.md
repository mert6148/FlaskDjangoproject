# System Protection for html

Bu klasör statik HTML içeriklerini içerir.

## Koruma Önerileri

- HTML dosyaları kullanıcıya açık içeriği temsil eder; hassas bilgi içermez olmalıdır.
- Sunucu tarafı konfigürasyonlar HTML içinde saklanmamalıdır.
- Statik içerik değişiklikleri kontrol edilmelidir.

## Uygulama

- `index.html` gibi dosyalar yalnızca görsel ve ön yüz içeriği içermelidir.
- Gizli parametreler veya veri anahtarları HTML içine yerleştirilmemelidir.
