# System Protection for templates

Bu klasör HTML ve şablon dosyalarını içerir.

## Koruma Önerileri

- Şablon dosyalarına gizli veri ya da kimlik bilgisi yazılmamalıdır.
- Template değişiklikleri test edilmeden canlıya alınmamalıdır.
- Şablonlar güvenli içerik üretmeye odaklanmalıdır.

## Uygulama

- `templates/` içindeki dosyalar yalnızca sunum katmanını temsil etmelidir.
- Kullanıcı girdilerini direkt olarak şablonlara dahil etmeden önce filtreleme yapılmalıdır.
